"""Post-run receipt (2026-08-29): does B03's nine-arm sequence leak steering between arms?
On 24 held-out artifacts of one fold, the random arm is scored (a) alone after zero and (b)
after the full B03 arm sequence, with the model's live forward-hook count recorded after
every context exit. Writes results/phase_2_4_stage_5/post/B03_LEAK.json.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §4 (hooks removed and replay verified), §3 (a control loud in one
  path and quiet in another is a path difference until shown otherwise).
expectations: under the null (no leak) the random arm's score is the same alone and after
  the sequence and the hook count returns to its baseline after every exit; under the
  alternative (a leak) the hook count stays above baseline after an exit and the random arm
  after the sequence scores like the congruent arm. The direction guarded is a control
  read as loud because an earlier arm's hook stayed attached. Receipt only; no band.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners import s5_lib                                                        # noqa: E402
from runners.s5_run_b import (ANCHOR_MODEL, CYCLE, TENDENCIES, _dose_ladder,      # noqa: E402
                              _fold_directions, _score, _steer_ctx, load_scene_artifacts)
from soundingline.s4 import now_iso, write_json                                    # noqa: E402
from soundingline.stage5 import S5                                                 # noqa: E402


def hook_count(model) -> int:
    n = 0
    for m in model.modules():
        n += len(getattr(m, "_forward_hooks", {})) + len(getattr(m, "_forward_pre_hooks", {}))
    return n


def main() -> int:
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    arts = load_scene_artifacts("scenes")
    tends = sorted(TENDENCIES)
    out = {"written_at": now_iso(), "reader": ANCHOR_MODEL, "per_artifact": [], "hook_counts": []}
    with s5_lib.GpuSession("s5_b03_leak") as gs:
        model, tok, _ = s5_lib.load_model(ANCHOR_MODEL)
        try:
            base_hooks = hook_count(model)
            states = [[h.mean(0) for h in capture_block_states(model, tok, a["body"], device="cuda")] for a in arts]
            n_blocks = len(states[0])
            third = n_blocks // 3
            locus = list(range(third, 2 * third, 2))
            fit_idx = [i for i, a in enumerate(arts) if a["fam"] == "smollm"]
            test_idx = [i for i, a in enumerate(arts) if a["fam"] == "qwen"][:24]
            cents, dirs = _fold_directions(states, arts, fit_idx, locus, tends)
            mean_norm = float(torch.stack([states[i][locus[0]] for i in fit_idx]).norm(dim=1).mean())
            ladder, alpha, frac = _dose_ladder(model, tok, locus, dirs, tends, mean_norm)
            out["after_ladder_hooks"] = hook_count(model) - base_hooks
            shifted = [min(n_blocks - 1, b + 3) for b in locus]
            rnd_blocks = random.Random(55100 + 11).sample([b for b in range(2, n_blocks - 1) if b not in locus], len(locus))
            for i in test_idx:
                a = arts[i]
                body = (f"Someone wrote this short passage about a situation they were in:\n\"{a['body']}\"\n\n"
                        f"Which impulse was driving the writer?")
                g = torch.Generator().manual_seed(55100 + 7100 + i)
                rd = {}
                for b in locus:
                    d = dirs[b][a["tend"]]
                    r = torch.randn(d.shape[0], generator=g)
                    r = r - (r @ d) * d
                    rd[b] = r / r.norm()
                cong = {b: dirs[b][a["tend"]] for b in locus}
                seq = [("zero", None, 0.0, locus), ("congruent", cong, alpha, locus),
                       ("incongruent", {b: dirs[b][CYCLE[a["tend"]]] for b in locus}, alpha, locus),
                       ("random", rd, alpha, locus),
                       ("shifted", {sb: dirs[b][a["tend"]] for sb, b in zip(shifted, locus)}, alpha, shifted),
                       ("random_blocks", {rb: dirs[b][a["tend"]] for rb, b in zip(rnd_blocks, locus)}, alpha, rnd_blocks),
                       ("half", cong, alpha / 2, locus), ("double", cong, alpha * 2, locus),
                       ("reversed", cong, -alpha, locus), ("random_after", rd, alpha, locus), ("zero_after", None, 0.0, locus)]
                rec = {"i": i, "truth": a["tend"], "scores": {}, "hooks_after": {}}
                # (a) the random arm alone, right after zero, a fresh rng
                with _steer_ctx(model, locus, None, 0.0):
                    r0 = _score(model, tok, body, tends, random.Random(1))
                with _steer_ctx(model, locus, rd, alpha):
                    r1 = _score(model, tok, body, tends, random.Random(2))
                rec["scores"]["zero_alone"] = s5_lib.log_score(r0["probs"], a["tend"]) if r0["valid"] else None
                rec["scores"]["random_alone"] = s5_lib.log_score(r1["probs"], a["tend"]) if r1["valid"] else None
                rec["hooks_after"]["random_alone"] = hook_count(model) - base_hooks
                # (b) the B03 sequence with one shared rng, as run_bridge does
                rng = random.Random(55100 + 7000 + i)
                for name, dmap, al, blocks in seq:
                    with _steer_ctx(model, blocks, dmap, al):
                        r = _score(model, tok, body, tends, rng)
                    rec["scores"][name] = s5_lib.log_score(r["probs"], a["tend"]) if r["valid"] else None
                    rec["hooks_after"][name] = hook_count(model) - base_hooks
                out["per_artifact"].append(rec)
        finally:
            s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s
    # summaries
    def mean(key, ref):
        v = [r["scores"][key] - r["scores"][ref] for r in out["per_artifact"] if r["scores"].get(key) is not None and r["scores"].get(ref) is not None]
        return (sum(v) / len(v)) if v else None
    out["summary"] = {"random_alone_minus_zero_alone": mean("random_alone", "zero_alone"),
                      "random_in_sequence_minus_zero": mean("random", "zero"),
                      "random_after_sequence_minus_zero": mean("random_after", "zero"),
                      "zero_after_sequence_minus_zero": mean("zero_after", "zero"),
                      "congruent_minus_zero": mean("congruent", "zero"),
                      "shifted_minus_zero": mean("shifted", "zero"), "permuted_absent": True,
                      "max_hooks_after_any_exit": max(h for r in out["per_artifact"] for h in r["hooks_after"].values()),
                      "after_ladder_hooks": out["after_ladder_hooks"], "n": len(out["per_artifact"])}
    (S5 / "post").mkdir(parents=True, exist_ok=True)
    write_json(S5 / "post" / "B03_LEAK.json", out)
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out["summary"].items()})
    print("wrote", S5 / "post" / "B03_LEAK.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
