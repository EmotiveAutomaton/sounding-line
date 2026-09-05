"""The student of years (brief §12.4 rung 6, A03/x6): a small adapter continued from the
frozen forward-model adapter on ONE maker's three earlier artifacts (a few gradient steps),
scored on the fourth artifact's cut through the same generative readout, against FM+3 (the
same three artifacts in context) and DOM. Host-side (the model is trained and read in one
process after the cell's capsule batch has closed its server), labeled as such; the per-maker
adapters are discarded after scoring; nothing of one maker reaches another.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §4 (assert the adapter took; record the measured revision), §5 (the
  GPU lock is taken once per invocation).
gates: none here; A03 owns the bands (STU against FMN and DOM, whole and tail). bands:
  the Stage 5 exhaustive bands.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7.scoring import prospective as PS                               # noqa: E402
from runners.stage8 import cards as C                                              # noqa: E402
from runners.stage8 import engines as E                                            # noqa: E402
from runners.stage8.cardrun import CardRun8                                        # noqa: E402
from runners.stage8.constructor import series as MS                                # noqa: E402
from runners.stage8.reader import logfmt as LF                                     # noqa: E402
from runners.stage8.train_adapter import score_next                                # noqa: E402
from soundingline.stage8 import read_registry                                      # noqa: E402

STEPS = 12
LR = 1e-4


def run_student(run: CardRun8, ws: list[dict], readers: list[str]) -> None:
    import torch                                                                  # noqa: PLC0415
    from peft import PeftModel                                                    # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    adapters = read_registry("ADAPTERS") or {}
    with s5_lib.GpuSession(f"s8_student_{run.card.lower()}"):
        for reader in readers:
            name = reader.split(":", 1)[1]
            rec = adapters.get(name)
            if not rec:
                continue
            tok = AutoTokenizer.from_pretrained(rec["base"])
            if tok.pad_token is None:
                tok.pad_token = tok.eos_token
            base = AutoModelForCausalLM.from_pretrained(rec["base"], dtype=torch.bfloat16).to("cuda")
            for w in ws:
                if run.is_done(reader, w["lid"], "STU"):
                    continue
                run.check_deadline()
                model = PeftModel.from_pretrained(base, rec["path"], is_trainable=True)
                model.train()
                opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
                texts = [MS.artifact_log(a) for a in w["series"]["artifacts"][:3]]
                for step in range(STEPS):
                    t = texts[step % len(texts)]
                    ids = tok(t + tok.eos_token, add_special_tokens=True, return_tensors="pt", truncation=True, max_length=1024).input_ids.to("cuda")
                    out = model(input_ids=ids, labels=ids)
                    out.loss.backward()
                    opt.step()
                    opt.zero_grad(set_to_none=True)
                model.eval()
                cond = E.build_condition(dict(C.ALL["A03"]["condition"], n_earlier=0), E._opaque(w["lid"]), run.card)
                ev = E.evidence_for(w, cond)
                b = E.bundle_for(w, cond, ev)
                ids_opt = ev["query"]["next_action_options"]
                cut = len(ev["process_prefix"])
                head = LF.header_from_evidence(ev)
                prefix = LF.compose([], head, LF.prefix_lines(ev["process_prefix"]))
                lines = [LF.event_line(cut, *aid.split(":")) for aid in ids_opt] + [LF.stop_line(cut)]
                with torch.no_grad():
                    lps = score_next(model, tok, prefix, lines)
                m = max(lps)
                z = sum(math.exp(v - m) for v in lps[:-1])
                na = {aid: math.exp(lps[i] - m) / z for i, aid in enumerate(ids_opt)} if ids_opt else {}
                zz = sum(math.exp(v - m) for v in lps)
                pred = {"targets": {"next_action": na, "stop": math.exp(lps[-1] - m) / zz}, "abstain": False, "confidence": max(na.values()) if na else 0.0}
                sc = PS.score(pred, b)
                run.row(w["lid"], reader=reader, arm="STU", factors={"domain": w["domain"], "tail": bool(b.get("tail")), "maker": w.get("maker"), "reveal": w.get("reveal"), "steps": STEPS},
                        truth=b["hidden"].get("next_action"), scores=sc, primary_score=sc.get("primary"), extra={"note": "host-side per-maker adapter, discarded after scoring"})
                run.unit_complete(reader, w["lid"], "STU")
                del model, opt
                torch.cuda.empty_cache()
            del base
            torch.cuda.empty_cache()
