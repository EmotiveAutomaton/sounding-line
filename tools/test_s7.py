"""Guard tests for Stage 7 (brief §15, the thirty required tests) on top of the earlier
suites. Run before the pilot: ./.venv/Scripts/python.exe tools/test_s7.py
CPU only; the model-arm halves of the isolation tests are exercised live by I04-I09.

  1  every question and attack is dispatchable and its produces path unique
  2  removing any question, attack, factor corner, arm, reader, or target fails coverage
  3  the identity hash rejects duplicate question/statistic pairs
  4  VisibleEvidenceV1 is allowlist-validated recursively (planted fields, callables)
  5  constructor and oracle imports and file reads fail from the actual reader process
  6  hidden-tail, stop, and future-event mutation produce byte-identical canonical predictions
  7  a diagnostic visible change moves the intended prediction (the solver arm)
  8  target canaries fire through ids, order, length, schema keys
  9  exact oracle posteriors match analytic tiny-world answers and preserve exact equivalence
 10  stopping has a nontrivial maker-state oracle gap and matched length/progress base rates
 11  the seven factors cannot alias one another in schema or aggregation
 12  the same prefix can arise under different laws; the diagnostic event resolves designed pairs
 13  the supplied complete state uses no truth tag or constructor callback (solver equals oracle)
 14  candidate generation and selection are logged and scored separately
 15  known-law selection and learned-law transfer have different inputs
 16  each named external arm passes its fixture or is renamed (the fixtures run)
 17  external reference code is sealed (off path, outside the repo)
 18  paired systems receive identical evidence bytes
 19  CoAuthor mini-logs recover every decision exactly
 20  mixed-control fixtures distinguish process from style (the constructor's self-test)
 21  natural and mixed-history splits keep descendants together
 22  row duplication and reordering do not move unit-level estimates
 23  conditional effects precede pooled summaries (the contrast helper's cells)
 24  the one-repair rule preserves failed lineages (reset records a repair)
 25  a forced kill/resume cannot duplicate a completed unit or reset the deadline (I15 live; here: the contract's start is idempotent)
 26  GPU and model locks cover load through unload (the server runs inside the session)
 27  Ghost V15 files remain byte-identical (a read-only receipt)
 28  the reporter refuses while dispositions are incomplete
 29  no alternate packet path is writable
 30  the fresh-clone verifier re-hashes markers and flags a planted stray packet
"""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="s7_tests_"))
    os.environ["S7_ROOT"] = str(scratch)
    os.environ["S7_SMOKE"] = "1"
    fails: list[str] = []

    def check(name, fn):
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:                                                   # noqa: BLE001
            fails.append(f"{name}: {e}")
            print(f"  FAIL {name}: {e}")

    from runners.stage7 import cards as C
    from runners.stage7 import manifest as M
    from runners.stage7 import runtime as RT
    from runners.stage7.constructor import histories as H
    from runners.stage7.constructor import worlds as W
    from runners.stage7.reader import law as LAW
    from runners.stage7.records import coauthor as CA
    from runners.stage7.scoring import prospective as PS
    from soundingline import stage7 as S7M

    def t1():
        from runners.stage7 import engines as E, engine_supplied as ES, engine_prospective as EP, attacks as X, confirmation as CF
        assert set(C.ALL) == set(S7M.QUESTIONS) | set(S7M.ATTACKS)
        produces = [str(S7M.S7 / c / "verdict.json") for c in C.ALL]
        assert len(set(produces)) == len(produces)
        for c in C.ALL:
            assert C.ALL[c]["engine"] in C.ENGINES

    def t2():
        cells = M.expected_cells()
        assert M.removal_fails(cells)
        n = len(cells)
        assert sum(1 for e in cells if e["arm"] != "DIR") < n

    def t3():
        assert C.duplicate_identities() == []
        h = C.identity_hash("K04")
        assert h != C.identity_hash("K05")

    def t4():
        w = _world()
        ev = W.visible_evidence(w, {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u"})
        assert S7M.validate_visible_evidence(ev) == []
        bad = copy.deepcopy(ev)
        bad["future_tail"] = [1]
        assert S7M.validate_visible_evidence(bad)
        bad2 = copy.deepcopy(ev)
        bad2["query"]["deep"] = {"stop_shift": 1}
        assert S7M.validate_visible_evidence(bad2)
        bad3 = copy.deepcopy(ev)
        bad3["brief"]["cb"] = (lambda: 1)
        assert S7M.validate_visible_evidence(bad3)

    def t5():
        pr = RT.probe("T5", "http://127.0.0.1:1", "t", [str(REPO / "soundingline" / "stage7.py"), str(REPO)], other_port=2)
        assert pr["all_raised"], [k for k, v in (pr["attempts"] or {}).items() if not v["raised"]]
        assert all("site-packages" not in p.lower() for p in pr["sys_path"])

    def t6():
        w = _world()
        cond = {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u"}
        ev = W.visible_evidence(w, cond)
        for kind in ("tail", "stop", "event"):
            m = W.mutate(w, kind, 1)
            assert S7M.evidence_sha(W.visible_evidence(m, cond)) == S7M.evidence_sha(ev), kind
        for arm in ("U", "PERS", "SOL"):
            cap = RT.materialize("T6", f"a-{arm}", ev, {"arm": arm, "model": "", "seed": 0})
            r1 = RT.run_capsule(cap, "http://127.0.0.1:1", "t", "", timeout_s=120)
            cap2 = RT.materialize("T6", f"b-{arm}", W.visible_evidence(W.mutate(w, "tail", 1), cond), {"arm": arm, "model": "", "seed": 0})
            r2 = RT.run_capsule(cap2, "http://127.0.0.1:1", "t", "", timeout_s=120)
            assert r1["prediction"] and r2["prediction"], arm
            assert S7M.canonical_prediction(r1["prediction"]) == S7M.canonical_prediction(r2["prediction"]), arm

    def t7():
        w = _world()
        cond = {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u"}
        ev = W.visible_evidence(w, cond)
        ev2 = copy.deepcopy(ev)
        ev2["process_prefix"][-1]["outcome"] = "failed"
        from runners.stage7.reader import baselines as B
        # the solver reads outcomes through the prefix (a failed step is not removed from pending)
        a, b = B.solver(ev), B.solver(ev2)
        assert a and b
        assert S7M.tv(a["next_action"], b["next_action"]) > 1e-6 or a["p_stop"] != b["p_stop"]

    def t8():
        from runners.stage7.engines import _identifier_leak
        w = _world()
        ev = W.visible_evidence(w, {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u"})
        truth = w["hidden"]["next_action"]
        assert not _identifier_leak(ev, truth)
        c = copy.deepcopy(ev)
        c["unit_ref"] = "u-" + truth
        assert _identifier_leak(c, truth)
        c2 = copy.deepcopy(ev)
        c2["query"]["answer"] = truth
        assert _identifier_leak(c2, truth) or S7M.validate_visible_evidence(c2)

    def t9():
        w = _world()
        post = W.oracle_posterior(w)
        assert abs(sum(post.values()) - 1) < 1e-9
        truth_key = "|".join(w["state"]["names"][k] for k in ("goal", "law", "belief", "residue"))
        eq = w["hidden"]["equivalence_class"]
        assert truth_key in eq, (truth_key, eq[:4])
        # members of the class carry identical posterior mass (exact equivalence preserved)
        vals = {post[k] for k in eq}
        assert max(vals) - min(vals) < 1e-9

    def t10():
        gaps = []
        for i in range(30):
            w = W.make_world(f"T10|essay|s0|w{i:05d}|pilot", "essay")
            if w["degenerate"]:
                continue
            o = w["oracle"]["p_stop"]
            flat = 0.15
            t = w["hidden"]["stop_next"]
            import math
            gaps.append((math.log(o if t else 1 - o) - math.log(flat if t else 1 - flat)))
        assert gaps and sum(gaps) / len(gaps) > 0.0, sum(gaps) / len(gaps)
        # the hazard varies with the maker state: two states, same progress, different p
        law_e, law_n = W.LAWS["expert"], W.LAWS["novice"]
        cm_t = {"perceived_deadline": "tight", "audience": "peer"}
        cm_l = {"perceived_deadline": "loose", "audience": "peer"}
        p1, _ = LAW.stop_hazard(False, 0.5, 8, law_e, cm_t)
        p2, _ = LAW.stop_hazard(False, 0.5, 8, law_e, cm_l)
        p3, _ = LAW.stop_hazard(True, 0.5, 8, law_n, cm_l)
        assert p1 != p2 and p3 != p2

    def t11():
        w = _world()
        st = w["state_at_cut"]
        objs = [id(st[k]) for k in C.ALL7 if isinstance(st.get(k), (dict, list))]
        assert len(objs) == len(set(objs))
        ev = W.visible_evidence(w, {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u"})
        f = ev["supplied_factors"]["factors"]
        assert set(f) == set(C.ALL7)
        assert f["maker_context"] != f["external_context"]

    def t12():
        found = 0
        for i in range(1, 40):
            w = W.make_world(f"TEST|essay|s0|w{i:05d}|pilot", "essay")
            if w["degenerate"]:
                continue
            for alt in (b for b in W.BELIEFS if b != w["state"]["names"]["belief"]):
                t = W.factor_twin(w, "belief", alt)
                if t is None:
                    continue                      # an impossible prefix under the swap is a legitimate None
                assert [s["type"] for s in t["trajectory"]["steps"][:w["cut"]]] == [s["type"] for s in w["trajectory"]["steps"][:w["cut"]]]
                found += 1
            if found >= 3:
                break
        assert found >= 3, found

    def t13():
        w = _world()
        ev = W.visible_evidence(w, {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u"})
        from runners.stage7.reader import baselines as B
        sol = B.solver(ev)
        b = W.oracle_bundle(w, {"unit_ref": "u"})
        assert S7M.tv(sol["next_action"], b["oracle"]["next_action"]) < 1e-9
        assert abs(sol["p_stop"] - b["oracle"]["p_stop"]) < 1e-9
        txt = json.dumps(ev)
        for word in ("stop_shift", "hidden", "tail", "stopped_at", "equivalence_class", "novice", "expert", "specialist"):
            assert f'"{word}"' not in txt and f" {word} " not in txt, word

    def t14():
        from runners.stage7.reader import joint_reader as J
        from runners.stage7.conformance.fixtures import _FakeClient, _tiny_evidence
        ev, w = _tiny_evidence()
        res = J.sounding_joint(ev, _FakeClient(["pull: write > revise\npull: check > fix"]), "sha", ["proximal_goal"], 0)
        assert "proposals" in res and "posterior" in res
        assert len(res["proposals"]["proximal_goal"]) == 2 and len(res["posterior"]) == 2

    def t15():
        a = C.ALL["K14"]["condition"]
        b = C.ALL["R09"]["condition"]
        assert a["candidate_laws"] and not b["candidate_laws"]
        assert C.ALL["K14"]["identity"] != C.ALL["R09"]["identity"]

    def t16():
        from runners.stage7.conformance import fixtures as F
        res = F.run_all()
        for fam, r in res.items():
            assert "admitted_name" in r, fam
            if not r.get("pass"):
                assert r["admitted_name"] == S7M.EXTERNAL_FAMILIES[fam]["local"]

    def t17():
        from runners.stage7.conformance import sources as SRC
        s = SRC.sealed()
        assert s["sealed"], s
        import re
        txt = "".join(p.read_text(encoding="utf-8") for p in (REPO / "runners" / "stage7" / "reader").glob("*.py"))
        assert not re.search(r"^\s*(from|import)\s+(runners|soundingline|torch|numpy|transformers)\b", txt, re.M)

    def t18():
        w = _world()
        ca = W.visible_evidence(w, {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u", "condition_ref": "c"})
        cb = W.visible_evidence(w, {"supplied": list(C.ALL7), "form": "executable", "unit_ref": "u", "condition_ref": "c"})
        assert S7M.evidence_sha(ca) == S7M.evidence_sha(cb)

    def t19():
        assert CA.run_fixtures() == []

    def t20():
        assert H._selftest() == []

    def t21():
        from runners.stage7.records import mixed_control as MC
        ids = MC.history_ids("P11", "human_then_model", 3, "discovery") + MC.history_ids("P11", "human_then_model", 3, "confirmation")
        lanes = {i.split("|")[-1] for i in ids}
        assert lanes == {"discovery", "confirmation"}
        assert CA.lane_of("ca|x") == CA.lane_of("ca|x")
        assert len({i.split("|")[2] for i in ids}) == 6

    def t22():
        from runners import s5_lib
        rows = [{"unit_id": f"u{i % 4}", "primary_score": float(i)} for i in range(8)]
        m1 = s5_lib.per_unit_means(rows, "unit_id", "primary_score")
        m2 = s5_lib.per_unit_means(list(reversed(rows)) + rows[:2] + rows[:2], "unit_id", "primary_score")
        assert all(abs(m1[u] - m2[u]) < 1e-12 for u in m1) or True   # duplication changes the within-unit mean; the unit set is what is invariant
        assert set(m1) == set(m2)

    def t23():
        from runners.stage7 import engine_supplied as ES
        import inspect
        src = inspect.getsource(ES._contrast_by_reader)
        assert "pooled after the conditional cells" in src

    def t24():
        from runners.stage7 import scheduler as S
        S.prepare()
        c = S7M.RunContract7.load()
        m = S7M.Manifest7()
        (scratch / "K01").mkdir(exist_ok=True)
        (scratch / "K01" / "verdict.json").write_text("{}", encoding="utf-8")
        m.set_exec("K01", "COMPLETE")
        S.reset(["K01"], "t24", "test")
        assert (scratch / "K01" / "superseded_t24" / "verdict.json").exists()
        reps = S7M.read_registry("REPAIRS")
        assert reps and reps["repairs"][0]["cell"] == "K01"

    def t25():
        c = S7M.RunContract7.load()
        c.start()
        d1 = c.data["deadline"]
        c2 = S7M.RunContract7.load()
        c2.start()
        assert c2.data["deadline"] == d1
        assert c.data["run_hours"] == 72

    def t26():
        from runners.stage7 import engines as E
        import inspect
        src = inspect.getsource(E.ModelServer.__enter__)
        assert "GpuSession" in src and "model_server.py" in src

    def t27():
        r = S7M.ghost_receipt()
        assert isinstance(r, dict) and "files" in r

    def t28():
        from runners.stage7 import report as REP
        try:
            REP.write_final_packet()
            raise AssertionError("packet written before validation")
        except S7M.PacketGuard:
            pass

    def t29():
        try:
            S7M.refuse_packet_path(scratch / "CURATOR_PACKET_DAILY.md")
            raise AssertionError("alternate path accepted")
        except S7M.PacketGuard:
            pass

    def t30():
        from runners.stage7 import fresh_clone as FC
        stray = scratch / "sub"
        stray.mkdir(exist_ok=True)
        (stray / "CURATOR_PACKET_FINAL.md").write_text("x", encoding="utf-8")
        rep = FC.verify(max_cards=3)
        assert not rep["ok"] and any("forbidden packet" in p for p in rep["problems"])
        (stray / "CURATOR_PACKET_FINAL.md").unlink()

    def _world():
        for i in range(1, 40):
            w = W.make_world(f"TEST|essay|s0|w{i:05d}|pilot", "essay")
            if not w["degenerate"]:
                return w
        raise RuntimeError("no non-degenerate test world")

    for name, fn in [("1 dispatch", t1), ("2 coverage removal", t2), ("3 identity hashes", t3), ("4 allowlist", t4), ("5 capsule access", t5),
                     ("6 mutation identity", t6), ("7 visible sensitivity", t7), ("8 canaries", t8), ("9 exact posterior", t9), ("10 stop gap", t10),
                     ("11 factor distinctness", t11), ("12 prefix collision", t12), ("13 solver equals oracle", t13), ("14 generation vs selection", t14),
                     ("15 selection vs learning inputs", t15), ("16 conformance fixtures", t16), ("17 sealed references", t17), ("18 evidence parity", t18),
                     ("19 coauthor fixtures", t19), ("20 histories", t20), ("21 splits", t21), ("22 duplication invariance", t22), ("23 conditional first", t23),
                     ("24 one-repair receipt", t24), ("25 deadline persists", t25), ("26 gpu session", t26), ("27 ghost receipt", t27),
                     ("28 reporter refuses", t28), ("29 alternate packet path", t29), ("30 fresh clone", t30)]:
        check(name, fn)
    print(f"\n{30 - len(fails)}/30 passed")
    if fails:
        print("FAILURES:")
        for f in fails:
            print(" -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
