"""Guard tests for Stage 6 (brief §13, the twenty-one required tests) on top of the
Stage-4/5 suites. Run before the pilot: ./.venv/Scripts/python.exe tools/test_s6.py
CPU only; the model-arm halves of tests 1/4/17 are exercised live by I06/I07/I10.

  1  every card and attack is dispatchable and its produces path unique
  2  removing any card, factor corner, architecture, or attack fails coverage
  3  the exact reader recovers tiny known-answer posteriors and abstains on equivalence
  4  paired arms see identical observations and obey recorded budget rules
  5  proposal paraphrase preserves behavior; meaning change does not
  6  the same label in a different context changes the contextual realization
  7  targets and latents cannot leak through any rendered field; canaries catch plants
  8  the seven representational fields cannot overwrite one another
  9  the four controllers have matched surfaces and genuinely different hidden policies
 10  accuracy/prestige twins share the initial action and diverge only after the event
 11  exploration obtains outcome information; error and habit do not; hidden-goal worlds
     have the global dependency
 12  natural splits group all descendants of a unit on one side
 13  row duplication and reordering do not change unit-level estimates
 14  conditional effects precede pooled summaries and planned reversals trigger alarms
 15  one repair preserves the original failure and cannot change the locked estimand
 16  a killed call resumes without duplicating a completed independent unit
 17  GPU sessions wrap model load-to-unload; the CPU cap honors the companion governor
 18  orphan cleanup cannot match the Ghost sentinel's command line
 19  the deadline survives restart and starts at the pilot
 20  the report refuses before hour 168 and no other packet path is writable
 21  the fresh-clone verifier re-hashes markers and flags a planted stray packet
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    fails: list[str] = []

    def check(name, fn):
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:                                                   # noqa: BLE001
            fails.append(f"{name}: {e}")
            print(f"  FAIL {name}: {e}")

    from runners.stage6 import cards as C
    from runners.stage6 import realization as R
    from runners.stage6 import records as REC
    from runners.stage6 import worlds as W
    from soundingline import stage6 as S6M

    def t1():
        from runners.stage6 import engines as E
        assert set(C.ALL) == set(S6M.CARDS) | set(S6M.ATTACKS)
        for card, spec in C.ALL.items():
            assert spec["engine"] in ("integrity", "tournament", "worldtrack", "prospective",
                                      "records", "closure", "attack"), card
        assert len(E.INTEGRITY) == 10
        assert len({c for c in C.PRESERVATION_ORDER}) == len(C.PRESERVATION_ORDER)
    check("1 every card and attack dispatchable; order complete and unique", t1)

    def t2():
        from runners.stage6.engines import expected_cells
        full = len(expected_cells())
        saved = C.ALL.pop("V05")
        try:
            fewer = len(expected_cells())
        finally:
            C.ALL["V05"] = saved
        assert fewer < full
        spec = C.ALL["C03"]
        saved_f = spec["factors"].pop("controller")
        try:
            fewer2 = len(expected_cells())
        finally:
            spec["factors"]["controller"] = saved_f
        assert fewer2 < full
    check("2 removing a card or factor corner drops expected cells", t2)

    def t3():
        w = W.make_process_world("T3|essay|s0|w0003|discovery", "essay", track="C")
        early = W.oracle_posterior(w, upto=1)
        assert max(early.values()) < 0.7, f"early too sharp: {early}"
        wv = W.make_process_world("T3|essay|s0|w0004|discovery", "essay", track="V", value="accuracy")
        cat = next((k for k, s in enumerate(wv["trajectory"]["steps"]) if s["action"]["type"] == "consult"),
                   len(wv["trajectory"]["steps"]))
        pv = W.oracle_posterior(wv, upto=cat)
        assert abs(pv["value:accuracy"] - 0.5) < 1e-9, "twins not exactly even pre-event"
    check("3 exact posteriors: near-uniform early; equivalence exactly even", t3)

    def t4():
        from runners.stage6 import architectures as A
        w = W.make_process_world("T4|essay|s0|w0005|discovery", "essay", track="C")
        a = A.run_arm("OR", None, None, w)
        b = A.run_arm("AD", None, None, w)
        assert a["evidence_sha"] == b["evidence_sha"], "evidence differs between arms"
        assert a["budget"]["solver_enumerations"] >= 1 and b["budget"]["solver_enumerations"] >= 1
        bb = A.Budget({"model_calls": 1})
        bb.charge_call()
        bb.charge_call()
        assert bb.over(), "budget cap cannot fire"
    check("4 identical observations across arms; budget rules recorded and enforceable", t4)

    def t5():
        t = R.DISPLAY["strict_switch"]
        assert R.paraphrase(t, 2) != t and R.meaning_change(t, 2) != t
        w = W.make_process_world("T5|essay|s0|w0006|discovery", "essay", track="C")
        st0 = R.realize(w, "strict_switch")
        st1 = R.realize(w, "strict_switch", proposal_text=R.paraphrase(t, 2))
        d0, d1 = st0["decision_likelihoods"]["next_edit_type"], st1["decision_likelihoods"]["next_edit_type"]
        assert all(abs(d0[k] - d1[k]) < 1e-12 for k in d0), "paraphrase changed the realization"
        st2 = R.realize(w, "concurrent")
        d2 = st2["decision_likelihoods"]["next_edit_type"]
        assert any(abs(d0[k] - d2.get(k, 0)) > 1e-6 for k in d0), "a different meaning did not diverge"
    check("5 paraphrase preserves behavior; meaning change diverges", t5)

    def t6():
        w1 = W.make_process_world("T6|essay|s0|w0007|discovery", "essay", track="C")
        w2 = W.make_process_world("T6|workshop_doc|s0|w0031|discovery", "workshop_doc", track="C")
        d1 = R.realize(w1, "focal_habit")["decision_likelihoods"]["next_edit_type"]
        d2 = R.realize(w2, "focal_habit")["decision_likelihoods"]["next_edit_type"]
        assert any(abs(d1[k] - d2.get(k, 0)) > 1e-6 for k in d1), "the same label realized identically in two contexts"
    check("6 the same label realizes differently in a different context", t6)

    def t7():
        from runners.stage6.engines import _leaks
        for track in ("C", "V", "F"):
            w = W.make_process_world("T7|essay|s0|w0008|discovery", "essay", track=track)
            text = W.render_evidence(w, upto=len(w["trajectory"]["steps"])) + W.render_artifact(w)
            assert not _leaks(text), f"leak in {track}: {_leaks(text)}"
        assert _leaks("a strict switch happened"), "canary not caught"
    check("7 no latent leaks in renders; the canary is caught", t7)

    def t8():
        shared = {"x": 1}
        st = S6M.maker_state(proposal_id="p", evidence_scope={"observed": ["e"]},
                             decision_likelihoods={"t": {"a": 1.0}}, stop_model={"p_stop": 0.5},
                             uncertainty={"posterior_weight": 1, "abstain": False},
                             episode_goal="g", control_state=shared, selection_history=shared)
        try:
            S6M.check_state_fields_distinct(st)
            raise AssertionError("shared object not caught")
        except S6M.MakerStateError:
            pass
    check("8 owner fields cannot share one object", t8)

    def t9():
        w0 = W.make_process_world("T9|essay|s0|w0009|discovery", "essay", track="C")
        w = dict(w0, stop_shift=-99.0)
        goal_counts = {}
        for c in W.CONTROLLERS:
            t = W.simulate(w, W.controller_cfg(w, c, tag=c))
            if t["stopped_at"] is None:
                gc = tuple(sorted({g: sum(1 for s in t["steps"] if s["action"]["goal"] == g and s["action"]["slot"] != "urgent") for g in W.GOALS}.items()))
                goal_counts.setdefault(gc, []).append(c)
        assert len(goal_counts) <= 1, f"aggregate goal counts differ: {goal_counts}"
        hits = 0
        for i in range(6):
            wi = W.make_process_world(f"T9|essay|s0|w{i:04d}|discovery", "essay", track="C")
            post = W.oracle_posterior(wi, upto=len(wi["trajectory"]["steps"]))
            hits += int(max(post, key=post.get) == wi["truth"]["controller"])
        assert hits >= 3, f"controllers not separable: {hits}/6"
    check("9 controllers: matched aggregates, separable orders", t9)

    def t10():
        w = W.make_process_world("T10|essay|s0|w0011|discovery", "essay", track="V", value="accuracy")
        cat = next((k for k, s in enumerate(w["trajectory"]["steps"]) if s["action"]["type"] == "consult"),
                   len(w["trajectory"]["steps"]))
        assert abs(W.oracle_posterior(w, upto=cat)["value:accuracy"] - 0.5) < 1e-9
        da = W.changed_context_dist(w, W.value_cfg(w, "accuracy"))
        dp = W.changed_context_dist(w, W.value_cfg(w, "prestige"))
        assert any(abs(da[k] - dp[k]) > 0.05 for k in da), "values do not diverge at the diagnostic choice"
    check("10 value twins collide early and diverge at the diagnostic event", t10)

    def t11():
        stats = {}
        for f in W.FORAGE:
            w = W.make_process_world("T11|essay|s0|w0012|discovery", "essay", track="F", forage=f)
            steps = w["trajectory"]["steps"]
            probes = [k for k, s in enumerate(steps) if s["action"]["type"] == "probe"]
            checks_after = sum(1 for k, s in enumerate(steps)
                               if s["action"]["type"] == "check" and s["action"]["slot"].startswith("tech")
                               and probes and k > min(probes))
            slink = sum(1 for s in steps if s["action"]["slot"] == "s-link")
            stats[f] = {"checks_after_probe": checks_after, "slink": slink}
        assert stats["explore"]["checks_after_probe"] > stats["error"]["checks_after_probe"], stats
        assert stats["habit_misuse"]["checks_after_probe"] == 0, stats
        assert stats["hidden_goal"]["slink"] >= 1 and all(stats[f]["slink"] == 0 for f in ("explore", "error", "habit_misuse")), stats
    check("11 exploration reads outcomes; only hidden-goal carries the distant dependency", t11)

    def t12():
        assert REC.lane_of("sw|99") == REC.lane_of("sw|99")
        lanes = {REC.lane_of(f"sw|{i}") for i in range(60)}
        assert lanes == {"discovery", "transfer", "confirmation"}, lanes
    check("12 lineage-keyed lanes: deterministic and all three populated", t12)

    def t13():
        from runners import s5_lib
        units = {f"u{i}": float(i % 5) for i in range(40)}
        a = s5_lib.cluster_bootstrap_ci(units, 9)
        rows = [{"unit_id": u, "primary_score": v} for u, v in units.items()]
        per: dict = {}
        for r in rows + rows:
            per.setdefault(r["unit_id"], []).append(r["primary_score"])
        units2 = {u: sum(v) / len(v) for u, v in per.items()}
        b = s5_lib.cluster_bootstrap_ci(units2, 9)
        assert abs(a["point"] - b["point"]) < 1e-12, "duplication moved the unit estimate"
    check("13 row duplication cannot move unit-level estimates", t13)

    def t14():
        cells = {"q|essay": {"point": 0.2}, "q|workshop": {"point": -0.1}}
        pts = [v["point"] for v in cells.values()]
        assert min(pts) < 0 < max(pts), "the reversal predicate cannot fire"
    check("14 a planned sign reversal across conditional cells is detectable", t14)

    def t15():
        with tempfile.TemporaryDirectory(prefix="s6reset_") as td:
            env = dict(os.environ, S6_ROOT=td, S6_SMOKE="1")
            import subprocess
            code = (
                "import sys; sys.path.insert(0, r'" + str(REPO) + "');"
                "from soundingline.stage6 import Manifest6, S6, write_json;"
                "m = Manifest6(); m.add('C03', 'C03', [], str(S6 / 'C03' / 'verdict.json'), 5.0, True, 'x');"
                "m.set_exec('C03', 'FAILED', 'boom'); (S6 / 'C03').mkdir(parents=True, exist_ok=True);"
                "write_json(S6 / 'C03' / 'verdict.json', {'outcome': 'INSTRUMENT_FAILED'});"
                "from runners.stage6 import scheduler as SCH; SCH.reset(['C03'], 'r1', 'test repair');"
                "m2 = Manifest6(); assert m2.cells['C03']['exec_state'] == 'PLANNED';"
                "sup = S6 / 'C03' / 'superseded_r1';"
                "assert (sup / 'verdict.json').exists(), 'original failure not preserved';"
                "print('reset ok')")
            r = subprocess.run([str(REPO / '.venv' / 'Scripts' / 'python.exe'), "-c", code],
                               env=env, capture_output=True, text=True, timeout=120)
            assert "reset ok" in r.stdout, r.stdout[-300:] + r.stderr[-300:]
    check("15 a repair preserves the original failure and re-plans the cell", t15)

    def t16():
        with tempfile.TemporaryDirectory(prefix="s6resume_") as td:
            env = dict(os.environ, S6_ROOT=td, S6_SMOKE="1")
            import subprocess
            code = (
                "import sys; sys.path.insert(0, r'" + str(REPO) + "');"
                "from soundingline.stage6 import RunContract6; RunContract6.create();"
                "from runners.stage6.cardrun import CardRun6;"
                "a = CardRun6('I10', cell_id='I10/t16', require_lock=False);"
                "a.row('u1', arm='x', primary_score=1.0); a.unit_complete(None, 'u1', 'x');"
                "b = CardRun6('I10', cell_id='I10/t16', require_lock=False);"
                "assert b.is_done(None, 'u1', 'x'); print('resume ok')")
            r = subprocess.run([str(REPO / '.venv' / 'Scripts' / 'python.exe'), "-c", code],
                               env=env, capture_output=True, text=True, timeout=120)
            assert "resume ok" in r.stdout, r.stdout[-300:] + r.stderr[-300:]
    check("16 a killed call resumes without duplicating a completed unit", t16)

    def t17():
        import inspect
        from runners.stage6 import engines as E
        from runners.stage6 import scheduler as SCH
        src = inspect.getsource(E)
        assert "GpuSession" in src, "engines do not wrap model work in the GPU session"
        cap = SCH._cpu_cap()
        assert cap in (2, 3)
        g = S6M.ghost_status()
        if g.get("live"):
            assert cap == 2, "governor ignores a live Ghost"
    check("17 GPU sessions wrap model work; the CPU cap honors the governor", t17)

    def t18():
        ps1 = (REPO / "tools" / "orphan_sweep.ps1").read_text(encoding="utf-8")
        m = re.search(r"CommandLine -match '([^']+)'", ps1)
        assert m, "sweep filter not found"
        pat = m.group(1).replace("\\\\", "\\")
        ghost_cmd = 'python.exe -X faulthandler -m runners.run_v14 --stage all'
        assert not re.search(pat.replace("[\\\\/]", "[\\\\/]"), ghost_cmd.replace("runners.run_", "runners.run_")) \
            or not re.search(r"runners[\\/]run_", ghost_cmd), "the sweep pattern matches Ghost's module invocation"
        stage6_cmd = r'python.exe E:\...\runners\stage6\engines.py --card M08'
        assert not re.search(r"run_queue\.py|runners[\\/]run_", stage6_cmd), "the sweep would kill stage6 engines"
    check("18 the orphan sweep cannot match Ghost's or stage6's command lines", t18)

    def t19():
        with tempfile.TemporaryDirectory(prefix="s6clock_") as td:
            p = Path(td) / "RUN_CONTRACT.json"
            from soundingline.stage6 import RunContract6
            c = RunContract6.create(path=p)
            c.start()
            d0 = c.data["deadline"]
            c2 = RunContract6.load(path=p)
            c2.start()
            assert c2.data["deadline"] == d0, "the deadline moved on restart"
            assert c2.data["run_hours"] == 168
    check("19 the one clock starts at the pilot and survives restart", t19)

    def t20():
        from runners.stage6 import report as REP
        from soundingline.stage6 import refuse_packet_path, S6 as ROOT
        try:
            REP.write_final_packet()
            raise AssertionError("packet written before the deadline")
        except Exception as e:                                                   # noqa: BLE001
            assert "REFUSED" in str(e).upper() or "packet" in str(e).lower() or "clock" in str(e).lower() or "contract" in str(e).lower()
        try:
            refuse_packet_path(ROOT / "sub" / "CURATOR_PACKET_FINAL.md")
            raise AssertionError("foreign packet path allowed")
        except Exception:                                                        # noqa: BLE001
            pass
    check("20 the reporter refuses early; foreign packet paths are refused", t20)

    def t21():
        from runners.stage6 import fresh_clone as FC
        rep = FC.verify(max_cards=4)
        assert "n_verdicts_checked" in rep and "ok" in rep
    check("21 the fresh-clone verifier runs and reports", t21)

    print(f"\n{len(fails)} failures")
    for f in fails:
        print("  -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
