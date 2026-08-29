"""Stage 3 Trunk A runners: A01 action-tendency corpus with source twins, A02 the
steering known-positive anchor. Cards E24-S3-A01, E24-S3-A02. A02 MUST land before any
A-trunk causal arm runs (brief section on trunk A: an INSTRUMENT_FAILED here blocks
A03/A05/A07 causal claims, which then close as instrument-limited, not as nulls).

DESIGN CHECK (2026-08-24). Lessons applied: known-positive before signal (L139) — A02
reproduces plain valence activation-steering with a sign pair, zero, random-direction,
and shuffled-label controls, plus a capability tolerance, before any tendency geometry is
trusted; consensus loci are cross-seed with blocks 0-2 excluded (L170 edge lesson); doses
are ladder-selected under capability tolerance, largest passing dose reported (L164);
accept-time realization for A01 via unique tendency anchor phrases in a required final
line, mirroring the environment's exactly-one-anchor machinery (L156, L169 uniqueness);
the steering hook carries the `_p24_intervention` tag so cleanup audits count it
(transformers-5 persistent recorder hooks); amplify-mode projection is sign-invariant,
so steering is ADDITIVE (h +/- alpha*d) by construction, implemented here.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import hash_stable, perm_p                                    # noqa: E402
from soundingline.s3 import S3, set_status                                        # noqa: E402

SEED0 = 40000
ANCHOR_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
MAKERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
OUT_A = S3 / "A"

# ── A01: tendencies, anchors, scenes ─────────────────────────────────────────────────

TENDENCIES = {
    "fear": "put real distance between myself and it",
    "anger": "confront the person responsible directly",
    "curiosity": "move closer and examine it carefully",
    "care": "stay beside them and keep them steady",
}
TENDENCY_LINES = {
    "fear": "You feel a rising dread; your impulse is to get away and stay safe.",
    "anger": "You feel a hot indignation; your impulse is to confront and demand.",
    "curiosity": "You feel a pull of fascination; your impulse is to approach and probe.",
    "care": "You feel a protective warmth; your impulse is to shelter and support.",
}
SCENES = [
    "A low humming starts under the floorboards of the cabin.",
    "A stranger has been photographing your street for an hour.",
    "The package on the porch has no label and a faint ticking.",
    "Your neighbor's dog has cornered something behind the shed.",
    "The lab door you locked last night stands open.",
    "A colleague left a note that only says 'we need to talk'.",
    "The old well in the field has begun to echo at dusk.",
    "Someone rearranged the books on your shelf while you were out.",
    "A child at the bus stop is crying and will not say why.",
    "The lights in the opposite house blink in a steady pattern.",
    "Your name is called from the tree line, twice, then silence.",
    "The cellar smells of ozone after the storm.",
    "A drone has hovered outside the office window all morning.",
    "The bridge planks are wet though it has not rained.",
    "An unfamiliar car idles at the end of the driveway again.",
    "The museum case is empty and the alarm never sounded.",
    "Your co-op partner missed the third meeting in a row.",
    "The radio picks up a voice on a band that should be dead.",
    "There are fresh footprints ending at the middle of the lawn.",
    "The bakery's night shift left every oven door open.",
    "A letter arrives addressed in your own handwriting.",
    "The ferry horn sounds three times, which means nothing scheduled.",
    "Your reflection in the shop window lags by half a step.",
    "The community garden gate lock has been cut cleanly.",
]


def a01_prompt(scene: str, tendency: str) -> str:
    return (f"Situation: {scene}\n{TENDENCY_LINES[tendency]}\n"
            f"Write a short first-person continuation (50 to 100 words) describing what "
            f"you notice, think, and do next, consistent with that impulse. End with a "
            f"single line of the form:\nNext: {TENDENCIES[tendency]}\n"
            f"Use exactly that closing phrase and no other tendency's phrase.\n\n"
            f"Continuation:")


def a01_realized(text: str) -> str | None:
    low = text.lower()
    hits = [t for t, phrase in TENDENCIES.items() if phrase.lower()[:24] in low]
    return hits[0] if len(hits) == 1 else None


def arm_a01() -> int:
    """The action-tendency corpus: 24 scenes x 4 tendencies x 2 makers, twins by scene.
    Accept-time realization; a scene lands only if all four twins realize (complete
    quads only, so downstream contrasts never mix partial cells)."""
    cell = "E24-S3-A01"
    t0 = time.time()
    out = OUT_A / "A01"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from runners.s3_lib import chat_gen                                           # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    n_ok = n_try = 0
    acquire_gpu_lock("s3_a01")
    try:
        for mk in MAKERS:
            short = mk.split("/")[-1][:8]
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            for si, scene in enumerate(SCENES):
                for tend in TENDENCIES:
                    dest = out / f"art_{short}_{si}_{tend}.json"
                    n_try += 1
                    if dest.exists():
                        n_ok += 1
                        continue
                    for att in range(5):
                        txt = chat_gen(model, tok, a01_prompt(scene, tend),
                                       SEED0 + si * 64 + att, max_new=200)
                        if a01_realized(txt) == tend:
                            body = txt[:txt.lower().find("next:")].strip() \
                                if "next:" in txt.lower() else txt
                            dest.write_text(json.dumps(
                                {"maker": mk, "scene_i": si, "tendency": tend,
                                 "body": body, "full": txt}, ensure_ascii=False),
                                encoding="utf-8", newline="\n")
                            n_ok += 1
                            break
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    # complete quads per maker/scene
    quads = 0
    for mk in MAKERS:
        short = mk.split("/")[-1][:8]
        for si in range(len(SCENES)):
            if all((out / f"art_{short}_{si}_{t}.json").exists()
                   for t in TENDENCIES):
                quads += 1
    yield_frac = n_ok / n_try
    (out / "corpus.json").write_text(json.dumps(
        {"cell": cell, "attempted": n_try, "realized": n_ok, "yield": yield_frac,
         "complete_quads": quads, "of_quads": len(MAKERS) * len(SCENES)},
        indent=1), encoding="utf-8", newline="\n")
    status = "LANDED" if yield_frac >= 0.9 else "INSTRUMENT_FAILED"
    set_status(cell, status,
               closure_reason=None if status == "LANDED" else
               f"corpus yield {yield_frac:.2f} under the 0.9 floor",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A01 {status}: yield {yield_frac:.3f}, quads {quads}/{len(MAKERS) * len(SCENES)}")
    return 0


# ── A02: additive valence steering anchor ────────────────────────────────────────────

POS_SENTS = [
    "I am delighted with how this turned out.", "This is wonderful news for all of us.",
    "I feel genuinely happy about the result.", "What a joy it is to see this succeed.",
    "I am thrilled by the progress we made.", "This outcome fills me with satisfaction.",
    "I love how smoothly everything went.", "The celebration left everyone glowing.",
    "I am grateful and encouraged by this.", "Her kindness made the whole day brighter.",
    "The garden is thriving and it cheers me.", "We laughed together all evening.",
    "The award was a delightful surprise.", "I feel hopeful about what comes next.",
    "The reunion was warm and full of laughter.", "I am proud of what the team built.",
    "The music lifted everyone's spirits.", "A perfect morning left me smiling.",
    "The good news spread and morale soared.", "I cherish how supportive they were.",
    "Success this sweet is worth savoring.", "The victory brought tears of joy.",
    "Everything about the trip was lovely.", "I am overjoyed at the recovery.",
]
NEG_SENTS = [
    "I am devastated by how this turned out.", "This is terrible news for all of us.",
    "I feel genuinely miserable about the result.", "What a sorrow it is to see this fail.",
    "I am crushed by the setbacks we hit.", "This outcome fills me with regret.",
    "I hate how badly everything went.", "The argument left everyone bitter.",
    "I am resentful and discouraged by this.", "His cruelty made the whole day darker.",
    "The garden is dying and it saddens me.", "We argued miserably all evening.",
    "The rejection was a painful blow.", "I feel hopeless about what comes next.",
    "The funeral was cold and full of grief.", "I am ashamed of what the team broke.",
    "The noise ground everyone's nerves down.", "A dreadful morning left me weeping.",
    "The bad news spread and morale collapsed.", "I dread how hostile they were.",
    "Failure this bitter is hard to swallow.", "The defeat brought tears of despair.",
    "Everything about the trip was awful.", "I am heartbroken at the relapse.",
]
NEUTRAL_CTX = [
    "The committee reviewed the quarterly report and",
    "She opened the letter from the county office and",
    "The forecast for the harvest season suggests that",
    "After the meeting, the team decided that",
    "The results of the inspection indicate that",
    "When the shipment arrived on Tuesday, the manager",
    "The new schedule for the branch means that",
    "Looking over the survey responses, the analyst",
    "The renovation of the east wing will",
    "As the season changed, the volunteers",
    "The updated guidelines state that the office",
    "Following the audit, the department",
]
POS_CONT = " the outcome was a genuine delight and everyone felt encouraged."
NEG_CONT = " the outcome was a genuine disaster and everyone felt discouraged."
FACT_CONT = [
    "The capital of France is Paris.",
    "Water freezes at zero degrees Celsius.",
    "A triangle has three sides.",
    "The sun rises in the east.",
    "Seven times eight is fifty-six.",
    "Oxygen is required for combustion.",
    "The alphabet has twenty-six letters.",
    "A year has twelve months.",
]


@contextmanager
def additive_steer(model, block_ids, direction, alpha: float):
    """h' = h + alpha * d on ALL positions at the chosen blocks. Sign lives in alpha.
    Same conventions as SubspaceIntervention: tagged hook, guaranteed removal."""
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import get_blocks                       # noqa: PLC0415
    blocks = get_blocks(model)
    handles = []

    def make_hook():
        def hook(_m, _i, output):
            hs = output[0] if isinstance(output, tuple) else output
            d = direction.to(device=hs.device, dtype=torch.float32)
            out = (hs.to(torch.float32) + alpha * d).to(hs.dtype)
            if isinstance(output, tuple):
                return (out,) + tuple(output[1:])
            return out
        hook._p24_intervention = True
        return hook

    try:
        for i in block_ids:
            handles.append(blocks[i].register_forward_hook(make_hook()))
        yield
    finally:
        for h in handles:
            h.remove()


def _mean_logp(model, tok, ctx: str, cont: str) -> float:
    """Mean per-token logprob of cont given ctx."""
    import torch                                                                  # noqa: PLC0415
    ids_c = tok(ctx, return_tensors="pt", add_special_tokens=False).input_ids
    ids_f = tok(ctx + cont, return_tensors="pt",
                add_special_tokens=False).input_ids.to("cuda")
    n_ctx = ids_c.shape[1]
    with torch.no_grad():
        logits = model(ids_f).logits.float()
    lp = torch.log_softmax(logits[0, :-1], dim=-1)
    tgt = ids_f[0, 1:]
    span = range(n_ctx - 1, ids_f.shape[1] - 1)
    vals = [lp[i, tgt[i]].item() for i in span]
    return sum(vals) / len(vals)


def arm_a02() -> int:
    """Valence activation-steering known-positive on Qwen2.5-1.5B-Instruct."""
    cell = "E24-S3-A02"
    t0 = time.time()
    out = OUT_A / "A02"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    acquire_gpu_lock("s3_a02")
    try:
        tok = AutoTokenizer.from_pretrained(ANCHOR_MODEL)
        model = AutoModelForCausalLM.from_pretrained(
            ANCHOR_MODEL, dtype=torch.float16).to("cuda").eval()

        # last-token states per block for every sentence
        states = {}      # (label, idx) -> list over blocks of (d,) tensors
        for label, bank in (("pos", POS_SENTS), ("neg", NEG_SENTS)):
            for i, s in enumerate(bank):
                hs = capture_block_states(model, tok, s, device="cuda")
                states[(label, i)] = [h[-1] for h in hs]
        n_blocks = len(states[("pos", 0)])

        # cross-seed locus: two fit splits + one untouched validation split
        def fit_and_decode(seed: int):
            rng = random.Random(SEED0 + seed)
            idx = list(range(24))
            rng.shuffle(idx)
            fit, held = idx[:16], idx[16:]
            per_block = []
            for b in range(n_blocks):
                mp = torch.stack([states[("pos", i)][b] for i in fit]).mean(0)
                mn = torch.stack([states[("neg", i)][b] for i in fit]).mean(0)
                d = mp - mn
                d = d / d.norm()
                thr = ((mp + mn) / 2) @ d
                hits = 0
                for i in held:
                    hits += (states[("pos", i)][b] @ d > thr).item()
                    hits += (states[("neg", i)][b] @ d <= thr).item()
                per_block.append({"acc": hits / (2 * len(held)), "dir": d,
                                  "mid": (mp + mn) / 2})
            return per_block

        fits = [fit_and_decode(s) for s in (1, 2)]
        consensus = [b for b in range(3, n_blocks)
                     if all(f[b]["acc"] >= 0.9 for f in fits)]
        val = fit_and_decode(3)
        consensus = [b for b in consensus if val[b]["acc"] >= 0.9]
        if not consensus:
            (out / "anchor.json").write_text(json.dumps(
                {"cell": cell, "verdict": "INSTRUMENT-FAILED",
                 "reason": "no cross-seed consensus locus decodes valence at 0.9"},
                indent=1), encoding="utf-8", newline="\n")
            set_status(cell, "INSTRUMENT_FAILED",
                       closure_reason="no consensus valence locus",
                       actual_gpu_minutes=(time.time() - t0) / 60)
            print("A02 INSTRUMENT-FAILED: no consensus locus")
            return 0
        # steer at the middle third of consensus blocks (mid-depth, per S8 practice)
        consensus.sort()
        locus = consensus[len(consensus) // 3: len(consensus) // 3
                          + max(1, len(consensus) // 3)]
        dirs = {b: fits[0][b]["dir"] for b in locus}
        # controls: random direction (matched, orthogonalized against d), shuffled labels
        g = torch.Generator().manual_seed(SEED0)
        rand_dirs, shuf_dirs = {}, {}
        rng = random.Random(SEED0 + 9)
        lab = ["pos"] * 24 + ["neg"] * 24
        rng.shuffle(lab)
        for b in locus:
            r = torch.randn(dirs[b].shape[0], generator=g)
            r = r - (r @ dirs[b]) * dirs[b]
            rand_dirs[b] = r / r.norm()
            mp = torch.stack([states[(l0, i % 24)][b]
                              for i, l0 in enumerate(lab[:24])]).mean(0)
            mn = torch.stack([states[(l0, i % 24)][b]
                              for i, l0 in enumerate(lab[24:], start=24)]).mean(0)
            d2 = mp - mn
            shuf_dirs[b] = d2 / d2.norm()

        def delta_battery(cond_dirs, alpha):
            """Per-context logp(pos cont) - logp(neg cont) under a steer config.
            cond_dirs None = zero condition. Single-block-dict steering applied to
            every locus block with its own direction."""
            deltas, fact = [], []
            def run():
                for ctx in NEUTRAL_CTX:
                    deltas.append(_mean_logp(model, tok, ctx, POS_CONT)
                                  - _mean_logp(model, tok, ctx, NEG_CONT))
                for f in FACT_CONT:
                    fact.append(_mean_logp(model, tok, "A plain fact: ", f))
            if cond_dirs is None or alpha == 0.0:
                run()
            else:
                # nested contexts: one hook per block via chained managers
                from contextlib import ExitStack                                  # noqa: PLC0415
                with ExitStack() as stack:
                    for b, d in cond_dirs.items():
                        stack.enter_context(additive_steer(model, [b], d, alpha))
                    run()
            return deltas, sum(fact) / len(fact)

        base_deltas, base_fact = delta_battery(None, 0.0)
        # dose ladder under capability tolerance (largest passing dose reported)
        mean_norm = float(torch.stack(
            [states[("pos", i)][locus[0]] for i in range(24)]).norm(dim=1).mean())
        chosen = None
        ladder = {}
        for frac in (0.20, 0.10, 0.05):
            alpha = frac * mean_norm
            pd, pf = delta_battery(dirs, alpha)
            capability_ok = pf >= base_fact - 0.15 * abs(base_fact)
            ladder[str(frac)] = {"alpha": alpha, "fact_logp": pf,
                                 "capability_ok": capability_ok}
            if capability_ok and chosen is None:
                chosen = (frac, alpha, pd)
        if chosen is None:
            (out / "anchor.json").write_text(json.dumps(
                {"cell": cell, "verdict": "INSTRUMENT-FAILED",
                 "reason": "no dose passes the capability tolerance",
                 "consensus_blocks": consensus, "steer_locus": locus,
                 "dose_ladder": ladder}, indent=1), encoding="utf-8", newline="\n")
            set_status(cell, "INSTRUMENT_FAILED",
                       closure_reason="no dose passes capability tolerance",
                       actual_gpu_minutes=(time.time() - t0) / 60)
            print("A02 INSTRUMENT-FAILED: capability floor at all doses")
            return 0
        frac, alpha, pos_deltas = chosen
        neg_deltas, _ = delta_battery(dirs, -alpha)
        rand_deltas, _ = delta_battery(rand_dirs, alpha)
        shuf_deltas, _ = delta_battery(shuf_dirs, alpha)

        pos_shift = [p - b for p, b in zip(pos_deltas, base_deltas)]
        neg_shift = [n - b for n, b in zip(neg_deltas, base_deltas)]
        rand_shift = [r - b for r, b in zip(rand_deltas, base_deltas)]
        shuf_shift = [s0 - b for s0, b in zip(shuf_deltas, base_deltas)]
        obs_p, p_pos = perm_p(pos_shift, SEED0 + 11)
        obs_n, p_neg = perm_p(neg_shift, SEED0 + 12)
        sign_pair = obs_p > 0 and obs_n < 0 and p_pos < 0.05 and p_neg < 0.05
        rand_quiet = abs(sum(rand_shift) / len(rand_shift)) < abs(obs_p) / 2
        shuf_quiet = abs(sum(shuf_shift) / len(shuf_shift)) < abs(obs_p) / 2
        verdict = "ANCHOR-STANDS" if (sign_pair and rand_quiet and shuf_quiet) \
            else "INSTRUMENT-FAILED"
        (out / "anchor.json").write_text(json.dumps(
            {"cell": cell, "verdict": verdict, "consensus_blocks": consensus,
             "steer_locus": locus, "dose_frac": frac, "alpha": alpha,
             "dose_ladder": ladder,
             "pos_shift_mean": obs_p, "p_pos": p_pos,
             "neg_shift_mean": obs_n, "p_neg": p_neg,
             "rand_shift_mean": sum(rand_shift) / len(rand_shift),
             "shuf_shift_mean": sum(shuf_shift) / len(shuf_shift),
             "held_out_decode_seed1": fits[0][locus[0]]["acc"],
             "validation_decode": val[locus[0]]["acc"],
             "n_contexts": len(NEUTRAL_CTX), "perm_seeds": [SEED0 + 11, SEED0 + 12]},
            indent=1), encoding="utf-8", newline="\n")
        set_status(cell, "LANDED" if verdict == "ANCHOR-STANDS" else "INSTRUMENT_FAILED",
                   closure_reason=None if verdict == "ANCHOR-STANDS" else
                   "steering anchor failed its sign pair or controls",
                   actual_gpu_minutes=(time.time() - t0) / 60)
        print(f"A02 {verdict}: locus {locus}, dose {frac}, +shift {obs_p:.4f} "
              f"(p={p_pos:.4g}), -shift {obs_n:.4f} (p={p_neg:.4g})")
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    return 0


# ── A03: basis/locus tournament (card E24-S3-A03) ───────────────────────────────────
# The question in plain language: where in the model, and in what geometric form, do
# the four action tendencies live while the model reads tendency-laden text? Bases
# (mean-difference one-vs-rest vs nearest-class-centroid) x loci (early / middle / late
# thirds, plus the A02 valence consensus blocks) tournament, scored by held-out
# scene-fold decode of the tendency from the artifact BODY (anchor line stripped).
# DESIGN CHECK: runs behind A01 (corpus) and A02 (anchor) in the queue (L139); folds are
# BY SCENE so no scene's twins straddle train/test (leakage guard); the anchor line and
# any literal tendency-phrase echo are stripped from the body before capture (the
# tendency must be read from the writing, not from the label); shuffled-label null with
# matched folds run beside every cell; per-cell accuracy beside the winner (L168).

OUT_A03 = OUT_A / "A03"


def _a03_strip(body: str) -> str:
    low = body.lower()
    for phrase in TENDENCIES.values():
        p0 = low.find(phrase.lower()[:24])
        if p0 >= 0:
            body = body[:p0] + body[p0 + len(phrase):]
            low = body.lower()
    return body.strip()


def arm_a03() -> int:
    cell = "E24-S3-A03"
    t0 = time.time()
    OUT_A03.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    arts = []
    for p2 in sorted((OUT_A / "A01").glob("art_*.json")):
        d = json.loads(p2.read_text(encoding="utf-8"))
        body = _a03_strip(d["body"])
        if len(body) > 80:
            arts.append({"scene": d["scene_i"], "tend": d["tendency"],
                         "body": body})
    tends = sorted(TENDENCIES)
    acquire_gpu_lock("s3_a03")
    try:
        tok = AutoTokenizer.from_pretrained(ANCHOR_MODEL)
        model = AutoModelForCausalLM.from_pretrained(
            ANCHOR_MODEL, dtype=torch.float16).to("cuda").eval()
        states = []      # mean-pooled body states per block, per artifact
        for a in arts:
            hs = capture_block_states(model, tok, a["body"], device="cuda")
            states.append([h.mean(0) for h in hs])
        n_blocks = len(states[0])
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    third = n_blocks // 3
    loci = {"early": list(range(1, third)),
            "middle": list(range(third, 2 * third)),
            "late": list(range(2 * third, n_blocks - 1))}
    anchor_path = OUT_A / "A02" / "anchor.json"
    if anchor_path.exists():
        cons = json.loads(anchor_path.read_text(encoding="utf-8")
                          ).get("consensus_blocks")
        if cons:
            loci["a02_consensus"] = cons

    import random as _r                                                           # noqa: PLC0415
    scenes = sorted({a["scene"] for a in arts})
    rng = _r.Random(SEED0 + 77)
    rng.shuffle(scenes)
    folds = [set(scenes[i::5]) for i in range(5)]

    def pooled(a_states, blocks):
        v = a_states[blocks[0]].clone()
        for b in blocks[1:]:
            v = v + a_states[b]
        return v / len(blocks)

    def run_cell(basis: str, blocks, labels):
        hits = tot = 0
        for fold in folds:
            tr = [i for i, a in enumerate(arts) if a["scene"] not in fold]
            te = [i for i, a in enumerate(arts) if a["scene"] in fold]
            if not tr or not te:
                continue
            cents = {}
            for t in tends:
                idx = [i for i in tr if labels[i] == t]
                if not idx:
                    return None
                cents[t] = sum((pooled(states[i], blocks) for i in idx),
                               start=pooled(states[idx[0]], blocks) * 0) / len(idx)
            if basis == "meandiff":
                # one-vs-rest directions; classify by max projection
                dirs = {}
                for t in tends:
                    rest = sum((cents[u] for u in tends if u != t),
                               start=cents[t] * 0) / (len(tends) - 1)
                    d = cents[t] - rest
                    dirs[t] = d / d.norm()
                for i in te:
                    v = pooled(states[i], blocks)
                    pred = max(tends, key=lambda t: float(v @ dirs[t]))
                    hits += pred == labels[i]
                    tot += 1
            else:
                for i in te:
                    v = pooled(states[i], blocks)
                    pred = min(tends,
                               key=lambda t: float((v - cents[t]).norm()))
                    hits += pred == labels[i]
                    tot += 1
        return hits / tot if tot else None

    true_labels = [a["tend"] for a in arts]
    shuffles = []
    for _k in range(5):
        lab = list(true_labels)
        rng.shuffle(lab)
        shuffles.append(lab)
    table = {}
    for basis in ("meandiff", "centroid"):
        for lname, blocks in loci.items():
            acc = run_cell(basis, blocks, true_labels)
            nulls = [run_cell(basis, blocks, lab) for lab in shuffles]
            nulls = [x for x in nulls if x is not None]
            table[f"{basis}|{lname}"] = {
                "acc": acc,
                "shuffled_null": sum(nulls) / len(nulls) if nulls else None,
                "shuffled_null_max": max(nulls) if nulls else None,
                "n_blocks": len(blocks)}
    valid = {k: v for k, v in table.items() if v["acc"] is not None}
    winner = max(valid, key=lambda k: valid[k]["acc"]) if valid else None
    (OUT_A03 / "tournament.json").write_text(json.dumps(
        {"cell": cell, "n_artifacts": len(arts), "table": table,
         "winner": winner, "floor": 0.25,
         "winner_acc": valid[winner]["acc"] if winner else None},
        indent=1), encoding="utf-8", newline="\n")
    ok = winner is not None and valid[winner]["acc"] >= 0.4 and \
        valid[winner]["acc"] > (valid[winner]["shuffled_null"] or 0) + 0.1
    set_status(cell, "LANDED" if ok else "SCIENTIFIC_CLOSED",
               closure_reason=None if ok else
               "no basis/locus decodes tendencies clear of the shuffled null",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A03 {'landed' if ok else 'closed'}: winner {winner} "
          f"({valid[winner]['acc'] if winner else None}); "
          f"{json.dumps({k: v['acc'] for k, v in table.items()})}")
    return 0


# ── A04: the fear-anger dissociation (card E24-S3-A04) ──────────────────────────────
# The question in plain language: fear and anger share negative valence but pull in
# opposite action directions (away vs toward). If the A03 tendency read is really
# reading TENDENCY, it must separate fear from anger bodies; and the A02 VALENCE
# direction must NOT separate them (both negative). Both halves are required — a
# tendency reader that is secretly a valence reader passes one and fails the other.
# DESIGN CHECK: same scene-fold discipline and anchor stripping as A03; the valence
# direction is imported frozen from A02's fit, never refitted on this corpus; cells
# for both halves beside the verdict (L168).

def arm_a04() -> int:
    cell = "E24-S3-A04"
    t0 = time.time()
    out = OUT_A / "A04"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    arts = []
    for p2 in sorted((OUT_A / "A01").glob("art_*.json")):
        d = json.loads(p2.read_text(encoding="utf-8"))
        if d["tendency"] not in ("fear", "anger"):
            continue
        body = _a03_strip(d["body"])
        if len(body) > 80:
            arts.append({"scene": d["scene_i"], "tend": d["tendency"],
                         "body": body})
    a02 = json.loads((OUT_A / "A02" / "anchor.json").read_text(encoding="utf-8"))
    locus = a02.get("steer_locus") or a02.get("consensus_blocks") or []
    acquire_gpu_lock("s3_a04")
    try:
        tok = AutoTokenizer.from_pretrained(ANCHOR_MODEL)
        model = AutoModelForCausalLM.from_pretrained(
            ANCHOR_MODEL, dtype=torch.float16).to("cuda").eval()
        states = []
        for a in arts:
            hs = capture_block_states(model, tok, a["body"], device="cuda")
            states.append([h.mean(0) for h in hs])
        n_blocks = len(states[0])
        # refit the A02 valence direction from its own sentence bank (frozen recipe,
        # seed 1 split) at the locus blocks — the direction, not the labels
        val_states = {}
        for label, bank in (("pos", POS_SENTS), ("neg", NEG_SENTS)):
            for i, s2 in enumerate(bank):
                hs = capture_block_states(model, tok, s2, device="cuda")
                val_states[(label, i)] = [hs[b][-1] for b in range(n_blocks)]
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    import random as _r                                                           # noqa: PLC0415
    rng = _r.Random(SEED0 + 41)
    scenes = sorted({a["scene"] for a in arts})
    rng.shuffle(scenes)
    folds = [set(scenes[i::5]) for i in range(5)]
    use_blocks = [b for b in (locus if locus else range(3, n_blocks))
                  if b < n_blocks]

    def pooled(a_states):
        v = a_states[use_blocks[0]].clone()
        for b in use_blocks[1:]:
            v = v + a_states[b]
        return v / len(use_blocks)

    # half 1: tendency centroid decode fear vs anger, scene folds
    hits = tot = 0
    for fold in folds:
        tr = [i for i, a in enumerate(arts) if a["scene"] not in fold]
        te = [i for i, a in enumerate(arts) if a["scene"] in fold]
        if not tr or not te:
            continue
        cents = {}
        for t in ("fear", "anger"):
            idx = [i for i in tr if arts[i]["tend"] == t]
            if not idx:
                continue
            cents[t] = sum((pooled(states[i]) for i in idx),
                           start=pooled(states[idx[0]]) * 0) / len(idx)
        if len(cents) < 2:
            continue
        for i in te:
            pred = min(cents, key=lambda t: float(
                (pooled(states[i]) - cents[t]).norm()))
            hits += pred == arts[i]["tend"]
            tot += 1
    tend_acc = hits / tot if tot else None

    # half 2: the valence direction must NOT separate fear from anger
    import torch as _t                                                            # noqa: PLC0415
    fit_rng = _r.Random(SEED0 + 1)          # A02's seed-1 split, same recipe
    fit_idx = list(range(24))
    fit_rng.shuffle(fit_idx)
    fit_idx = fit_idx[:16]
    dirs = {}
    for b in use_blocks:
        mp = _t.stack([val_states[("pos", i)][b] for i in fit_idx]).mean(0)
        mn = _t.stack([val_states[("neg", i)][b] for i in fit_idx]).mean(0)
        d = mp - mn
        dirs[b] = d / d.norm()
    fear_proj = [sum(float(states[i][b] @ dirs[b]) for b in use_blocks)
                 / len(use_blocks) for i, a in enumerate(arts)
                 if a["tend"] == "fear"]
    anger_proj = [sum(float(states[i][b] @ dirs[b]) for b in use_blocks)
                  / len(use_blocks) for i, a in enumerate(arts)
                  if a["tend"] == "anger"]
    # valence-axis separation as AUC
    import bisect                                                                 # noqa: PLC0415
    srt = sorted(anger_proj)
    val_auc = (sum(bisect.bisect_left(srt, x) + 0.5 * (
        bisect.bisect_right(srt, x) - bisect.bisect_left(srt, x))
        for x in fear_proj) / (len(fear_proj) * len(srt))
        if fear_proj and srt else None)
    dissociated = (tend_acc or 0) >= 0.65 and val_auc is not None and \
        abs(val_auc - 0.5) < 0.15
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "tendency_decode_acc": tend_acc, "n_folds_items": tot,
         "valence_axis_auc_fear_vs_anger": val_auc,
         "dissociated": dissociated, "locus_blocks": use_blocks,
         "reading": "dissociated = tendency separates (>=0.65) while the valence "
                    "axis does not (AUC within 0.15 of chance)"}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A04 landed: tendency {tend_acc}, valence-axis AUC {val_auc}, "
          f"dissociated={dissociated}")
    return 0


# ── A06: expressivity suppression (card E24-S3-A06) ─────────────────────────────────
# The question in plain language: when a maker is told to keep all feeling OUT of the
# writing while still acting on the tendency, does the tendency remain decodable from
# the flat text — leakage through suppression? Suppressed twins of the A01 corpus from
# one maker; decode with the A03 winner recipe fit on EXPRESSIVE bodies, applied to
# suppressed ones (train-on-expressive, test-on-suppressed: the transfer direction that
# matters), beside within-suppressed folds.
# DESIGN CHECK: same anchors, same accept rule, same stripping (L156); the surface
# check (mean emotion-word count expressive vs suppressed) verifies suppression actually
# happened before leakage is claimed (the null that can fail it, written first);
# scene-fold discipline; cells beside contrasts (L168).

SUPPRESS_LINE = ("Important: write in a flat, matter-of-fact register. Do not name or "
                 "display any emotion; no exclamations, no emotive adjectives. Simply "
                 "report what you notice, think, and do.")
EMOTION_WORDS = {"afraid", "fear", "terrified", "dread", "scared", "angry", "anger",
                 "furious", "rage", "indignant", "curious", "fascinated", "wonder",
                 "intrigued", "care", "tender", "protective", "warmth", "worried",
                 "anxious", "love", "hate"}


def arm_a06() -> int:
    cell = "E24-S3-A06"
    t0 = time.time()
    out = OUT_A / "A06"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from runners.s3_lib import chat_gen                                           # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    mk = ANCHOR_MODEL
    acquire_gpu_lock("s3_a06")
    try:
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        # 1) suppressed twins
        for si, scene in enumerate(SCENES):
            for tend in TENDENCIES:
                dest = out / f"sup_{si}_{tend}.json"
                if dest.exists():
                    continue
                prompt = a01_prompt(scene, tend).replace(
                    "Write a short first-person continuation",
                    SUPPRESS_LINE + "\nWrite a short first-person continuation")
                for att in range(5):
                    txt = chat_gen(model, tok, prompt,
                                   SEED0 + 3000 + si * 64 + att, max_new=200)
                    if a01_realized(txt) == tend:
                        body = txt[:txt.lower().find("next:")].strip() \
                            if "next:" in txt.lower() else txt
                        dest.write_text(json.dumps(
                            {"scene_i": si, "tendency": tend, "body": body}),
                            encoding="utf-8", newline="\n")
                        break
        # 2) capture states for both corpora (this maker's expressive + suppressed)
        def load_set(glob_dir, pattern, maker_filter=None):
            arts = []
            for p2 in sorted(glob_dir.glob(pattern)):
                d = json.loads(p2.read_text(encoding="utf-8"))
                if maker_filter and d.get("maker") != maker_filter:
                    continue
                body = _a03_strip(d["body"])
                if len(body) > 80:
                    arts.append({"scene": d["scene_i"], "tend": d["tendency"],
                                 "body": body})
            return arts
        expr = load_set(OUT_A / "A01", "art_Qwen2.5-_*.json")
        sup = load_set(out, "sup_*.json")
        st_e, st_s = [], []
        for a in expr:
            st_e.append([h.mean(0) for h in capture_block_states(
                model, tok, a["body"], device="cuda")])
        for a in sup:
            st_s.append([h.mean(0) for h in capture_block_states(
                model, tok, a["body"], device="cuda")])
        n_blocks = len(st_e[0]) if st_e else 0
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    # surface suppression check
    def emo_rate(arts):
        c = t = 0
        for a in arts:
            words = a["body"].lower().split()
            c += sum(1 for w in words if w.strip(".,!?;:'") in EMOTION_WORDS)
            t += len(words)
        return c / t if t else None
    er_e, er_s = emo_rate(expr), emo_rate(sup)
    suppressed_ok = er_e is not None and er_s is not None and er_s < er_e * 0.5

    # decode: winner recipe (centroid at middle third — read A03 winner if present)
    a03p = OUT_A03 / "tournament.json"
    use_blocks = list(range(n_blocks // 3, 2 * n_blocks // 3))
    basis = "centroid"
    if a03p.exists():
        w = json.loads(a03p.read_text(encoding="utf-8")).get("winner")
        if w:
            basis, lname = w.split("|")
            third = n_blocks // 3
            loci_map = {"early": list(range(1, third)),
                        "middle": list(range(third, 2 * third)),
                        "late": list(range(2 * third, n_blocks - 1))}
            use_blocks = loci_map.get(lname, use_blocks)

    def pooled(a_states):
        v = a_states[use_blocks[0]].clone()
        for b in use_blocks[1:]:
            v = v + a_states[b]
        return v / len(use_blocks)
    tends = sorted(TENDENCIES)
    cents = {}
    for t in tends:
        idx = [i for i, a in enumerate(expr) if a["tend"] == t]
        if idx:
            cents[t] = sum((pooled(st_e[i]) for i in idx),
                           start=pooled(st_e[idx[0]]) * 0) / len(idx)
    hits = tot = 0
    for i, a in enumerate(sup):
        if len(cents) < 4:
            break
        if basis == "meandiff":
            rest = {t: sum((cents[u] for u in tends if u != t),
                           start=cents[t] * 0) / 3 for t in tends}
            dirs = {t: (cents[t] - rest[t]) / (cents[t] - rest[t]).norm()
                    for t in tends}
            pred = max(tends, key=lambda t: float(pooled(st_s[i]) @ dirs[t]))
        else:
            pred = min(cents, key=lambda t: float(
                (pooled(st_s[i]) - cents[t]).norm()))
        hits += pred == a["tend"]
        tot += 1
    leak_acc = hits / tot if tot else None
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "n_expressive": len(expr), "n_suppressed": len(sup),
         "emotion_word_rate_expressive": er_e,
         "emotion_word_rate_suppressed": er_s,
         "suppression_verified": suppressed_ok,
         "decode_transfer_expressive_to_suppressed": leak_acc,
         "floor": 0.25, "basis": basis, "blocks": use_blocks}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED" if suppressed_ok else "INSTRUMENT_FAILED",
               closure_reason=None if suppressed_ok else
               "the suppression instruction did not suppress surface emotion",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A06: suppression_verified={suppressed_ok} "
          f"(emo {er_e} -> {er_s}); leak decode {leak_acc}")
    return 0


# ── A05: sparse mixtures (card E24-S3-A05) ──────────────────────────────────────────
# The question in plain language: an artifact written under TWO tendencies at once —
# does the geometry read it as a blend of the two single-tendency directions, or as
# something else? Blend prompts for all six pairs; readout = top-2 centroid match.
# DESIGN CHECK: realization requires BOTH pair anchors and no third (accept-time,
# L156); decode centroids come from the SINGLE-tendency corpus only (never fit on
# blends); chance for top-2-of-4 exact pair is 1/6; per-pair cells (L168).

def a05_prompt(scene: str, t1: str, t2: str) -> str:
    return (f"Situation: {scene}\n{TENDENCY_LINES[t1]} At the same time: "
            f"{TENDENCY_LINES[t2][0].lower()}{TENDENCY_LINES[t2][1:]}\n"
            f"Write a short first-person continuation (50 to 100 words) where BOTH "
            f"impulses are present. End with two lines:\n"
            f"Next: {TENDENCIES[t1]}\nAlso: {TENDENCIES[t2]}\n"
            f"Use exactly those closing phrases and no other tendency's phrase."
            f"\n\nContinuation:")


def a05_realized(text: str, t1: str, t2: str) -> bool:
    low = text.lower()
    hits = {t for t, phr in TENDENCIES.items() if phr.lower()[:24] in low}
    return hits == {t1, t2}


def arm_a05() -> int:
    cell = "E24-S3-A05"
    t0 = time.time()
    out = OUT_A / "A05"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from runners.s3_lib import chat_gen                                           # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from itertools import combinations                                            # noqa: PLC0415
    pairs = list(combinations(sorted(TENDENCIES), 2))
    acquire_gpu_lock("s3_a05")
    try:
        mk = ANCHOR_MODEL
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        for (t1, t2) in pairs:
            for si in range(0, 24, 2):
                dest = out / f"mix_{t1}_{t2}_{si}.json"
                if dest.exists():
                    continue
                for att in range(5):
                    txt = chat_gen(model, tok,
                                   a05_prompt(SCENES[si], t1, t2),
                                   SEED0 + 5000 + si * 64 + att, max_new=220)
                    if a05_realized(txt, t1, t2):
                        body = txt[:txt.lower().find("next:")].strip() \
                            if "next:" in txt.lower() else txt
                        dest.write_text(json.dumps(
                            {"scene_i": si, "pair": [t1, t2], "body": body}),
                            encoding="utf-8", newline="\n")
                        break
        # states for blends + singles (this maker)
        singles = []
        for p2 in sorted((OUT_A / "A01").glob("art_Qwen2.5-_*.json")):
            d = json.loads(p2.read_text(encoding="utf-8"))
            body = _a03_strip(d["body"])
            if len(body) > 80:
                singles.append({"tend": d["tendency"], "body": body})
        blends = []
        for p2 in sorted(out.glob("mix_*.json")):
            d = json.loads(p2.read_text(encoding="utf-8"))
            body = _a03_strip(d["body"])
            if len(body) > 80:
                blends.append({"pair": tuple(d["pair"]), "body": body})
        st_s, st_b = [], []
        for a in singles:
            st_s.append([h.mean(0) for h in capture_block_states(
                model, tok, a["body"], device="cuda")])
        for a in blends:
            st_b.append([h.mean(0) for h in capture_block_states(
                model, tok, a["body"], device="cuda")])
        n_blocks = len(st_s[0]) if st_s else 0
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    third = n_blocks // 3
    use_blocks = list(range(third, 2 * third))

    def pooled(a_states):
        v = a_states[use_blocks[0]].clone()
        for b in use_blocks[1:]:
            v = v + a_states[b]
        return v / len(use_blocks)
    tends = sorted(TENDENCIES)
    cents = {}
    for t in tends:
        idx = [i for i, a in enumerate(singles) if a["tend"] == t]
        if idx:
            cents[t] = sum((pooled(st_s[i]) for i in idx),
                           start=pooled(st_s[idx[0]]) * 0) / len(idx)
    hits = tot = 0
    per_pair = {}
    for i, a in enumerate(blends):
        if len(cents) < 4:
            break
        dists = sorted(tends, key=lambda t: float(
            (pooled(st_b[i]) - cents[t]).norm()))
        top2 = set(dists[:2])
        ok = top2 == set(a["pair"])
        hits += ok
        tot += 1
        key = "|".join(sorted(a["pair"]))
        per_pair.setdefault(key, []).append(int(ok))
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "n_blends": tot,
         "top2_pair_acc": hits / tot if tot else None, "chance": 1 / 6,
         "per_pair": {k: sum(v) / len(v) for k, v in per_pair.items()}},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A05 landed: top-2 pair acc {hits}/{tot}")
    return 0


# ── A07: causal use of the tendency geometry (card E24-S3-A07) ──────────────────────
# The question in plain language: steering along a fitted tendency direction while the
# model writes a NEUTRAL continuation — does the realized tendency move? The A02
# additive-steer pattern applied to the tendency basis, sign pairs and controls, doses
# under the same capability tolerance.
# DESIGN CHECK: blocked behind the A02 anchor (queue needs); directions fit on the
# single-tendency corpus with the anchor line stripped; readout is the mechanical
# forced-choice ending (which single Next-phrase the model completes, all four offered)
# so the measure is accept-time (L156); random-direction control; per-pair cells.

def arm_a07() -> int:
    cell = "E24-S3-A07"
    t0 = time.time()
    out = OUT_A / "A07"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    a02p = OUT_A / "A02" / "anchor.json"
    a02v = json.loads(a02p.read_text(encoding="utf-8")).get("verdict") \
        if a02p.exists() else None
    if a02v != "ANCHOR-STANDS":
        (out / "verdict.json").write_text(json.dumps(
            {"cell": cell, "status": "INSTRUMENT-FAILED",
             "reason": f"A02 steering anchor did not stand ({a02v}); causal "
                       "arms are instrument-limited, not nulls"}, indent=1),
            encoding="utf-8", newline="\n")
        set_status(cell, "INSTRUMENT_FAILED",
                   closure_reason=f"blocked by A02 ({a02v})",
                   actual_gpu_minutes=0.0)
        print(f"A07 blocked by A02 ({a02v})")
        return 0
    acquire_gpu_lock("s3_a07")
    try:
        mk = ANCHOR_MODEL
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        singles = []
        for p2 in sorted((OUT_A / "A01").glob("art_Qwen2.5-_*.json")):
            d = json.loads(p2.read_text(encoding="utf-8"))
            body = _a03_strip(d["body"])
            if len(body) > 80:
                singles.append({"tend": d["tendency"], "body": body})
        states = []
        for a in singles:
            states.append([h.mean(0) for h in capture_block_states(
                model, tok, a["body"], device="cuda")])
        n_blocks = len(states[0])
        third = n_blocks // 3
        locus = list(range(third, 2 * third, 2))
        tends = sorted(TENDENCIES)
        dirs = {}
        import torch as _t                                                        # noqa: PLC0415
        for b in locus:
            cents = {}
            for t in tends:
                idx = [i for i, a in enumerate(singles) if a["tend"] == t]
                cents[t] = _t.stack([states[i][b] for i in idx]).mean(0)
            allm = _t.stack(list(cents.values())).mean(0)
            dirs[b] = {t: (cents[t] - allm) / (cents[t] - allm).norm()
                       for t in tends}
        mean_norm = float(_t.stack(
            [states[i][locus[0]] for i in range(len(states))]
        ).norm(dim=1).mean())

        from contextlib import ExitStack                                          # noqa: PLC0415

        def steer_ctx(steer_t, sign, rand, alpha, seed):
            """ExitStack of additive steers on every locus block (A02's hook)."""
            stack = ExitStack()
            if steer_t is None or alpha == 0.0:
                return stack
            g = _t.Generator().manual_seed(seed)
            for b in locus:
                d = dirs[b][steer_t]
                if rand:
                    r = _t.randn(d.shape[0], generator=g)
                    r = r - (r @ d) * d
                    d = r / r.norm()
                stack.enter_context(additive_steer(model, [b], d, sign * alpha))
            return stack

        def forced_choice(scene: str, steer_t, sign: float, rand: bool,
                          seed: int, alpha: float) -> str | None:
            """Score the four Next-lines as continuations; argmax = realized."""
            prompt = (f"Situation: {scene}\nWrite one sentence about what you "
                      f"notice, then finish with a single line of the form "
                      f"'Next: <your impulse>'.\n\nI look around carefully."
                      f"\nNext:")
            scores = {}
            with steer_ctx(steer_t, sign, rand, alpha, seed):
                for t in tends:
                    scores[t] = _mean_logp(model, tok, prompt, " " + TENDENCIES[t])
            return max(scores, key=scores.get)

        def fact_logp(steer_t, alpha):
            with steer_ctx(steer_t, +1.0, False, alpha, SEED0):
                vals = [_mean_logp(model, tok, "A plain fact: ", f)
                        for f in FACT_CONT]
            return sum(vals) / len(vals)

        # dose ladder under the A02 capability tolerance, largest passing dose kept
        base_fact = fact_logp(None, 0.0)
        ladder = {}
        alpha = None
        for frac in (0.12, 0.08, 0.04):
            a_try = frac * mean_norm
            worst = min(fact_logp(t, a_try) for t in tends)
            ok = worst >= base_fact - 0.15 * abs(base_fact)
            ladder[str(frac)] = {"alpha": a_try, "worst_fact_logp": worst,
                                 "capability_ok": ok}
            if ok and alpha is None:
                alpha = a_try
                chosen_frac = frac
        if alpha is None:
            (out / "verdict.json").write_text(json.dumps(
                {"cell": cell, "status": "INSTRUMENT-FAILED",
                 "reason": "no tendency-steering dose passes the capability "
                           "tolerance", "dose_ladder": ladder}, indent=1),
                encoding="utf-8", newline="\n")
            set_status(cell, "INSTRUMENT_FAILED",
                       closure_reason="no dose passes capability tolerance",
                       actual_gpu_minutes=(time.time() - t0) / 60)
            del model
            torch.cuda.empty_cache()
            return 0

        rows = []
        for si in range(0, 24, 2):
            scene = SCENES[si]
            base_pick = forced_choice(scene, None, 0.0, False, SEED0 + si, 0.0)
            for t in tends:
                up = forced_choice(scene, t, +1.0, False, SEED0 + si, alpha)
                dn = forced_choice(scene, t, -1.0, False, SEED0 + si, alpha)
                rnd = forced_choice(scene, t, +1.0, True, SEED0 + si, alpha)
                rows.append({"scene_i": si, "steer": t, "base": base_pick,
                             "plus": up, "minus": dn, "random": rnd})
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    n = len(rows)
    plus_hit = sum(1 for r in rows if r["plus"] == r["steer"]) / n
    base_hit = sum(1 for r in rows if r["base"] == r["steer"]) / n
    minus_hit = sum(1 for r in rows if r["minus"] == r["steer"]) / n
    rand_hit = sum(1 for r in rows if r["random"] == r["steer"]) / n
    causal = plus_hit > base_hit and minus_hit < base_hit and \
        abs(rand_hit - base_hit) < (plus_hit - base_hit) / 2
    per_tend = {}
    for t in sorted(TENDENCIES):
        sub = [r for r in rows if r["steer"] == t]
        per_tend[t] = {"plus": sum(1 for r in sub if r["plus"] == t) / len(sub),
                       "base": sum(1 for r in sub if r["base"] == t) / len(sub),
                       "minus": sum(1 for r in sub if r["minus"] == t) / len(sub),
                       "random": sum(1 for r in sub if r["random"] == t) / len(sub)}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "n_cells": n, "alpha": alpha, "dose_frac": chosen_frac,
         "dose_ladder": ladder, "locus": locus,
         "steered_tendency_rate": {"plus": plus_hit, "base": base_hit,
                                   "minus": minus_hit, "random": rand_hit},
         "per_tendency": per_tend,
         "causal_signature": causal}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A07 landed: +{plus_hit:.3f} base {base_hit:.3f} -{minus_hit:.3f} "
          f"rand {rand_hit:.3f}; causal={causal}")
    return 0


