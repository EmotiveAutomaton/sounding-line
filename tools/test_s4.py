"""Guard tests for Stage 4 (brief §9.3, the eleven verification requirements).
Run before the Stage-4 pilot: ./.venv/Scripts/python.exe tools/test_s4.py
CPU only; the intervention fixtures use pythia-410m in float32.

  1  parser fixtures: negation, quotation, ambiguity, malformed output, label permutations
  2  expected-cell validation fails when a corner, domain, or control is removed
  3  sample validation fails when duplicate lineages masquerade as independent units
  4  split validation fails when a derived item crosses splits or an inspected source
     is labeled fresh
  5  aggregation is invariant to row order and weights every eligible reader equally
  6  ground-truth validation rejects an assigned instruction offered as a realized choice
  7  a downstream gate inspects the prerequisite VERDICT, not its path
  8  exact-collision fixture: identical inputs with balanced hidden labels cannot be told
     apart by a classifier
  9  intervention: alpha=0 is a no-op, positions before the steered span are untouched,
     hooks are removed, a second full pass replays identically
 10  duration accounting: the deadline persists across a reload; a short run cannot be
     labeled complete; lost time is recorded
 11  reporting guards: no packet before the deadline; interim packets refused
 12  stratum balancing cancels a main effect under unbalanced signs
 13  construction known answers
 14  the pilot writes under its manifest produce path
 15  (R7) the lesson space is enumerated per domain: every allocatable world distinct,
     no cross-split or cross-domain twin, over-allocation raises, latent knowledge
     outside the identity
 16  (R7) two lineage writers holding stale snapshots lose nothing: the ledger is a
     lock-held reload-modify-write
 17  (R7) the scheduler's reset op preserves the first attempt and re-plans the cell
 18  (R7) rows carry their construction hash and intervals cluster on it
"""

from __future__ import annotations

import json
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soundingline import s4                                                       # noqa: E402
from runners import s4_lib                                                        # noqa: E402

MODEL = "EleutherAI/pythia-410m"


