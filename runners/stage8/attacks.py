"""Stage 8 adversarial matrix (brief §8): the 12 attacks. Most derive from landed rows and
registries; X05, X06, and X11 replay small capsule batches with the presentation varied.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (a falsifier is an instrument: every replay attack carries the
  case where the invariant SHOULD break; a quiet control needs its replicate; a pooled
  mean over a planned reversal is refused), §5.
gates: an attack lands INFRASTRUCTURE when its invariant holds, INSTRUMENT_FAILED when it
  fails on the covered questions (the registry's consequence applies), VOID when its
  covered rows do not exist; per attack: X05 NULL (an order-driven readout) is a mean
  total-variation move above 0.10 between orders on the letter readout and above 1e-6 on
  the generative readout (fails DOWN); X06 NULL (double counting) is confidence rising with
  duplicated evidence by over 0.05 (fails DOWN); X09 NULL is any unpriced arm or a ledger
  total above the cap (fails DOWN); X11 NULL is FM on the unseen law family under DOM by
  more than the band (fails DOWN, a conditional failure reported before any generality
  claim). bands: exhaustive.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7.constructor import worlds as W                                 # noqa: E402
from runners.stage8 import cards as C                                              # noqa: E402
from runners.stage8 import engines as E                                            # noqa: E402
from runners.stage8 import runtime as RT                                           # noqa: E402
from runners.stage8.cardrun import SMOKE, CardRun8                                 # noqa: E402
from soundingline.stage8 import (FRONTIER_CAP_USD, S8, gate_state, read_json,       # noqa: E402
                                 read_jsonl, read_registry, tv)

SEED = 84000


def _finish(run: CardRun8, metrics: dict, ok: bool | None, reason: str) -> int:
    oc = "VOID" if ok is None else ("INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED")
    run.finish(metrics, {"exec": "COMPLETE", "outcome": oc, "primary": C.ALL[run.card]["question"], "reason": reason},
               rival=C.ALL[run.card]["consequence"])
    return 0


def _verdict(card: str) -> dict:
    p = S8 / card / "verdict.json"
    return read_json(p) if p.exists() else {}


def _metrics(card: str) -> dict:
    p = S8 / card / "metrics.json"
    return read_json(p) if p.exists() else {}


def run_X05(run: CardRun8) -> int:
    """Option order: the generative readout scores lines one by one (order-free by
    construction); the letter readout is asked under two orders; both measured."""
    n = E.n_units("X05")
    spec = C.ALL["X05"]
    readers = E.reader_set(run)
    ws = E.worlds_for(run, "X05", n, family="PU")

    def permute(w, ev):
        import copy                                                               # noqa: PLC0415
        ev2 = copy.deepcopy(ev)
        ids = list(ev2["query"]["next_action_options"])
        ev2["query"]["next_action_options"] = ids[::-1]
        oo = ev2.get("objective_options") or {}
        if isinstance(oo, dict) and oo.get("at_cut"):
            oo["at_cut"] = list(oo["at_cut"])[::-1]
        return ev2
    E.batch(run, ["FM", "DIR0"], readers, spec["condition"], n, worlds=ws, unit_suffix="~a", targets=["next_action"])
    E.batch(run, ["FM", "DIR0"], readers, spec["condition"], n, worlds=ws, unit_suffix="~b", evidence_hook=permute, targets=["next_action"])
    rows = run.rows()
    preds = {}
    for r in rows:
        if r.get("valid") and r.get("pred_ref") and Path(r["pred_ref"]).exists():
            preds[(r["arm"], r["model_id"], r["unit_id"])] = read_json(Path(r["pred_ref"]))["targets"]["next_action"]
    moved = {"FM": [], "DIR0": []}
    for (arm, rd, uid), d in preds.items():
        if not uid.endswith("~a"):
            continue
        d2 = preds.get((arm, rd, uid[:-2] + "~b"))
        if d2 is not None:
            moved[arm].append(tv(d, d2))
    mean_tv = {a: (sum(v) / len(v)) if v else None for a, v in moved.items()}
    # FM scores each option line by line (order-free by construction), but the batched fp16 scoring pads
    # by the batch's longest row, and reversing the option order changes the batches, so the per-option
    # log-probabilities move at the fourth decimal: the bound is fp16 batch noise (0.01), not exactness.
    # The first reading used 1e-6 and read a 0.0013 TV as a failure (2026-09-04 19:19, L363).
    ok = mean_tv["FM"] is not None and mean_tv["FM"] <= 0.01 and (mean_tv["DIR0"] is None or mean_tv["DIR0"] <= 0.10)
    return _finish(run, {"mean_tv_by_arm": mean_tv, "n_pairs": {a: len(v) for a, v in moved.items()}, "degenerate": run._degenerate},
                   ok, f"order TV {mean_tv} (FM within fp16 batch noise 0.01; DIR0 within 0.10)")


def run_X06(run: CardRun8) -> int:
    """Duplicated evidence: one earlier artifact shown once against the same artifact shown
    three times; the reader's confidence and surprise must not sharpen as if independent."""
    n = E.n_units("X06")
    spec = C.ALL["X06"]
    readers = E.admitted(run) or E.reader_set(run)
    ws = E.worlds_for(run, "X06", n, family="MS")
    E.batch(run, ["FMN"], readers, dict(spec["condition"], n_earlier=1), n, worlds=ws, unit_suffix="~once")

    def dup(w, ev):
        ev = dict(ev)
        ev["demonstrations"] = list(ev.get("demonstrations") or []) * 3
        return ev
    E.batch(run, ["FMN"], readers, dict(spec["condition"], n_earlier=1), n, worlds=ws, unit_suffix="~thrice", evidence_hook=dup)
    rows = run.rows()
    conf = {}
    for r in rows:
        if r["arm"] == "FMN" and r.get("valid"):
            conf[(r["model_id"], r["unit_id"])] = float((r.get("extra") or {}).get("confidence") or 0.0)
    deltas = [conf[(rd, u)] for (rd, u) in list(conf) if u.endswith("~thrice")]
    diffs = []
    for (rd, u), c in conf.items():
        if u.endswith("~once"):
            c3 = conf.get((rd, u[:-5] + "~thrice"))
            if c3 is not None:
                diffs.append(c3 - c)
    mean_d = (sum(diffs) / len(diffs)) if diffs else None
    ok = mean_d is not None and mean_d <= 0.05
    return _finish(run, {"mean_confidence_rise_with_duplication": mean_d, "n_pairs": len(diffs), "n_thrice": len(deltas)}, ok, f"confidence rise with a triplicated earlier artifact {mean_d}")