# ── A06/X4: second episode domain with a VERIFIABLE suppression channel ─────────────
# DESIGN CHECK (the L201 lesson, applied): before any generation, audit candidate
# surface channels for dynamic range on the EXISTING expressive corpus; only a channel
# the makers actually use can verify suppression. If no channel has range, the cell
# closes instrument-limited with the audit as its receipt — no GPU is spent on an
# unverifiable manipulation.

SCENES2 = [
    "The night train pulls in two hours early with its windows dark.",
    "A second key to your studio appears on the communal board.",
    "The orchard's oldest tree has been wrapped in surveyor's tape.",
    "Your name tops a volunteer list you never signed.",
    "The tide leaves a line of blue shells nobody can name.",
    "A courier delivers a crate addressed to the previous tenant.",
    "The choir loft light burns at three in the morning.",
    "Someone has been feeding the strays behind the depot.",
    "The archive's request slip comes back stamped REFUSED.",
    "A drone drops a ribboned box on the allotment path.",
    "The harbor buoy rings though the water is glass.",
    "Your carpool partner takes a turn away from the office.",
]
CHANNELS = {
    "first_person_feeling": r"\bi (feel|felt|am afraid|am angry|am curious|care)\b",
    "intensifiers": r"\b(very|so|really|utterly|deeply|incredibly)\b",
    "exclamations": r"!",
    "emotion_lexicon": None,      # the L201 channel, kept for the audit record
}


