"""Guard tests for Stage 8 (brief §13, §18 pre-mortem). Run before the pilot:
./.venv/Scripts/python.exe tests/test_stage8_guards.py   (CPU only; the fake transport)

  1  every card is dispatchable and its produces path unique
  2  removing any question fails coverage; identity hashes distinct
  3  the log grammar round-trips (render, parse) and the capsule's header equals the constructor's
  4  purpose worlds leak neither the purpose name nor the required sections; planted canaries are caught
  5  the purpose equivalence class contains the truth and equivalence worlds exist
  6  the reveal parameter scales the residue; earlier logs carry no goal line
  7  the generation feasibility check catches an infeasible log; the world's own log passes
  8  the population marginal likelihood is a log probability; the tail threshold is a number written before readers
  9  the split receipt flags a planted overlap between a test root and the training manifest
 10  the frontier cap raises on a planted overspend before the request
 11  the adapter hash changes when a byte changes
 12  the FM readout through the fake server yields a normalized prediction and the per-event mode scores every boundary
 13  the capsule probe raises on every forbidden access (training corpus and adapter paths included)
 14  the mutation attack through the fake FM is byte-identical and the oracle differs (I04 in smoke)
 15  the re-lock sizes the ladder from measured charges, not the pilot forecast
 16  the closure tail is ordered B04, X12, B03 in the manifest
 17  the reporter refuses before closure
 18  a theory-change interrupt blocks its dependents and nothing else
 19  the reference workspace is sealed (outside the repository, off sys.path)
 20  every corpus loader parses its fixture
 21  the keystone auto-sign requires every mechanical check
 22  the second law family registers and constructs live worlds
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
    scratch = Path(tempfile.mkdtemp(prefix="s8_tests_"))
    os.environ["S7_ROOT"] = str(scratch)
    os.environ["S7_STAGE"] = "phase_2_4_stage_8"
    os.environ["S7_SMOKE"] = "1"
    os.environ["S7_FAKE_SERVER"] = "1"
    os.environ["S8_SKIP_TRAIN"] = "1"
    fails: list[str] = []

    def check(name, fn):
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:                                                   # noqa: BLE001
            import traceback                                                      # noqa: PLC0415
            fails.append(f"{name}: {e!r}")
            print(f"  FAIL {name}: {e!r}")
            traceback.print_exc(limit=3)

    from runners.stage8 import cards as C
    from runners.stage8 import engines as E
    from runners.stage8 import manifest as M
    from runners.stage8 import runtime as RT
    from runners.stage8 import scheduler as S
    from runners.stage8.constructor import gradient as G, population as POP, purpose as PU, series as MS
    from runners.stage8.reader import logfmt as LF
    from soundingline import stage8 as S8M
    from soundingline.stage8 import (FrontierCap, Manifest8, RunContract8, adapter_hash, frontier_charge, read_registry,
                                     record_interrupt, validate_visible_evidence, write_registry)

    def t1():
        S.prepare()
        m = Manifest8()
        assert set(C.ALL) == set(m.cells), set(C.ALL) ^ set(m.cells)
        produces = [c["produces"] for c in m.cells.values()]
        assert len(produces) == len(set(produces))
        for card, spec in C.ALL.items():
            eng = spec["engine"]
            if card in E.I_CARDS or card in E.E_CARDS:
                continue
            if card == "E07" or eng in ("difference", "purpose", "accumulation"):
                from runners.stage8 import engine_dpa as DPA
                assert card in DPA.DISPATCH, card
            elif eng in ("testbed", "closure", "attack"):
                continue
            else:
                raise AssertionError(f"{card} has no engine")

    def t2():
        exp = M.expected_cells()
        assert M.removal_fails(exp)
        assert not C.duplicate_identities()

    def t3():
        w = next(x for x in (POP.sample_world(POP.pop_lid(i, "essay"), finish=True) for i in range(1, 40)) if not x["degenerate"])
        txt = POP.world_log(w, True)
        lines = txt.split("\n")
        assert lines[0].startswith("task:") and "goal:" in txt and "log:" in txt
        ev_lines = [LF.parse_line(x) for x in lines[lines.index("log:") + 1:]]
        assert all(e is not None for e in ev_lines)
        assert ev_lines[-1]["stop"] or len(ev_lines) == len(w["trajectory"]["steps"])
        ev = POP.evidence_at(w, w["cut"], {"unit_ref": "u", "condition_ref": "c"})
        head_cap = LF.header_from_evidence(ev)
        c = w["state"]["external_context"]
        head_con = LF.header(w["doc"]["topic"], c["audience"], c["tools"], c["deadline"], w["doc"]["sections"])
        assert head_cap == head_con, (head_cap, head_con)

    def t4():
        cond = E.build_condition(C.ALL["G01"]["condition"], "u", "G01")
        n = 0
        for i in range(1, 30):
            w = PU.make_pu_world(f"S8T|essay|s0|w{i:05d}|pilot", "essay")
            if w["degenerate"]:
                continue
            ev = E.evidence_for(w, cond)
            assert not PU.leak_check(ev, w), PU.leak_check(ev, w)
            assert not validate_visible_evidence(ev), validate_visible_evidence(ev)
            c5 = copy.deepcopy(ev)
            c5["brief"]["required_sections"] = list(w["state"]["external_context"]["brief_sections"])
            assert PU.leak_check(c5, w)
            c6 = copy.deepcopy(ev)
            c6["query"]["answer_hint"] = w["hidden"]["next_action"]
            assert validate_visible_evidence(c6)
            n += 1
            if n >= 5:
                break
        assert n >= 3

    def t5():
        assert PU._selftest() == [], PU._selftest()

    def t6():
        assert MS._selftest() == [], MS._selftest()
        assert G._selftest() == [], G._selftest()

    def t7():
        assert POP._selftest() == [], POP._selftest()

    def t8():
        dom = E.fit_dom_pop(6)
        write_registry("DOM_FROZEN", dom)
        t = POP.tail_threshold(dom, 4)
        assert isinstance(t["tau"], float) and t["n_events"] > 0
        w = POP.sample_world(POP.pop_lid(5, "essay"), finish=True)
        if not w["degenerate"]:
            m = POP.marginal_log_likelihood(w)
            assert m["total"] is not None and m["total"] <= 0 and m["per_event"] <= 0
        assert "TAIL_THRESHOLDS" in S8M.S7M.REGISTRIES

    def t9():
        write_registry("POP_CORPUS", {"fake": {"lineages": [POP.pop_lid(1, "essay")]}})
        from soundingline.stage8 import Lineages8
        L = Lineages8()
        L.rows[POP.pop_lid(1, "essay")] = {"id": POP.pop_lid(1, "essay"), "split": "discovery"}
        L.rows["WP|essay|s0|w00001|discovery"] = {"id": "WP|essay|s0|w00001|discovery", "split": "discovery"}
        L.save()
        rec = M.split_receipt()
        assert not rec["clean"] and rec["overlap"], rec
        write_registry("POP_CORPUS", {"fake": {"lineages": [POP.pop_lid(900, "essay")]}})     # the ledger is append-only: move the training side instead
        assert M.split_receipt()["clean"]

    def t10():
        frontier_charge("T", "m", 1000, 1000, 0, 0.1, 0.4)
        try:
            frontier_charge("T", "m", 1, 200_000_000, 0, 0.1, 0.4, projected=True)
            raise AssertionError("the cap did not raise")
        except FrontierCap:
            pass
        assert (read_registry("FRONTIER_LEDGER") or {}).get("total_usd", 0) < 0.01

    def t11():
        d = scratch / "ad"
        d.mkdir(exist_ok=True)
        (d / "a.bin").write_bytes(b"abc")
        h1 = adapter_hash(d)
        (d / "a.bin").write_bytes(b"abd")
        assert adapter_hash(d) != h1

    def t12():
        from runners.stage8.cardrun import CardRun8
        c = RunContract8.load() or RunContract8.create()
        c.start()
        S._workload_lock(c, {"unit|FM": 1.0})
        run = CardRun8("E02", require_lock=False)
        E.run_E02(run)
        w = next(x for x in (PU.make_pu_world(f"S8T|essay|s0|w{i:05d}|pilot", "essay") for i in range(1, 40)) if not x["degenerate"] and x["hidden"]["next_action"] is not None)
        cond = E.build_condition(C.ALL["G02"]["condition"], "u", "G02")
        ev = E.evidence_for(w, cond)
        b = E.bundle_for(w, cond, ev)
        from soundingline.stage7 import validate_prediction
        with E.ModelServer("s8_test", ["adapter:fm_qwen"]) as server:
            for arm, extra, pe in (("FM", {}, False), ("FMP", {"propose": True, "purpose_candidates": PU.purpose_candidates()}, False), ("GEN", {}, False), ("FM", {}, True)):
                cond2 = dict(cond, per_event=pe)
                ev2 = E.evidence_for(w, cond2)
                b2 = E.bundle_for(w, cond2, ev2)
                task = {"arm": arm, "model": "adapter:fm_qwen", "seed": 1, "withheld": [], **extra}
                if pe:
                    task["per_event"] = True
                cap = RT.materialize("TEST", f"{arm}{'pe' if pe else ''}", ev2, task, read_registry("DOM_FROZEN"))
                res = RT.run_capsule(cap, server.endpoint, server.token, "adapter:fm_qwen", timeout_s=300)
                pred = res.get("prediction")
                assert pred, (arm, res.get("error"), res.get("stderr_tail"))
                assert not validate_prediction(pred), validate_prediction(pred)
                if pe:
                    sc = E.score_per_event(pred, b2)
                    assert sc["n_valid"] == sc["n_events"] > 0, sc
                if arm == "FMP":
                    assert "purpose" in pred["targets"] and abs(sum(pred["targets"]["purpose"].values()) - 1) < 1e-6
                if arm == "GEN":
                    assert pred["notes"]["generated"]["events"], pred["notes"]
                RT.cleanup_unit(cap)

    def t13():
        pr = RT.probe("TEST", "http://127.0.0.1:1", "x", [str(REPO / "soundingline" / "stage8.py"), str(scratch / "adapters"), str(scratch / "POP_CORPUS.json")], other_port=RT.free_port())
        assert pr["all_raised"], pr

    def t14():
        from runners.stage8.cardrun import CardRun8
        run = CardRun8("I04", require_lock=False)
        E.run_I04(run)
        v = json.loads((scratch / "I04" / "verdict.json").read_text(encoding="utf-8"))
        assert v["outcome"] == "INFRASTRUCTURE", v.get("reason")

    def t15():
        m = Manifest8()
        for k in ("E03", "D01", "G01"):
            m.cells[k]["budget_charged_min"] = 30.0
            m.cells[k]["exec_state"] = "COMPLETE"
        m.save()
        c = RunContract8.load()
        wl = S.relock(c, m)
        assert wl["relocked"] and wl["actual_card_hours"]["E03"] == 0.5
        assert (read_registry("RELOCK") or {}).get("ladder")

    def t16():
        m = Manifest8()
        assert m.cells["B03"]["depends_on"] == ["B04", "X12"] and m.cells["X12"]["depends_on"] == ["B04"]
        assert C.LATE_CELLS == ("B04", "X12", "B03")

    def t17():
        from runners.stage8 import report as REP
        try:
            REP.write_final_packet()
            raise AssertionError("the reporter wrote before closure")
        except REP.PacketGuard:
            pass

    def t18():
        record_interrupt("test_interrupt", "a test", blocks=["G01", "G02"])
        m = Manifest8()
        m.cells["G01"]["depends_on"] = []
        m.cells["G01"]["exec_state"] = "PLANNED"
        m.cells["E03"]["depends_on"] = []
        m.cells["E03"]["exec_state"] = "PLANNED"
        m.save()
        assert S._admissible(m, "G01") is False and m.cells["G01"]["exec_state"] == "BLOCKED"
        assert S._admissible(m, "E03") is True
        write_registry("INTERRUPTS", {"interrupts": []})

    def t19():
        from runners.stage8.testbed import clones as CL
        assert not str(CL.REFERENCE.resolve()).lower().startswith(str(REPO.resolve()).lower())
        assert not any(str(CL.REFERENCE).lower() in (p or "").lower() for p in sys.path)

    def t20():
        from runners.stage8.testbed import loaders as L
        fx = L.fixtures_pass()
        assert all(v.get("pass") is not False for v in fx.values()), fx

    def t21():
        from runners.stage8.cardrun import CardRun8
        run = CardRun8("I08", require_lock=False)
        E.run_I08(run)
        key = read_registry("KEYSTONE_LOCK")
        assert key and "checks" in key and key["signed"] == all(key["checks"].values())

    def t22():
        E.register_laws2()
        w = next((x for x in (__import__("runners.stage7.constructor.worlds", fromlist=["x"]).make_world(f"S8T|essay|s0|w{i:05d}|pilot", "essay", law_name="editor2") for i in range(1, 30)) if not x["degenerate"]), None)
        assert w is not None and w["state"]["names"]["law"] == "editor2"

    for name, fn in [("1 dispatch and produces", t1), ("2 coverage and identities", t2), ("3 grammar round trip", t3), ("4 purpose leak canaries", t4),
                     ("5 purpose equivalence", t5), ("6 series and gradient", t6), ("7 feasibility", t7), ("8 marginal and tau", t8), ("9 split receipt", t9),
                     ("10 frontier cap", t10), ("11 adapter hash", t11), ("12 FM readout through the capsule", t12), ("13 capsule probe", t13),
                     ("14 mutation identity", t14), ("15 relock from charges", t15), ("16 closure order", t16), ("17 reporter refuses", t17),
                     ("18 interrupt blocks", t18), ("19 sealed reference", t19), ("20 loader fixtures", t20), ("21 keystone auto-sign", t21), ("22 second law family", t22)]:
        check(name, fn)
    print(f"\n{22 - len(fails)}/22 passed")
    if fails:
        print("FAILURES:")
        for f in fails:
            print(" -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