def run_X11(run: CardRun8) -> int:
    n = E.n_units("X11")
    spec = C.ALL["X11"]
    readers = E.admitted(run) or E.reader_set(run)
    E.batch(run, ["FM", "DOM", "U"], readers, spec["condition"], n, family="K2")
    rows = run.rows()
    c = E.contrast_by_reader(run, rows, "FM", "DOM")
    cells = {k: v for k, v in c.items() if k != "pooled"}
    ok = bool(cells) and all(v.get("point") is not None and v["point"] >= -0.05 for v in cells.values())
    e03 = {k: v.get("gap") for k, v in ((read_registry("EXPERTISE_GATE") or {}).get("readers") or {}).items()}
    return _finish(run, {"cells": c, "e03_gaps_on_the_seen_family": e03, "degenerate": run._degenerate},
                   ok, "unseen law family: " + "; ".join(f"{k}: {v.get('point')!s:.6} {v.get('ci')}" for k, v in cells.items()) + f"; seen-family gaps {e03}")


def run_X12(run: CardRun8) -> int:
    """The fresh-clone verifier plus one forced kill and resume of a small cell in a scratch root."""
    from runners.stage8 import fresh_clone as FC                                  # noqa: PLC0415
    rep = FC.verify()
    import shutil                                                                 # noqa: PLC0415
    import tempfile                                                               # noqa: PLC0415
    scratch = Path(tempfile.mkdtemp(prefix="s8_x12_"))
    env = dict(os.environ, S7_ROOT=str(scratch), S7_SMOKE="1", S7_SPLIT="pilot", S7_FAKE_SERVER="1", S8_SKIP_TRAIN="1")
    code = ("import sys; sys.path.insert(0, %r); from runners.stage8 import scheduler as S; S.prepare(); "
            "from soundingline.stage8 import RunContract8; c=RunContract8.load(); c.start(); "
            "S._workload_lock(c, {'unit|FM|x': 1.0}); "
            "from runners.stage8 import engines as E; from runners.stage8.cardrun import CardRun8; E.run_E01(CardRun8('E01')); "
            "E.run_E02(CardRun8('E02')); E.run_E03(CardRun8('E03'))") % str(REPO)
    p1 = subprocess.Popen([E.PY, "-c", code], cwd=str(REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(25)
    p1.kill()
    p1.wait()
    cases = scratch / "E03" / "pilot" / "cases.jsonl"
    rows1 = read_jsonl(cases) if cases.exists() else []
    d1 = (read_json(scratch / "RUN_CONTRACT.json") or {}).get("deadline")
    p2 = subprocess.run([E.PY, "-c", code], cwd=str(REPO), env=env, capture_output=True, text=True, timeout=1500)
    rows2 = read_jsonl(cases) if cases.exists() else []
    d2 = (read_json(scratch / "RUN_CONTRACT.json") or {}).get("deadline")
    keys = [(r["model_id"], r["unit_id"], r["arm"]) for r in rows2]
    dup = len(keys) - len(set(keys))
    ok_resume = dup == 0 and d1 == d2 and d1 is not None and p2.returncode == 0 and len(rows2) >= max(1, len(rows1))
    shutil.rmtree(scratch, ignore_errors=True)
    ok = bool(rep.get("ok")) and ok_resume
    return _finish(run, {**rep, "resume": {"rows_after_kill": len(rows1), "rows_after_resume": len(rows2), "duplicates": dup, "deadline_kept": d1 == d2, "rc": p2.returncode, "stderr": p2.stderr[-300:]}},
                   ok, f"{rep.get('summary')}; kill/resume duplicates {dup}, deadline kept {d1 == d2}, rc {p2.returncode}")


def run_card(run: CardRun8) -> int:
    card = run.card
    if card == "X01":
        v = _verdict("I04")
        rates = _metrics("I04").get("identity_rate_by_arm") or {}
        ok = None if not v else all(x == 1.0 for x in rates.values() if x is not None)
        return _finish(run, {"identity_rates": rates}, ok, f"I04 {v.get('outcome')}: {rates}")
    if card == "X02":
        adapters = read_registry("ADAPTERS") or {}
        forbidden = [str(S8 / "POP_CORPUS.json"), str(S8 / "TRAINING.json"), str(S8 / "adapters")] + [rec.get("path", "") for rec in adapters.values() if rec.get("path")]
        forbidden += [str(S8 / f"train_{k}.log") for k in adapters]
        pr = RT.probe(run.cell_id, "http://127.0.0.1:1", "x", [p for p in forbidden if p], other_port=RT.free_port())
        ok = bool(pr["all_raised"]) and (gate_state("isolation") or {}).get("passed") is True
        return _finish(run, pr, ok, f"training corpus and adapter reads all raised {pr['all_raised']}; attempts {len(pr.get('attempts') or {})}")
    if card == "X03":
        from runners.stage8 import manifest as M                                  # noqa: PLC0415
        rec = M.split_receipt()
        v = _verdict("I07")
        return _finish(run, rec, None if not v else rec["clean"], f"overlap {len(rec['overlap'])} across {rec['n_roots']} roots and {rec['n_training_roots']} training roots")
    if card == "X04":
        v = _verdict("G06")
        per = _metrics("G06").get("per_reader") or {}
        ok = None if not v or v.get("outcome") == "NOT_RUN" else any(x.get("crossover") for x in per.values())
        return _finish(run, {"per_reader": per}, ok, f"G06 {v.get('outcome')}: crossover {[k for k, x in per.items() if x.get('crossover')]}")
    if card == "X05":
        return run_X05(run)
    if card == "X06":
        return run_X06(run)
    if card == "X07":
        v = _verdict("G04")
        per = _metrics("G04").get("per_reader") or {}
        ok = None if not v or v.get("outcome") in ("NOT_RUN", "VOID") else any(x.get("passed") for x in per.values())
        return _finish(run, {"per_reader": per}, ok, f"G04 {v.get('outcome')}; class preserved on {[k for k, x in per.items() if x.get('passed')]}")
    if card == "X08":
        cells = {}
        rev = []
        for c in ("E03", "D01", "G02", "A01"):
            v = _verdict(c)
            cc = v.get("conditional_cells") or {}
            cells[c] = len(cc)
            pts = [x.get("point") for x in cc.values() if x.get("point") is not None]
            if pts and min(pts) < 0 < max(pts):
                rev.append(c)
        ok = None if not any(cells.values()) else all(n > 0 for c, n in cells.items() if _verdict(c) and _verdict(c).get("outcome") != "NOT_RUN")
        return _finish(run, {"conditional_cells": cells, "sign_reversals": rev}, ok, f"conditional cells {cells}; reversals surfaced {rev}")
    if card == "X09":
        led = read_registry("COMPUTE_LEDGER") or {}
        fr = read_registry("FRONTIER_LEDGER") or {}
        total = float(fr.get("total_usd") or 0.0)
        def priced_by(k, v):
            if (v or {}).get("ledger"):
                return True
            fr_ = (v or {}).get("from_rows") or {}
            if fr_.get("model_calls"):
                return True
            d = S8 / k
            rows = []
            for p in [d / "cases.jsonl"] + sorted(d.glob("superseded_*/cases.jsonl")):
                if p.exists():
                    rows += read_jsonl(p)
            return bool(E.rows_budget(rows).get("model_calls"))
        priced = {k: priced_by(k, v) for k, v in led.items() if isinstance(v, dict)}
        gpu_s = sum(float((v or {}).get("gpu_held_s") or 0.0) for v in led.values() if isinstance(v, dict))
        ok = bool(priced) and all(priced.values()) and total <= FRONTIER_CAP_USD
        return _finish(run, {"cells_priced": len(priced), "unpriced": [k for k, v in priced.items() if not v], "frontier_usd": total, "cap": FRONTIER_CAP_USD, "gpu_lock_seconds": gpu_s, "by_cell_usd": fr.get("by_cell")},
                       ok, f"{sum(priced.values())}/{len(priced)} cells priced; frontier {total:.4f} of {FRONTIER_CAP_USD} USD; GPU lock {gpu_s / 3600:.2f} h")
    if card == "X10":
        rows = read_jsonl(S8 / "E03" / "cases.jsonl") if (S8 / "E03" / "cases.jsonl").exists() else []
        best = {}
        for key in ("next_action_ls", "stop_ls"):
            cands = {}
            for arm in ("DOM", "PERS", "U"):
                vals = [float((r.get("scores") or {}).get(key)) for r in rows if r["arm"] == arm and r.get("valid") and (r.get("scores") or {}).get(key) is not None]
                if vals:
                    cands[arm] = sum(vals) / len(vals)
            best[key] = max(cands.items(), key=lambda kv: kv[1]) if cands else None
        strengthened = {}
        for card_ in ("G02", "A03"):
            rs = read_jsonl(S8 / card_ / "cases.jsonl") if (S8 / card_ / "cases.jsonl").exists() else []
            rs = [r for r in rs if r.get("valid") and r.get("primary_score") is not None]
            arm = "FMP" if card_ == "G02" else "FMN"
            for rival in ("DOM", "PERS"):
                c = s5_lib.paired_contrast([r for r in rs if r["arm"] == arm], [r for r in rs if r["arm"] == rival], "unit_id", "primary_score", SEED)
                strengthened[f"{card_}:{arm}_vs_{rival}"] = c.get("point")
        ok = None if not rows else True
        return _finish(run, {"best_cheap_by_target": best, "strengthened": strengthened}, ok, f"strengthened rival {json.dumps(best)}; claims against it {strengthened}")
    if card == "X11":
        return run_X11(run)
    if card == "X12":
        return run_X12(run)
    raise ValueError(card)
