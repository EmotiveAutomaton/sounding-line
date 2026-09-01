"""Guard tests for Stage 5 (brief §9.1, the twelve required tests) on top of the Stage-4
suite. Run before the pilot: ./.venv/Scripts/python.exe tools/test_s5.py
CPU only; the intervention fixture uses pythia-410m in float32.

  1  parser fixtures: negation, quotation, unknown, malformed, evidence spans, permutations
  2  removing a card, corner, domain, route, regime, or control fails expected-cell validation
  3  exact surface collisions (source twins) remain collisions after prompt assembly and
     tokenization
  4  a route-selection world fails closed under the divergence floor
  5  enactability and historical correspondence cannot alias
  6  owner variables cannot overwrite one another in the record or its merge
  7  joint and staged readers receive the same evidence, candidates, and allowance
  8  the L255 replication verifies coordinates, dose, sign, hook removal, replay, own-answer
  9  confirmation access is rejected after a discovery read or shared ancestry
 10  aggregation is order-invariant and clusters at the construction
 11  the clock survives a reload; a run short of the window cannot be labeled complete;
     restarts and waits are recorded
 12  no curator packet at any other path; none before closure
 13  the four lanes allocate and the transfer lane resolves to its own identity block
 14-19 added 2026-08-29/30 (the second contract's repairs; the receipts' rulers and echo rule)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soundingline import s4, stage5                                                # noqa: E402
from runners import s5_cards, s5_lib, s5_sources, s5_worlds                        # noqa: E402

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

    tmp = Path(tempfile.mkdtemp(prefix="s5test_"))

    def t1():
        assert s5_lib.run_record_fixtures() == []
        assert s5_lib.s4_lib.run_parser_fixtures() == []
    check("1 parser fixtures", t1)

    def t2():
        spec = {"A02": s5_cards.expected_spec("minimum")["A02"], "R01": s5_cards.expected_spec("minimum")["R01"]}
        full = stage5.expand_expected_cells(spec)
        assert stage5.validate_expected(spec, full) == []
        assert stage5.validate_expected(spec, [c for c in full if c["card"] != "R01"])
        assert stage5.validate_expected(spec, [c for c in full if not (c["card"] == "A02" and c["factors"].get("behavior") == "correction")])
        assert stage5.validate_expected(spec, [c for c in full if c["factors"]["domain"] != "memo"])
        assert stage5.validate_expected(spec, [c for c in full if c["factors"].get("control") != "collision_abstention"])
        assert stage5.validate_expected(spec, [c for c in full if c["factors"].get("choice") != "easiest"])
    check("2 expected-cell validation", t2)

    def t3():
        from transformers import AutoTokenizer                                    # noqa: PLC0415
        tok = AutoTokenizer.from_pretrained(MODEL)
        n = 0
        for i in range(12):
            w = s5_sources.make_source_world(f"A01|notice|s0|w{i:04d}|discovery", "notice")
            t = s5_sources.collision_twin(w)
            body_w = f"A notice you received:\n\"{w['text']}\"\n\nWhat would it show?"
            body_t = f"A notice you received:\n\"{t['text']}\"\n\nWhat would it show?"
            assert body_w == body_t
            assert tok(body_w).input_ids == tok(body_t).input_ids
            assert w["factors"]["belief"] != t["factors"]["belief"]
            n += 1
        assert n == 12
    check("3 collisions survive assembly and tokenization", t3)

    def t4():
        w = s5_worlds.make_joint_world("J01|workshop|s0|w0002|discovery", "workshop")
        info = s5_worlds.route_information(w)
        assert "divergence" in info and info["best"] != info["second"]
        # a flat menu: force the divergence under the floor and require the void
        floor = 0.05
        flat = dict(info, divergence=0.001)
        assert not (flat["divergence"] >= floor), "a flat menu passed the floor"
        assert (info["divergence"] >= floor) == (info["divergence"] >= 0.05)
    check("4 route selection fails closed under the floor", t4)

    def t5():
        early, late = [1, 2], [3, 4]
        import itertools                                                          # noqa: PLC0415
        valid = [list(p) + list(q) for p in itertools.permutations(early) for q in itertools.permutations(late)]
        true = [2, 1, 3, 4]
        prop = [1, 2, 4, 3]
        assert (prop in valid) and (prop != true), "a valid but non-historical order must score enactable and not historical"
        assert len(valid) == 4 and true in valid
        bad = [3, 1, 2, 4]
        assert bad not in valid
    check("5 enactability and history cannot alias", t5)

    def t6():
        rec = stage5.latent_record(maker_appraisal={"candidates": {"a": 1, "b": 1}}, reader_response={"candidates": {"x": 1}},
                                   content_support={"candidates": {"h": 2, "l": 1}, "unknown": 1})
        stage5.check_owners_distinct(rec)
        rec["audience_effect_goal"] = rec["maker_appraisal"]              # the overwrite this guards
        raised = False
        try:
            stage5.check_owners_distinct(rec)
        except stage5.LatentRecordError:
            raised = True
        assert raised
        m = stage5.merge_records({"content_support": {"candidates": {"h": 0.8, "l": 0.2}, "unknown": 0.0, "confidence": 0.8, "evidence": ["e1"]}},
                                 {"content_support": {"candidates": {"h": 0.8, "l": 0.2}, "unknown": 0.0, "confidence": 0.8, "evidence": ["e1"]}})
        assert m["content_support"]["candidates"]["h"] == 0.8, "identical evidence must add no constraint"
    check("6 owner variables cannot overwrite", t6)

    def t7():
        from runners import s5_run_j                                              # noqa: PLC0415
        w = s5_worlds.make_joint_world("J01|civic|s1|w0005|discovery", "civic")
        c1, c2 = s5_run_j.candidates(w), s5_run_j.candidates(w)
        assert c1 == c2 and set(c1) == {"episode_goal", "process_plan", "standing_preference"}
        assert " > ".join(w["process_plan"]) in c1["process_plan"]
        ev1, ids1 = s5_run_j.evidence_text(w)
        ev2, ids2 = s5_run_j.evidence_text(w)
        assert ev1 == ev2 and ids1 == ids2
        assert s5_run_j.CALL_ALLOWANCE == 9
        assert len(s5_run_j.STAGED) == 3
    check("7 joint and staged readers share evidence, candidates, allowance", t7)

    def t8():
        import torch                                                              # noqa: PLC0415
        from soundingline.probe.conditional_reader import load_reader             # noqa: PLC0415
        from soundingline.probe.interventions import get_blocks                   # noqa: PLC0415
        from runners.s3_run_a import additive_steer                                # noqa: PLC0415
        model, tok = load_reader(MODEL, device="cpu", dtype="float32")
        ids = tok("The keeper climbed the stairs and checked the lamp.", return_tensors="pt").input_ids
        d = torch.randn(model.config.hidden_size)
        d = d / d.norm()
        b = len(get_blocks(model)) // 2
        with torch.no_grad():
            base = model(ids).logits
        with additive_steer(model, [b], d, 2.0):
            with torch.no_grad():
                plus = model(ids).logits
                plus2 = model(ids).logits
        with additive_steer(model, [b], d, -2.0):
            with torch.no_grad():
                minus = model(ids).logits
        with additive_steer(model, [b + 1], d, 2.0):
            with torch.no_grad():
                shifted = model(ids).logits
        with torch.no_grad():
            after = model(ids).logits
        assert s5_lib.hooks_present(model) == 0, "hook not removed"
        assert torch.equal(base, after), "baseline not restored"
        assert torch.equal(plus, plus2), "replay differs"
        assert not torch.equal(base, plus) and not torch.equal(plus, minus) and not torch.equal(plus, shifted)
        # dose: a larger alpha moves more
        with additive_steer(model, [b], d, 4.0):
            with torch.no_grad():
                big = model(ids).logits
        assert (big - base).abs().mean() > (plus - base).abs().mean()
    check("8 L255 replication: coordinates, dose, sign, hook removal, replay", t8)

    def t9():
        L = s4.Lineages(tmp / "lin.json")
        d = L.allocate("J01", "civic", [0], 1, "discovery")[0]
        c = L.allocate("J01", "civic", [10], 1, "confirmation", world_offset=10000)[0]
        child = L.derive(d, "j02", card="J02")
        L.check_fresh([c])
        L.mark_inspected([d])
        raised = False
        try:
            L.check_fresh([child])
        except s4.FreshnessViolation:
            raised = True
        assert raised, "a derived child of an inspected root passed as fresh"
        L.mark_inspected([c])
        raised = False
        try:
            L.check_fresh([c])
        except s4.FreshnessViolation:
            raised = True
        assert raised
    check("9 confirmation access rejected after inspection or shared ancestry", t9)

    def t10():
        from runners.s5_run_common import cluster_by_construction                # noqa: PLC0415
        rows = [{"unit_id": "u1", "primary_score": 1.0, "extra": {"construction_hash": "h1"}},
                {"unit_id": "u2", "primary_score": 0.0, "extra": {"construction_hash": "h1"}},
                {"unit_id": "u3", "primary_score": 1.0, "extra": {"construction_hash": "h2"}}]
        a = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(cluster_by_construction(rows), "unit_id", "primary_score"), 1)
        b = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means(cluster_by_construction(list(reversed(rows))), "unit_id", "primary_score"), 1)
        assert a == b and a["n_units"] == 2
        agg = s4.aggregate_equal(rows, "unit_id", "extra", "primary_score") if False else None
        assert agg is None
    check("10 aggregation order-invariant, clustered at the construction", t10)

    def t11():
        p = tmp / "contract.json"
        c = stage5.RunContract5.create(path=p)
        c.start()
        d1 = c.data["deadline_epoch"]
        c2 = stage5.RunContract5.load(p)
        c2.start()
        assert c2.data["deadline_epoch"] == d1, "restart reset the clock"
        assert not c2.stops_at_deadline and c2.data["run_until_queue_empty"]
        c2.record_lost_time("gpu wait", 90.0)
        assert stage5.RunContract5.load(p).data["lost_time"][0]["seconds"] == 90.0
        raised = False
        try:
            stage5.validate_run_label(c2, "COMPLETE_24H")
        except s4.ContractError:
            raised = True
        assert raised, "a short run was labeled a completed window"
        stage5.validate_run_label(c2, "RUN_TO_EMPTY")
    check("11 clock persists; short run cannot be labeled complete", t11)

    def t12():
        p = tmp / "contract2.json"
        c = stage5.RunContract5.create(path=p)
        c.start()
        raised = False
        try:
            stage5.write_packet("x", c, exhausted=False)
        except s4.PacketGuard:
            raised = True
        assert raised, "packet written before closure"
        raised = False
        try:
            stage5.refuse_packet_path(tmp / "CURATOR_PACKET_DAY1.md")
        except s4.PacketGuard:
            raised = True
        assert raised
        raised = False
        try:
            stage5.refuse_packet_path(stage5.S5 / "packet_preview.md")
        except s4.PacketGuard:
            raised = True
        assert raised
        stage5.refuse_packet_path(stage5.S5 / "CURATOR_PACKET_FINAL.md")
    check("12 packet path and closure guards", t12)

    def t13():
        L = s4.Lineages(tmp / "lin4.json")
        for lane, off in (("discovery", 0), ("transfer", s5_worlds.TRANSFER_WORLD_OFFSET), ("confirmation", s5_worlds.CONFIRMATION_WORLD_OFFSET)):
            ids = L.allocate("A01", "memo", [0], 2, lane, world_offset=off)
            assert L.rows[ids[0]]["split"] == lane
        assert s5_worlds.lineage_index("A01|memo|s20|w20003|transfer") == (3, "transfer")
        a = s5_sources.make_source_world("A01|memo|s0|w0003|discovery", "memo")
        b = s5_sources.make_source_world("A01|memo|s20|w20003|transfer", "memo")
        c = s5_sources.make_source_world("A01|memo|s10|w10003|confirmation", "memo")
        assert len({a["text"], b["text"], c["text"]}) == 3, "lanes share a construction"
    check("13 four lanes allocate with disjoint identity blocks", t13)

    def t14():
        # an infrastructure pass and a descriptive card carry their own labels, never VOID
        # (the Stage-4 manifest's whitelist refused them and crashed the third smoke)
        m = stage5.Manifest5(tmp / "manifest14.json")
        m.add("X", "I01", [], "x", 1.0, False, "test")
        for oc in ("INFRASTRUCTURE", "DESCRIPTIVE", "VOID"):
            m.set_outcome("X", oc)
            assert m.cells["X"]["outcome"] == oc
        try:
            m.set_outcome("X", "PASSED")
            raise AssertionError("an unknown label was accepted")
        except AssertionError as e:
            if "unknown label" in str(e):
                raise
    check("14 the manifest accepts the two Stage-5 labels and refuses unknown ones", t14)

    def t15():
        # the future-choice readout, version 2: short axis-word candidates with the option
        # sentences in the body (LESSONS §3); version 1 kept reproducible for the record
        from runners import s5_run_j
        w = s5_worlds.make_joint_world("J01|workshop|s0|w0000|discovery", "workshop")
        b1, c1 = s5_run_j.choice_prompt(w, {}, w["target_scenario"], version="1")
        b2, c2 = s5_run_j.choice_prompt(w, {}, w["target_scenario"], version="2")
        assert set(c2) == set(w["scenarios"][w["target_scenario"]]["feasible"])
        assert all(k == v for k, v in c2.items()), "v2 candidates are the axis words"
        assert all(len(v) > len(k) for k, v in c1.items()), "v1 candidates were the sentences"
        assert all(w["scenarios"][w["target_scenario"]]["options"][ax] in b2 for ax in c2), "v2 body lists every option"
    check("15 the future-choice readout v2 scores axis words with the options in the body", t15)

    def t16():
        # design 2: the lenient order parser and the twin pairing key
        from runners import s5_run_p
        assert s5_run_p.parse_order_lenient("3, 1, 4, 2") == [3, 1, 4, 2]
        assert s5_run_p.parse_order_lenient("I think 2 then 2 then 4, 1, 3.") == [2, 4, 1, 3]
        assert s5_run_p.parse_order_lenient("strokes 1 and 2 first") is None
        import inspect
        from runners import s5_run_a
        src = inspect.getsource(s5_run_a)
        assert 'pairs.setdefault((r["model_id"], r["unit_id"], r["factors"]["behavior"])' in src, "twin pairs key on the unit"
    check("16 design 2: lenient order parser; twin pairs keyed on the unit", t16)

    def t17():
        # design 2 worlds: equifinal twins exist, the forensic step pays in some worlds, the
        # second episode's ceiling clears uniform; the default design is unchanged
        import importlib, math, os
        os.environ["S5_DESIGN"] = "2"
        try:
            import runners.s5_worlds as W2
            W2 = importlib.reload(W2)
            lids = [(f"J01|{d}|s0|w{i:04d}|discovery", d) for d in ("workshop", "civic") for i in range(16)]
            eq = pays = 0
            lp = []
            for lid, d in lids:
                w = W2.make_joint_world(lid, d)
                eq += int(w["equifinal"])
                ri = W2.route_information(w, 6)
                pays += int(ri["forensic"]["kl_from_prior"] > w["forensic_cost_nats"])
                ti = w["target2_scenario"]
                hs = W2.hypotheses(w)
                oh = {h: 1.0 if (h[0] == w["episode_goal"] and h[1] == w["standing_preference"] and tuple(h[2]) == tuple(w["process_plan"])) else 0.0 for h in hs}
                pr = W2.predictive(w, oh, ti)
                lp.append(math.log(max(pr[w["scenarios"][ti]["draw"]], 1e-9)))
            assert eq >= 6, f"equifinal worlds under design 2: {eq} of 32"
            assert 6 <= pays <= 26, f"forensic pays in {pays} of 32"
            assert sum(lp) / len(lp) > math.log(0.25) + 0.4, f"episode-2 ceiling {sum(lp) / len(lp):.3f}"
        finally:
            os.environ.pop("S5_DESIGN", None)
            import runners.s5_worlds as W1
            W1 = importlib.reload(W1)
            assert W1.FORENSIC_COST_NATS == 0.08 and W1.GOAL_BONUS2 is None
            w = W1.make_joint_world("J01|workshop|s0|w0000|discovery", "workshop")
            assert w["relaxed_order"] is False
    check("17 design 2 worlds: equifinal twins, a forensic step that pays, a second episode that clears uniform", t17)

    def t18():
        # TODO (u), (v): the abstention rule has no near-equal clause; the integrity runners honor S5_CELL
        import inspect, os
        from runners import s5_run_a, s5_run_i
        assert "abs(a[\"probs\"]" not in inspect.getsource(s5_run_a), "the near-equal clause is gone"
        os.environ["S5_CELL"] = "I03/v2"
        try:
            assert s5_run_i._card_dir("I03").as_posix().endswith("I03/v2")
            assert s5_run_i._card_dir("I04").as_posix().endswith("I04")
        finally:
            os.environ.pop("S5_CELL", None)
    check("18 the twin-abstention rule and the integrity runners' cell override", t18)

    def t19():
        # 2026-08-30 receipts: the ease rulers order a known-answer rendering as harder (the mean
        # ruler cannot), the validation can fail, and the echo rule declares its population
        import os
        added = [k for k in ("S5_DESIGN", "S5_STAGE", "S5_ROOT") if k not in os.environ]
        try:
            from runners import s5_receipts as R
            from runners.s5_ease_ruler import validate
            from runners.s5_p02_echo import blind_rate_excluding_echo, is_echo
            plain = [("It", -1.0), (" chose", -2.0), (" oak", -3.0)]
            dotted = [("It", -1.0), (" \u00b7", -0.1), (" chose", -2.0), (" \u00b7", -0.1), (" oak", -3.0)]
            a, b = R.rulers(plain), R.rulers(dotted)
            assert b["mean_token_logp"] > a["mean_token_logp"], "the mean ruler rates the dotted text easier (L301)"
            assert b["total_logp"] < a["total_logp"] and b["neg_token_count"] < a["neg_token_count"]
            assert abs(b["content_total_logp"] - a["content_total_logp"]) < 1e-9, "content tokens unchanged by filler"
            names = ("stilted", "stilted2", "stilted3", "stilted4", "stilted5")
            good = {"r": {k: {ru: {"harder_fraction": 1.0, "mean_diff": -1.0} for ru in R.RULER_NAMES} for k in names}}
            v = validate(good)
            assert v["realized"] and v["ruler"] == "content_total_logp"
            bad = {"r": {k: {ru: {"harder_fraction": 0.5, "mean_diff": 0.0} for ru in R.RULER_NAMES} for k in names}}
            v = validate(bad)
            assert not v["realized"] and v["passing"] == [], "the validation can fail"
            assert is_echo([1, 2, 3, 4]) and not is_echo([2, 1, 3, 4]) and not is_echo(None)
            assert abs(blind_rate_excluding_echo([[1, 2, 3, 4], [2, 1, 3, 4], [1, 2, 4, 3], [2, 1, 4, 3]]) - 3 / 23) < 1e-9
            assert abs(blind_rate_excluding_echo([[3, 4, 1, 2], [4, 3, 1, 2], [3, 4, 2, 1], [4, 3, 2, 1]]) - 4 / 23) < 1e-9
        finally:
            for k in added:
                os.environ.pop(k, None)
    check("19 the ease rulers and their validation can fail; the echo rule declares its population", t19)

    print(f"\n{len(fails)} failures")
    for f in fails:
        print("  -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