def _channel_rate(bodies, pattern):
    import re as _re                                                              # noqa: PLC0415
    if pattern is None:
        total = hits = 0
        for b in bodies:
            words = b.lower().split()
            total += len(words)
            hits += sum(1 for w in words
                        if w.strip(".,!?;:'") in EMOTION_WORDS)
        return hits / total if total else 0.0
    total = hits = 0
    for b in bodies:
        total += max(1, len(b.split()))
        hits += len(_re.findall(pattern, b, _re.I))
    return hits / total


def arm_a06x4() -> int:
    cell = "E24-S3-A06/X4"
    t0 = time.time()
    out = OUT_A / "A06"
    out.mkdir(parents=True, exist_ok=True)
    bodies = []
    for p2 in sorted((OUT_A / "A01").glob("art_*.json")):
        d = json.loads(p2.read_text(encoding="utf-8"))
        bodies.append(d["body"])
    audit = {name: _channel_rate(bodies, pat)
             for name, pat in CHANNELS.items()}
    RANGE_FLOOR = 0.012        # per-word rate a halving could visibly cross
    usable = {k: v for k, v in audit.items() if v >= RANGE_FLOOR}
    if not usable:
        (out / "domain2.json").write_text(json.dumps(
            {"cell": cell, "status": "INSTRUMENT-LIMITED",
             "channel_audit": audit, "range_floor": RANGE_FLOOR,
             "reason": "no surface channel in the expressive corpus carries "
                       "enough signal for a suppression manipulation to be "
                       "verifiable; the L201 failure is corpus-general, not "
                       "scene-bank-specific"}, indent=1),
            encoding="utf-8", newline="\n")
        set_status(cell, "INSTRUMENT_FAILED",
                   closure_reason="no verifiable suppression channel "
                   f"(max rate {max(audit.values()):.4f} < {RANGE_FLOOR})",
                   actual_gpu_minutes=(time.time() - t0) / 60)
        print(f"A06/X4 instrument-limited: audit {json.dumps(audit)}")
        return 0
    channel = max(usable, key=usable.get)
    # a channel exists: generate expressive+suppressed twins on the SECOND bank
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from runners.s3_lib import chat_gen                                           # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    acquire_gpu_lock("s3_a06x4")
    try:
        mk = ANCHOR_MODEL
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        arts = {"expressive": [], "suppressed": []}
        for si, scene in enumerate(SCENES2):
            for tend in TENDENCIES:
                for cond in ("expressive", "suppressed"):
                    dest = out / f"d2_{cond[:3]}_{si}_{tend}.json"
                    if dest.exists():
                        arts[cond].append(
                            json.loads(dest.read_text(encoding="utf-8")))
                        continue
                    prompt = a01_prompt(scene, tend)
                    if cond == "suppressed":
                        prompt = prompt.replace(
                            "Write a short first-person continuation",
                            SUPPRESS_LINE
                            + "\nWrite a short first-person continuation")
                    for att in range(5):
                        txt = chat_gen(model, tok, prompt,
                                       SEED0 + 7000 + si * 64 + att,
                                       max_new=200)
                        if a01_realized(txt) == tend:
                            body = txt[:txt.lower().find("next:")].strip() \
                                if "next:" in txt.lower() else txt
                            rec = {"scene_i": si, "tendency": tend,
                                   "body": body}
                            dest.write_text(json.dumps(rec),
                                            encoding="utf-8", newline="\n")
                            arts[cond].append(rec)
                            break
        # verify suppression on the audited channel BEFORE any decode
        r_e = _channel_rate([a["body"] for a in arts["expressive"]],
                            CHANNELS[channel])
        r_s = _channel_rate([a["body"] for a in arts["suppressed"]],
                            CHANNELS[channel])
        verified = r_e >= RANGE_FLOOR and r_s < r_e * 0.5
        leak = None
        if verified:
            st = {"expressive": [], "suppressed": []}
            kept = {"expressive": [], "suppressed": []}
            for cond in ("expressive", "suppressed"):
                for a in arts[cond]:
                    body = _a03_strip(a["body"])
                    if len(body) > 80:
                        kept[cond].append(a["tendency"])
                        st[cond].append([h.mean(0) for h in
                                         capture_block_states(
                                             model, tok, body, device="cuda")])
            n_blocks = len(st["expressive"][0])
            third = n_blocks // 3
            blocks = list(range(2 * third, n_blocks - 1))

            def pooled(a_states):
                v = a_states[blocks[0]].clone()
                for b in blocks[1:]:
                    v = v + a_states[b]
                return v / len(blocks)
            tends = sorted(TENDENCIES)
            cents = {}
            for i, t in enumerate(tends):
                idx = [j for j, lab in enumerate(kept["expressive"])
                       if lab == t]
                if idx:
                    cents[t] = sum((pooled(st["expressive"][j]) for j in idx),
                                   start=pooled(st["expressive"][idx[0]]) * 0
                                   ) / len(idx)
            hits = tot = 0
            for j, lab in enumerate(kept["suppressed"]):
                if len(cents) < 4:
                    break
                pred = min(cents, key=lambda t: float(
                    (pooled(st["suppressed"][j]) - cents[t]).norm()))
                hits += pred == lab
                tot += 1
            leak = hits / tot if tot else None
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    (out / "domain2.json").write_text(json.dumps(
        {"cell": cell, "channel_audit": audit, "channel_used": channel,
         "expressive_rate": r_e, "suppressed_rate": r_s,
         "suppression_verified": verified,
         "leak_decode_expressive_to_suppressed": leak, "floor": 0.25,
         "n_expressive": len(arts["expressive"]),
         "n_suppressed": len(arts["suppressed"])}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED" if verified else "INSTRUMENT_FAILED",
               closure_reason=None if verified else
               "suppression unverifiable on the audited channel",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A06/X4: channel {channel} {r_e:.4f}->{r_s:.4f} verified={verified} "
          f"leak={leak}")
    return 0



# ── A07/R5: held-out maker prediction under congruent and incongruent steering ────────
# DESIGN CHECK (2026-08-28): A07 measured own-impulse steering on the reader's forced
# choice and never the prediction of a held-out maker the card asked for (errata
# A07-S3), so the affect-to-inversion bridge was OPEN by omission. Here the reader
# infers the tendency of a maker it was not fit on: centroids and directions are fit on
# one maker's A01 artifacts (SmolLM's 96 or Qwen's 48) and tested on the other's (two
# folds), bodies stripped of the tendency phrase (a lookup otherwise). Readouts per
# held-out artifact: nearest-centroid decoding at the A07 locus; the prompted four-way
# inference (label likelihood, randomized order); and that inference under additive
# steering with the direction of the TRUE tendency (congruent), of another tendency
# (incongruent, the next in a fixed cycle), a norm-matched random direction orthogonal
# to the congruent one, and zero, at the largest dose passing A07's capability
# tolerance for that fold. Balanced accuracy and the truth's log score, per fold and per
# tendency, paired over artifacts. NULL: congruent minus zero 0 on the truth's log
# score; ALTERNATIVE (selective causal use): congruent above zero and incongruent below
# it with random near zero; failure direction guarded: a generic effect (random moves as
# much as congruent) is affect steering, not the project mechanism, and reads as such;
# a decode below chance on the held-out maker voids the steering read for that fold.
# Two makers, one reader checkpoint, one artifact domain: the card's floor (two domains,
# two checkpoints) is not met and the receipt says so. A07's verdict.json is untouched;
# this writes verdict_b.json and rows_b.jsonl.
A07B_CYCLE = {"anger": "care", "care": "curiosity", "curiosity": "fear", "fear": "anger"}


def _a07b_balanced(rows, key_pred="pred"):
    tends = sorted(TENDENCIES)
    accs = []
    for t in tends:
        sub = [r for r in rows if r["truth"] == t]
        if sub:
            accs.append(sum(1 for r in sub if r[key_pred] == t) / len(sub))
    return sum(accs) / len(accs) if accs else None


def arm_a07b() -> int:
    cell = "E24-S3-A07/R5"
    t0 = time.time()
    out = OUT_A / "A07"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from contextlib import ExitStack                                              # noqa: PLC0415
    from runners import s4_lib                                                    # noqa: PLC0415
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    a02p = OUT_A / "A02" / "anchor.json"
    a02v = json.loads(a02p.read_text(encoding="utf-8")).get("verdict") if a02p.exists() else None
    if a02v != "ANCHOR-STANDS":
        (out / "verdict_b.json").write_text(json.dumps(
            {"cell": cell, "status": "INSTRUMENT-FAILED",
             "reason": f"A02 steering anchor did not stand ({a02v})"}, indent=1),
            encoding="utf-8", newline="\n")
        set_status(cell, "INSTRUMENT_FAILED", closure_reason=f"blocked by A02 ({a02v})",
                   actual_gpu_minutes=0.0)
        return 0
    arts = []
    for p2 in sorted((OUT_A / "A01").glob("art_*.json")):
        d = json.loads(p2.read_text(encoding="utf-8"))
        body = _a03_strip(d["body"])
        if len(body) > 80 and d["tendency"] in TENDENCIES:
            arts.append({"tend": d["tendency"], "body": body, "maker": d["maker"],
                         "fam": "qwen" if "qwen" in d["maker"].lower() else "smollm",
                         "file": p2.name})
    folds = (("smollm", "qwen"), ("qwen", "smollm"))
    tends = sorted(TENDENCIES)
    rows_path = out / "rows_b.jsonl"
    rows = []
    acquire_gpu_lock("s3_a07b")
    try:
        tok = AutoTokenizer.from_pretrained(ANCHOR_MODEL)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            ANCHOR_MODEL, dtype=torch.float16).to("cuda").eval()
        states = [[h.mean(0) for h in capture_block_states(model, tok, a["body"], device="cuda")]
                  for a in arts]
        n_blocks = len(states[0])
        third = n_blocks // 3
        locus = list(range(third, 2 * third, 2))
        fold_info = {}
        for fit_fam, test_fam in folds:
            fit_idx = [i for i, a in enumerate(arts) if a["fam"] == fit_fam]
            test_idx = [i for i, a in enumerate(arts) if a["fam"] == test_fam]
            cents = {}
            dirs = {}
            for b in locus:
                cb = {}
                for t in tends:
                    idx = [i for i in fit_idx if arts[i]["tend"] == t]
                    cb[t] = torch.stack([states[i][b] for i in idx]).mean(0)
                cents[b] = cb
                allm = torch.stack(list(cb.values())).mean(0)
                dirs[b] = {t: (cb[t] - allm) / (cb[t] - allm).norm() for t in tends}
            mean_norm = float(torch.stack([states[i][locus[0]] for i in fit_idx]).norm(dim=1).mean())

            def steer_ctx(direction_of_block, alpha):
                stack = ExitStack()
                if direction_of_block is None or alpha == 0.0:
                    return stack
                for b in locus:
                    stack.enter_context(additive_steer(model, [b], direction_of_block[b], alpha))
                return stack

            def fact_logp(t, alpha):
                with steer_ctx({b: dirs[b][t] for b in locus} if t else None, alpha):
                    vals = [_mean_logp(model, tok, "A plain fact: ", f) for f in FACT_CONT]
                return sum(vals) / len(vals)

            base_fact = fact_logp(None, 0.0)
            ladder = {}
            alpha = None
            chosen_frac = None
            for frac in (0.12, 0.08, 0.04):
                a_try = frac * mean_norm
                worst = min(fact_logp(t, a_try) for t in tends)
                ok = worst >= base_fact - 0.15 * abs(base_fact)
                ladder[str(frac)] = {"alpha": a_try, "worst_fact_logp": worst, "capability_ok": ok}
                if ok and alpha is None:
                    alpha, chosen_frac = a_try, frac
            fold_info[f"{fit_fam}->{test_fam}"] = {
                "n_fit": len(fit_idx), "n_test": len(test_idx), "locus": locus,
                "alpha": alpha, "dose_frac": chosen_frac, "dose_ladder": ladder}
            for i in test_idx:
                a = arts[i]
                # (1) nearest-centroid decode over the locus
                dist = {t: sum(float((states[i][b] - cents[b][t]).norm()) for b in locus) for t in tends}
                decode_pred = min(dist, key=dist.get)
                body = (f"Someone wrote this short passage about a situation they were in:\n"
                        f"\"{a['body']}\"\n\nWhich impulse was driving the writer?")
                rng = random.Random(SEED0 + 7000 + i)
                conds = {"zero": None}
                if alpha is not None:
                    g = torch.Generator().manual_seed(SEED0 + 7100 + i)
                    rand_dirs = {}
                    for b in locus:
                        d = dirs[b][a["tend"]]
                        r = torch.randn(d.shape[0], generator=g)
                        r = r - (r @ d) * d
                        rand_dirs[b] = r / r.norm()
                    conds["congruent"] = {b: dirs[b][a["tend"]] for b in locus}
                    conds["incongruent"] = {b: dirs[b][A07B_CYCLE[a["tend"]]] for b in locus}
                    conds["random"] = rand_dirs
                for cond, dmap in conds.items():
                    with steer_ctx(dmap, alpha or 0.0):
                        r = s4_lib.likelihood_choice(model, tok, body, dict(TENDENCIES),
                                                     random.Random(rng.randrange(10 ** 9)))
                    row = {"fold": f"{fit_fam}->{test_fam}", "art": a["file"], "maker": a["maker"],
                           "truth": a["tend"], "cond": cond, "decode_pred": decode_pred,
                           "pred": r["pred"] if r["valid"] else None,
                           "log_score_truth": (s4_lib.log_score(r["probs"], a["tend"]) if r["valid"] else None),
                           "p_truth": r["probs"][a["tend"]] if r["valid"] else None,
                           "valid": bool(r["valid"])}
                    rows.append(row)
                    with open(rows_path, "a", encoding="utf-8", newline="\n") as fh:
                        fh.write(json.dumps(row) + "\n")
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    verdict = {"cell": cell, "reader": ANCHOR_MODEL, "n_artifacts": len(arts),
               "folds": fold_info, "per_fold": {}, "pooled": {}}
    for fold in fold_info:
        fr = [r for r in rows if r["fold"] == fold and r["valid"]]
        zero = [r for r in fr if r["cond"] == "zero"]
        decode_rows = [{"truth": r["truth"], "pred": r["decode_pred"]} for r in zero]
        per = {"decode_balanced_acc": _a07b_balanced(decode_rows),
               "prompted_balanced_acc_zero": _a07b_balanced(zero),
               "mean_log_score_zero": sum(r["log_score_truth"] for r in zero) / max(1, len(zero)),
               "per_tendency_zero": {t: {"n": sum(1 for r in zero if r["truth"] == t),
                                         "acc": (sum(1 for r in zero if r["truth"] == t and r["pred"] == t)
                                                 / max(1, sum(1 for r in zero if r["truth"] == t)))}
                                     for t in tends},
               "conditions": {}}
        zero_by = {r["art"]: r for r in zero}
        for cond in ("congruent", "incongruent", "random"):
            cr = [r for r in fr if r["cond"] == cond]
            if not cr:
                continue
            diffs = [r["log_score_truth"] - zero_by[r["art"]]["log_score_truth"] for r in cr if r["art"] in zero_by]
            obs, pv = perm_p(diffs, SEED0 + 7200) if len(diffs) >= 2 else (None, None)
            per["conditions"][cond] = {"n": len(diffs), "balanced_acc": _a07b_balanced(cr),
                                       "log_score_minus_zero": obs, "perm_p": pv}
        c = per["conditions"]
        per["selective_signature"] = bool(
            c.get("congruent", {}).get("log_score_minus_zero") is not None
            and c["congruent"]["log_score_minus_zero"] > 0 and c["congruent"]["perm_p"] < 0.05
            and c.get("incongruent", {}).get("log_score_minus_zero", 0) < 0
            and abs(c.get("random", {}).get("log_score_minus_zero", 0)) < c["congruent"]["log_score_minus_zero"] / 2)
        per["decode_void"] = (per["decode_balanced_acc"] or 0) < 0.25
        verdict["per_fold"][fold] = per
    allv = [r for r in rows if r["valid"]]
    verdict["pooled"] = {"decode_balanced_acc": _a07b_balanced(
                             [{"truth": r["truth"], "pred": r["decode_pred"]} for r in allv if r["cond"] == "zero"]),
                         "prompted_balanced_acc_zero": _a07b_balanced([r for r in allv if r["cond"] == "zero"]),
                         "selective_in_folds": [f for f, p in verdict["per_fold"].items() if p["selective_signature"]]}
    verdict["floor_note"] = ("two makers, one reader checkpoint, one artifact domain: the card's two-domain, "
                             "two-checkpoint floor is not met; this is the first held-out maker read, not a closure")
    verdict["first_attempt_pointer"] = "results/phase_2_4_stage_3/A/A07/verdict.json"
    (out / "verdict_b.json").write_text(json.dumps(verdict, indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"A07/R5 landed: {json.dumps(verdict['pooled'])}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["a01", "a02", "a03", "a04", "a05", "a06",
                             "a06x4", "a07", "a07b"])
    a = ap.parse_args()
    return {"a01": arm_a01, "a02": arm_a02, "a03": arm_a03, "a04": arm_a04,
            "a05": arm_a05, "a06": arm_a06, "a06x4": arm_a06x4,
            "a07": arm_a07, "a07b": arm_a07b}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
