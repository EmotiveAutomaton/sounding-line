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
        for i in range(200):
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

    print(f"\n{len(fails)} failures")
    for f in fails:
        print("  -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