def main() -> int:
    fails: list[str] = []

    def check(name, fn):
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:                                                   # noqa: BLE001
            fails.append(f"{name}: {e}")
            print(f"  FAIL {name}: {e}")

    tmp = Path(tempfile.mkdtemp(prefix="s4test_"))

    # 1 parser
    check("1 parser fixtures", lambda: (_ for _ in ()).throw(AssertionError(
        s4_lib.run_parser_fixtures())) if s4_lib.run_parser_fixtures() else None)

    # 2 expected cells
    def t2():
        spec = {"C01": {"factors": {"condition": ["none", "bundle", "facts"]},
                        "domains": ["workshop", "civic"], "n_units": 4,
                        "controls": ["irrelevant"]}}
        full = s4.expand_expected_cells(spec)
        assert s4.validate_expected(spec, full) == []
        drop_corner = [c for c in full if not (c["factors"].get("condition") == "facts"
                                                and c["factors"]["domain"] == "civic")]
        assert len(s4.validate_expected(spec, drop_corner)) == 1
        drop_domain = [c for c in full if c["factors"]["domain"] != "civic"]
        assert len(s4.validate_expected(spec, drop_domain)) == 4
        drop_control = [c for c in full if "control" not in c["factors"]]
        assert len(s4.validate_expected(spec, drop_control)) == 2
    check("2 expected-cell validation", t2)

    # 3 duplicate lineages
    def t3():
        L = s4.Lineages(tmp / "lin.json")
        ids = L.allocate("C01", "workshop", [0, 1, 2], 3, "discovery")
        L.mark_generated(ids[0], "hash-a")
        L.mark_generated(ids[1], "hash-a")
        L.mark_generated(ids[2], "hash-b")
        assert L.duplicate_content() == [(ids[0], ids[1])]
    check("3 duplicate-lineage detection", t3)

    # 4 split validation and freshness
    def t4():
        L = s4.Lineages(tmp / "lin2.json")
        d = L.allocate("T01", "civic", [0], 1, "discovery")[0]
        c = L.allocate("T01", "civic", [0], 1, "confirmation", world_offset=500)[0]
        child = L.derive(d, "hop1")
        assert L.rows[child]["split"] == "discovery"
        raised = False
        try:
            L.check_same_split(child, c)
        except s4.SplitViolation:
            raised = True
        assert raised, "cross-split join not caught"
        L.check_fresh([c])                       # clean confirmation lineage is fresh
        L.mark_inspected([c])
        raised = False
        try:
            L.check_fresh([c])
        except s4.FreshnessViolation:
            raised = True
        assert raised, "inspected lineage passed as fresh"
        raised = False
        try:
            L.check_fresh([d])
        except s4.FreshnessViolation:
            raised = True
        assert raised, "discovery lineage passed as fresh"
    check("4 split and freshness validation", t4)

    # 5 aggregation invariance and equal weighting
    def t5():
        rows = [{"unit": "w1", "fam": "q", "v": 0.0}, {"unit": "w1", "fam": "q", "v": 1.0},
                {"unit": "w2", "fam": "q", "v": 0.5}, {"unit": "w1", "fam": "q", "v": 0.2}]
        a = s4.aggregate_equal(rows, "unit", "fam", "v")
        b = s4.aggregate_equal(list(reversed(rows)), "unit", "fam", "v")
        rng = random.Random(3)
        sh = rows[:]
        rng.shuffle(sh)
        c = s4.aggregate_equal(sh, "unit", "fam", "v")
        assert a == b == c
        # the overwrite semantics would give w1 = 0.2 (last) or 0.0 (first); equal gives 0.4
        assert abs(a["q"]["mean"] - (0.4 + 0.5) / 2) < 1e-9
    check("5 aggregation order-invariance", t5)

    # 6 ground truth must be realized
    def t6():
        raised = False
        try:
            s4.require_realized_truth({"unit_id": "u", "truth_provenance": "assigned_instruction"})
        except s4.RealizationError:
            raised = True
        assert raised
        s4.require_realized_truth({"unit_id": "u", "truth_provenance": "realized_draw"})
    check("6 assigned-is-not-realized", t6)

    # 7 gate reads the verdict content
    def t7():
        p = tmp / "gate.json"
        p.write_text(json.dumps({"gate_pass": False, "verdict": "INSTRUMENT-FAILED"}),
                     encoding="utf-8")
        assert s4.verdict_gate(p) is False
        p.write_text(json.dumps({"gate_pass": True}), encoding="utf-8")
        assert s4.verdict_gate(p) is True
        assert s4.verdict_gate(tmp / "absent.json") is False
    check("7 gate inspects verdict", t7)

    # 8 exact-collision leakage fixture
    def t8():
        X = [[0.3, 0.7, 0.1]] * 40
        y = [0, 1] * 20
        acc = s4_lib.collision_leak_check(X, y, seed=1)
        assert acc <= 0.6, acc
        X2 = [[0.0, 0.0, 0.0] if lab == 0 else [1.0, 1.0, 1.0] for lab in y]
        assert s4_lib.collision_leak_check(X2, y, seed=1) > 0.9
    check("8 collision fixture", t8)

    # 9 intervention on a tiny fixture
    def t9():
        import torch                                                              # noqa: PLC0415
        from soundingline.probe.conditional_reader import load_reader             # noqa: PLC0415
        from soundingline.probe.interventions import get_blocks                   # noqa: PLC0415
        model, tok = load_reader(MODEL, device="cpu", dtype="float32")
        text = "The keeper climbed the stairs and checked the lamp before dusk."
        ids = tok(text, return_tensors="pt").input_ids
        d = torch.randn(model.config.hidden_size)
        d = d / d.norm()
        blocks = get_blocks(model)
        b = len(blocks) // 2
        with torch.no_grad():
            base = model(ids, output_hidden_states=True)
        with s4_lib.steer_positions(model, [b], d, 0.0, 3, ids.shape[1]):
            with torch.no_grad():
                zero = model(ids, output_hidden_states=True)
        assert torch.equal(base.logits, zero.logits), "alpha=0 changed the output"
        with s4_lib.steer_positions(model, [b], d, 4.0, 3, ids.shape[1]):
            assert s4_lib.hooks_present(model) == 1
            with torch.no_grad():
                st = model(ids, output_hidden_states=True)
            with torch.no_grad():
                st2 = model(ids, output_hidden_states=True)
        assert s4_lib.hooks_present(model) == 0, "hook not removed"
        # the library's own recorder captures block b's output before our hook rewrites
        # it, so the steered value is visible from the NEXT block's output onward
        hb, hs = base.hidden_states[b + 2][0], st.hidden_states[b + 2][0]
        assert torch.allclose(hb[:3], hs[:3]), "positions before the span moved"
        assert not torch.allclose(hb[3:], hs[3:]), "steered span did not move"
        assert not torch.equal(base.logits, st.logits), "steering left the logits unchanged"
        assert torch.equal(st.logits, st2.logits), "replay differs"
        with torch.no_grad():
            after = model(ids, output_hidden_states=True)
        assert torch.equal(base.logits, after.logits), "baseline not restored"
        lab = s4_lib.label_token_ids(tok)
        assert all(v["id"] is not None for v in lab.values()), lab
    check("9 intervention fixture", t9)

    # 10 duration accounting
    def t10():
        p = tmp / "contract.json"
        c = s4.RunContract.create(path=p)
        c.start()
        d1 = c.data["deadline_epoch"]
        c2 = s4.RunContract.load(p)
        c2.start()
        assert c2.data["deadline_epoch"] == d1, "restart reset the deadline"
        assert 0 <= c2.elapsed_h() < 0.01 and c2.remaining_h() > 23.9
        raised = False
        try:
            s4.validate_run_label(c2, "COMPLETE_24H")
        except s4.ContractError:
            raised = True
        assert raised
        c2.record_lost_time("test", 120.0)
        assert s4.RunContract.load(p).data["lost_time"][0]["seconds"] == 120.0
        h = c2.hash()
        c2.freeze("primary_contrasts", {"C01": "bundle_vs_facts"})
        assert c2.hash() != h
        raised = False
        try:
            c2.freeze("primary_contrasts", {"C01": "changed"})
        except s4.ContractError:
            raised = True
        assert raised, "a frozen section was silently changed"
    check("10 duration accounting and freezing", t10)

    # 11 reporting guards (a run-until-empty contract, the default since his 2026-08-28
    # ruling, admits the packet only on recorded exhaustion; a windowed contract also at
    # its deadline)
    def t11():
        p = tmp / "contract2.json"
        c = s4.RunContract.create(path=p)
        c.start()
        raised = False
        try:
            s4.write_packet("x", c, exhausted=False, path=tmp / "packet.md")
        except s4.PacketGuard:
            raised = True
        assert raised, "packet written before exhaustion"
        raised = False
        try:
            s4.refuse_interim_packet("daily")
        except s4.PacketGuard:
            raised = True
        assert raised
        c.data["deadline_epoch"] = 0
        assert not c.deadline_passed(), "a run-until-empty contract stopped at its deadline"
        raised = False
        try:
            s4.write_packet("x", c, exhausted=False, path=tmp / "packet.md")
        except s4.PacketGuard:
            raised = True
        assert raised, "an elapsed window licensed the packet under run-until-empty"
        assert s4.write_packet("x", c, exhausted=True, path=tmp / "packet.md").exists()
        c.data["stop_at_deadline"] = True
        assert c.deadline_passed(), "a windowed contract did not stop at its deadline"
        assert not c.closure_due(), "closure fired before the closure hour"
        assert s4.write_packet("x", c, exhausted=False, path=tmp / "packet2.md").exists()
        s4.validate_run_label(c, "RUN_TO_EMPTY")
    check("11 reporting guards", t11)

    # 12 stratum balancing cancels a main effect under unbalanced appraisal signs
    def t12():
        # a pure main effect of steering: delta 0.3 for every unit; aligned = sign x delta
        vals = {f"p{i}": 0.3 for i in range(6)} | {f"n{i}": -0.3 for i in range(3)}
        strat = {u: u.startswith("n") for u in vals}
        raw = sum(vals.values()) / len(vals)
        bal = s4_lib.stratum_balanced(vals, strat)
        assert abs(raw) > 0.05 and abs(sum(bal.values()) / len(bal)) < 1e-9, (raw, bal)
        # a true interaction (delta +0.3 on positive targets, -0.3 on negative) survives
        vals2 = {f"p{i}": 0.3 for i in range(6)} | {f"n{i}": 0.3 for i in range(3)}
        bal2 = s4_lib.stratum_balanced(vals2, strat)
        assert abs(sum(bal2.values()) / len(bal2) - 0.3) < 1e-9
    check("12 stratum-balanced interaction", t12)

    # 13 constructions: exactly one correct step option, a deterministic known next
    # choice, intent realized in every lesson world, an exact history collision
    def t13():
        from runners import s4_worlds                                             # noqa: PLC0415
        two = 0
        for i in range(150):
            lid = f"T13|workshop|s0|w{i:04d}|pilot"
            w = s4_worlds.make_world(lid, "workshop")
            q = s4_worlds.step_question(w, random.Random(i))
            correct = ([o for o in q["options"] if o in w["blocked_steps"]] if "ruled out" in q["question"]
                       else [o for o in q["options"].values() if o in w["feasible_steps"]])
            assert len(correct) == 1, (lid, q)
            two += len(w["blocked_steps"]) == 2
            a = s4_worlds.make_appraisal_world(lid, "workshop")
            assert a["next_choice"]["truth"] in s4_worlds.NEXT_ACTS
            assert a["next_choice"]["truth"] == s4_worlds.make_appraisal_world(lid, "workshop")["next_choice"]["truth"]
            t = s4_worlds.make_lesson_world(lid, "workshop")
            for truth in ("true", "false"):
                b = s4_worlds.lesson_message(t, truth, "benefit", "bare")
                d = s4_worlds.lesson_message(t, truth, "induce", "bare")
                assert b["recommended"] != d["recommended"], lid
            hs = s4_worlds.make_history_world(lid, "workshop", "stable")
            hm = s4_worlds.make_history_world(lid, "workshop", "marker_removed")
            assert s4_worlds.history_record(hs, 9, False) == s4_worlds.history_record(hm, 9, False), lid
        assert two > 0, "no two-blocked world in 200: the branch is untested"
    check("13 construction known answers", t13)

    # 14 every manifest cell's produce is written by its runner: the pilot cell's path
    def t14():
        src = (Path(__file__).resolve().parents[1] / "runners" / "s4_run_i.py").read_text(encoding="utf-8")
        assert 'card_dir("I03pilot")' in src, "the pilot writes no verdict under its manifest produce path"
    check("14 pilot produce path", t14)

    # 15 the enumerated lesson space (R7)
    def t15():
        from runners import s4_worlds                                             # noqa: PLC0415
        for domain in s4_worlds.DOMAINS4:
            half = s4_worlds.lesson_identity_space(domain) // 2
            assert half >= 128, (domain, half)   # expanded discovery and confirmation both fit
            seen = {}
            for split in ("discovery", "confirmation"):
                for i in range(half):
                    w = s4_worlds.make_lesson_world(f"T01|{domain}|s{i % 3}|w{i:04d}|{split}", domain)
                    h = s4_worlds.construction_hash(w)
                    assert h not in seen, (domain, split, i, seen[h])
                    seen[h] = (split, i)
            raised = False
            try:
                s4_worlds.make_lesson_world(f"T01|{domain}|s0|w{half:04d}|discovery", domain)
            except ValueError:
                raised = True
            assert raised, "over-allocation did not raise"
        off = s4_worlds.CONFIRMATION_WORLD_OFFSET
        assert (s4_worlds.make_lesson_world(f"T01|workshop|s10|w{off + 9:04d}|confirmation", "workshop")["identity_code"]
                == s4_worlds.make_lesson_world("T01|workshop|s10|w0009|confirmation", "workshop")["identity_code"])
        a = s4_worlds.make_lesson_world("T01|workshop|s0|w0007|discovery", "workshop")
        b = s4_worlds.make_lesson_world("T01|civic|s0|w0007|discovery", "civic")
        assert s4_worlds.construction_hash(a) != s4_worlds.construction_hash(b)
        c = dict(a, knowledge="mistaken" if a["knowledge"] == "correct" else "correct")
        assert s4_worlds.construction_hash(a) == s4_worlds.construction_hash(c)
        # determinism across calls and derived ids reach the parent's world unchanged
        assert json.dumps(a) == json.dumps(s4_worlds.make_lesson_world("T01|workshop|s0|w0007|discovery", "workshop"))
    check("15 enumerated lesson space", t15)

    # 16 lineage writers with stale snapshots (the lost-update shape, R7)
    def t16():
        pth = tmp / "lin3.json"
        L1 = s4.Lineages(pth)
        L2 = s4.Lineages(pth)                       # loaded EMPTY, before any allocation
        ids = L1.allocate("C01", "civic", [0, 1, 2], 4, "discovery")
        L1.mark_inspected([ids[0]])
        L2.mark_generated(ids[1], "h-b")           # a stale writer: the old code wrote {} back
        L2.mark_inspected([ids[2]])
        L1.mark_generated(ids[3], "h-d")
        disk = s4.Lineages(pth).rows
        assert len(disk) == 4, disk.keys()
        assert disk[ids[0]]["inspected"] and disk[ids[2]]["inspected"]
        assert disk[ids[1]]["generation_hash"] == "h-b" and disk[ids[3]]["generation_hash"] == "h-d"
        assert L1.rows[ids[2]]["inspected"] and L2.rows[ids[0]]["inspected"], "caches not refreshed"
        cov = s4.Lineages(pth).generation_coverage()
        assert cov["C01|discovery"] == {"roots": 4, "hashed": 2, "distinct": 2, "duplicates": 0, "checked": False}, cov
        L1.mark_generated(ids[0], "h-a")
        L1.mark_generated(ids[2], "h-a")
        cov2 = s4.Lineages(pth).generation_coverage()["C01|discovery"]
        assert cov2["checked"] and cov2["duplicates"] == 1 and cov2["distinct"] == 3, cov2
        assert not (pth.with_name(pth.name + ".lock")).exists()
    check("16 lineage concurrent writers", t16)

    # 17 the reset op (R7)
    def t17():
        from runners import s4_scheduler                                          # noqa: PLC0415
        root = tmp / "resetroot"
        (root / "T01").mkdir(parents=True)
        (root / "T01" / "cases.jsonl").write_text('{"a": 1}\n', encoding="utf-8")
        (root / "T01" / "verdict.json").write_text('{"outcome": "SUPPORT_CANDIDATE"}', encoding="utf-8")
        (root / "T01.log").write_text("log", encoding="utf-8")
        m = s4.Manifest(root / "QUEUE_MANIFEST.json")
        m.add("T01", "T01", [], str(root / "T01" / "verdict.json"), 10, True, "why")
        m.add("T02", "T02", ["T01"], str(root / "T02" / "verdict.json"), 10, True, "why")
        m.add("T01/expand", "T01", ["T01"], str(root / "T01" / "verdict.json"), 10, True, "rung")
        m.set_exec("T01", "RUNNING")
        m.set_exec("T01", "COMPLETE")
        m.set_outcome("T01", "SUPPORT_CANDIDATE")
        m.charge("T01", 25.0, 25.0)
        s4_scheduler.reset(["T01"], "testtag", "a construction repair", root=root)
        m2 = s4.Manifest(root / "QUEUE_MANIFEST.json")
        c = m2.cells["T01"]
        assert c["exec_state"] == "PLANNED" and c["outcome"] == "NOT_RUN" and c["attempts"] == 0
        assert c["resets"][0]["before"]["outcome"] == "SUPPORT_CANDIDATE"
        assert "T01/expand" not in m2.cells and "T02" in m2.cells
        sup = root / "T01" / "superseded_testtag"
        assert (sup / "verdict.json").exists() and (sup / "cases.jsonl").exists() and (sup / "T01.log").exists()
        assert (sup / "RESET_NOTE.json").exists()
        assert not (root / "T01" / "verdict.json").exists() and not (root / "T01.log").exists()
        assert m2.deps_complete("T02") is False
    check("17 reset op", t17)

    # 18 construction hashes on rows; intervals cluster on them (R7)
    def t18():
        from runners.s4_run_common import cid, cluster_by_construction, construction_summary   # noqa: PLC0415
        rows = [{"unit_id": "u1", "primary_score": 1.0, "extra": {"construction_hash": "h1"}},
                {"unit_id": "u2", "primary_score": 0.0, "extra": {"construction_hash": "h1"}},
                {"unit_id": "u3", "primary_score": 1.0, "extra": {"construction_hash": "h2"}},
                {"unit_id": "u4", "primary_score": 1.0, "extra": {}}]
        assert [cid(r) for r in rows] == ["h1", "h1", "h2", "u4"]
        cl = cluster_by_construction(rows)
        assert {r["unit_id"] for r in cl} == {"h1", "h2", "u4"}
        summ = construction_summary(rows)
        assert summ["n_units"] == 4 and summ["n_distinct_constructions"] == 3 and not summ["checked"]
        a = s4_lib.paired_contrast(cl, [{**r, "primary_score": 0.0} for r in cl], "unit_id", "primary_score", 1)
        assert a["n_units"] == 3, a
        # twins resample as one unit: the same rows unclustered claim four
        b = s4_lib.paired_contrast(rows, [{**r, "primary_score": 0.0} for r in rows], "unit_id", "primary_score", 1)
        assert b["n_units"] == 4
    check("18 construction clustering", t18)

    print(f"\n{len(fails)} failures")
    for f in fails:
        print("  -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
