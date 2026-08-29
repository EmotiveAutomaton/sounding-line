"""Stage 4 hierarchy track (brief §7 H01-H03): shared conventions and goals through a
relay, continuous goal weights and traces after editing, and human writing episodes
beyond label persistence.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (hop-zero realization before any decay curve; a shared brief
  is the required rival to a director; exact collisions are identifiability bounds;
  relative weights only, scale and noise aliased by construction; the session-log
  lesson: a record's chronology is audited, never assumed; leave-one-project-out with
  author overlap disclosed), §5 (produces guards; CPU caps), CONTROLS §6.
gates and bands:
  - H01 hop-zero gate: a chain whose hop-0 plan does not satisfy its primary constraint
    (mechanically, from the plan JSON) is unrealized and its decay curve is not
    interpreted; chains under 0.80 realization void the relay interpretation for that
    cell. The local elaboration (the maker's stated favorite holding the largest free
    share) is verified at hop 0 as well and its relay curve is read only on chains
    that realized it. Primary (the frozen contrast in s4_cards): retention at hop 3
    minus hop 1 under the SHARED convention minus the same under the REMAPPED
    convention, director construction, paired by chain. NULL: 0 (the convention does
    not change what survives the relay). ALTERNATIVE: positive (a shared convention
    carries the upstream constraint further); the plain decay curves and each cell's
    hop 3 minus hop 1 are reported beside it. Attribution rival:
    director versus shared-brief construction on identical dependency rules; the
    reader's attribution accuracy is expected at 0.5 and reported, not gated.
  - H02 primary: history-type balanced accuracy with the ordered history minus
    artifact-only, paired by unit. NULL: 0. ALTERNATIVE: >= 0.05. Collision control:
    stable versus marker-removed histories share every draw and differ only in their
    explicit markers, so the artifact-only reader must sit at 0.5 on that pair; a
    reader above 0.6 there marks a leak, not a finding.
  - H03 primary: online next-boundary log loss of the text-plus-duration model minus
    the duration-aware baseline, leave-one-project-out, five projects reported one by
    one. NULL: 0. ALTERNATIVE: an improvement of 0.05 in balanced accuracy. Five
    projects cap generalization whatever the keystroke count; author overlap is
    disclosed in the verdict.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_lib, s4_worlds                                             # noqa: E402
from runners.s4_run_common import CardRun, DeadlineReached, cell_counts, mean_by, select_rows  # noqa: E402
from soundingline.s4 import append_jsonl, read_jsonl, write_json                  # noqa: E402

SEED = 49000
REMAP = {"materials": "stock", "labor": "hands", "inspection": "checking", "transport": "carriage"}
REALIZATION_FLOOR = 0.80


# ── H01 ───────────────────────────────────────────────────────────────────────────────

def _schema(remapped: bool) -> str:
    keys = [REMAP[k] if remapped else k for k in s4_worlds.PLAN_ITEMS]
    return "{" + ", ".join(f"\"{k}\": <share>" for k in keys) + "}"


def _show_plan(plan: dict, remapped: bool) -> str:
    return json.dumps({(REMAP[k] if remapped else k): round(float(plan[k]), 2)
                       for k in s4_worlds.PLAN_ITEMS})


def _unmap(plan: dict) -> dict:
    inv = {v: k for k, v in REMAP.items()}
    out = {}
    for k, v in plan.items():
        out[inv.get(k, k)] = v
    return out


def _leaf_sum(v) -> float | None:
    """A share may arrive as a number, a numeric string, or a nested dict of parts
    (the smoke test's makers wrote {"materials": {"wood": 25, "fabric": 10}}); nested
    parts sum. Any positive scale is accepted because shares are normalized by total."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip().rstrip("%"))
        except ValueError:
            return None
    if isinstance(v, dict):
        parts = [_leaf_sum(x) for x in v.values()]
        parts = [p for p in parts if p is not None]
        return sum(parts) if parts else None
    return None


def _parse_any_plan(text: str) -> dict | None:
    """The outermost JSON object carrying the four items (nested braces allowed)."""
    import re                                                                     # noqa: PLC0415
    txt = text or ""
    starts = [m.start() for m in re.finditer(r"\{", txt)]
    for s in starts:
        depth = 0
        for j in range(s, len(txt)):
            if txt[j] == "{":
                depth += 1
            elif txt[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(txt[s:j + 1])
                    except Exception:                                            # noqa: BLE001
                        break
                    if isinstance(obj, dict):
                        un = _unmap(obj)
                        present = [k for k in s4_worlds.PLAN_ITEMS if k in un]
                        # a plan naming three of the four items allocates nothing to the
                        # fourth (the smoke test's makers dropped 'inspection' while
                        # meeting the floor); fewer than three is not a plan
                        if len(present) >= 3:
                            vals = {k: (_leaf_sum(un[k]) if k in un else 0.0)
                                    for k in s4_worlds.PLAN_ITEMS}
                            if all(v is not None and v >= 0 for v in vals.values()) and sum(vals.values()) > 0:
                                return vals
                    break
    return None


def _hop0_prompt(cw: dict, construction: str, constrained: str, floor: float) -> str:
    """Hop 0. The smoke makers put the floor's number on the FIRST key of the example
    ('35 percent to inspection' became materials 0.35) and otherwise followed their own
    appetite for materials, realizing the constraint in a third to a half of chains; the
    example now leads with the constrained key at its floor and the other three shares
    are equal placeholders, so the maker's local elaboration is still its own."""
    rule = f"allocate at least {int(floor * 100)} percent of the budget to {constrained}"
    if construction == "director":
        head = f"The director of {cw['institution']} instructs you: {rule}."
    else:
        head = f"The shared brief of the {cw['institution'].split()[1]} tradition, which every maker reads: {rule}."
    # the example is itself a realized plan: the constrained key at its floor, the maker's
    # stated favorite the largest of the rest, the other two equal, all four summing to
    # 1.00 exactly (the loop smoke's example summed to 1.01, so a maker that copied it
    # landed at 0.3465 on a 0.35 floor and was scored unrealized, 23 of 44 attempts)
    others = [k for k in s4_worlds.PLAN_ITEMS if k != constrained]
    rest = round(1.0 - floor, 2)
    small = round(rest / 4, 2)
    big = round(rest - 2 * small, 2)
    shape = json.dumps({constrained: floor, cw["local_pref"]: big,
                        **{k: small for k in others if k != cw["local_pref"]}})
    return (f"{head} You are planning the {cw['item']} commission. You personally favor "
            f"{cw['local_pref']} and give it the largest share you can within the rule. Reply with the "
            f"plan as ONE flat JSON object with exactly these four keys and plain numbers that sum to "
            f"1.0. Write the \"{constrained}\" share first and keep it at {floor:.2f} or more; the other "
            f"three shares are yours to set, for example {shape}. No nested parts, no percent signs; "
            f"then one sentence on your emphasis.")


def _relay_prompt(cw: dict, prev_plan: dict, construction: str, remapped: bool,
                  constrained: str, floor: float, hop: int) -> str:
    brief = (f" The shared brief every maker reads: allocate at least {int(floor * 100)} percent of "
             f"the budget to {constrained}." if construction == "brief" else "")
    return (f"You are maker {hop} in the {cw['institution'].split()[1]} tradition.{brief} The "
            f"previous maker's plan for a similar commission was: {_show_plan(prev_plan, remapped)}. "
            f"Produce your own plan for a new {cw['item']} commission in the same tradition. Reply "
            f"with ONE flat JSON object {_schema(remapped)} with plain numbers that sum to 1.0 (no "
            f"nested parts, no percent signs), then one sentence on your emphasis.")


def arm_h01() -> int:
    run = CardRun("H01", "s4_run_h.py")
    maker = run.readers[0] if run.readers else None
    chains_path = run.out / "chains.jsonl"
    chains = {r["key"]: r for r in read_jsonl(chains_path)}
    with s4_lib.GpuSession("s4_h01") as gs:
        if maker:
            model, tok, _ = s4_lib.load_model(maker)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        cw = s4_worlds.make_chain_world(lid, domain)
                        run.register_world(lid, cw)
                        variants = [("director", "shared", False), ("director", "remapped", False),
                                    ("brief", "shared", False), ("brief", "remapped", False),
                                    ("director", "shared", True)]        # last: constraint flipped
                        for construction, convention, flipped in variants:
                            key = f"{lid}|{construction}|{convention}|{'flip' if flipped else 'orig'}"
                            if key in chains:
                                continue
                            run.check_deadline()
                            constrained = cw["flipped_item"] if flipped else cw["constrained_item"]
                            floor = cw["floor"]
                            remapped = convention == "remapped"
                            plans, texts, realized0 = [], [], False
                            prompt = _hop0_prompt(cw, construction, constrained, floor)
                            for att in range(2):
                                g = s4_lib.generate(model, tok, prompt, seed=SEED + 100 * i + att, max_new=110)
                                plan = _parse_any_plan(g["text"])
                                ok = plan is not None and s4_worlds.plan_satisfies(plan, constrained, floor)
                                run.raw(maker, lid, prompt, g, validity_reason="ok" if ok else "hop0_unrealized",
                                        extra={"key": key, "hop": 0, "attempt": att})
                                if ok:
                                    plans.append(plan)
                                    texts.append(g["text"])
                                    realized0 = True
                                    break
                            if realized0:
                                for hop in (1, 2, 3):
                                    rp = _relay_prompt(cw, plans[-1], construction, remapped, constrained, floor, hop)
                                    g = s4_lib.generate(model, tok, rp, seed=SEED + 100 * i + 10 * hop, max_new=110)
                                    plan = _parse_any_plan(g["text"])
                                    run.raw(maker, lid, rp, g, validity_reason="ok" if plan else "malformed_plan",
                                            extra={"key": key, "hop": hop})
                                    if plan is None:
                                        break
                                    plans.append(plan)
                                    texts.append(g["text"])
                            tops = [max((k for k in s4_worlds.PLAN_ITEMS if k != constrained), key=lambda k: p[k]) for p in plans]
                            rec = {"key": key, "lineage_id": lid, "domain": domain, "construction": construction,
                                   "convention": convention, "flipped": flipped, "constrained": constrained,
                                   "floor": floor, "hop0_realized": realized0, "plans": plans,
                                   "retention": [s4_worlds.plan_satisfies(p, constrained, floor) for p in plans],
                                   "original_constraint_kept": [s4_worlds.plan_satisfies(p, cw["constrained_item"], floor) for p in plans],
                                   "local_pref": cw["local_pref"], "top_free_item": tops,
                                   # the local elaboration is verified at hop 0 too (the largest free
                                   # share is the maker's stated favorite); its relay curve is read
                                   # only on chains where hop 0 realized it
                                   "local_realized0": bool(tops) and tops[0] == cw["local_pref"]}
                            chains[key] = rec
                            append_jsonl(chains_path, [rec])
                            run.flush()
            finally:
                s4_lib.free_model(model)
        # readers: downstream prediction and attribution on complete original chains
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        cw = s4_worlds.make_chain_world(lid, domain)
                        run.register_world(lid, cw)
                        rng = random.Random(SEED + 900 + i)
                        for construction in ("director", "brief"):
                            for convention in ("shared", "remapped"):
                                rec = chains.get(f"{lid}|{construction}|{convention}|orig")
                                if not rec or not rec["hop0_realized"] or len(rec["plans"]) < 4:
                                    continue
                                f = {"domain": domain, "construction": construction, "convention": convention, "hops": 3}
                                hist = "\n".join(f"- maker {h}: {_show_plan(p, False)}" for h, p in enumerate(rec["plans"][:3]))
                                truth = rec["top_free_item"][3]
                                opts = {k: k for k in s4_worlds.PLAN_ITEMS if k != rec["constrained"]}
                                body = (f"A tradition's plans, in order:\n{hist}\nThe next maker (maker 3) will produce a plan for "
                                        f"the {cw['item']} commission. Apart from {rec['constrained']}, which item will it give the largest share?")
                                r = s4_lib.likelihood_choice(model, tok, body, opts, rng)
                                run.row(reader, lid, lid, f"predict|{construction}|{convention}", {**f, "task": "downstream"},
                                        truth, "realized_choice", "ordered_history", r,
                                        s4_lib.log_score(r["probs"], truth) if r["valid"] else None,
                                        extra={"correct": r["valid"] and r["pred"] == truth})
                                # attribution: director versus shared brief (identical rules)
                                hist4 = "\n".join(f"- maker {h}: {_show_plan(p, False)}" for h, p in enumerate(rec["plans"][:4]))
                                body = (f"A tradition's plans, in order:\n{hist4}\nWas this tradition steered by a director's "
                                        f"instruction to the first maker only, or by a shared brief that every maker read?")
                                ra = s4_lib.likelihood_choice(model, tok, body, {"director": "a director instructed the first maker only",
                                                                                 "brief": "a shared brief that every maker read"}, rng)
                                run.row(reader, lid, lid, f"attrib|{construction}|{convention}", {**f, "task": "attribution"},
                                        construction, "construction", "ordered_history", ra,
                                        s4_lib.log_score(ra["probs"], construction) if ra["valid"] else None,
                                        extra={"correct": ra["valid"] and ra["pred"] == construction})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _h01_analyze(run, gs.held_s, chains)


def _h01_analyze(run: CardRun, gpu_s: float, chains: dict) -> int:
    recs = list(chains.values())
    orig = [r for r in recs if not r["flipped"]]
    realization = {}
    for construction in ("director", "brief"):
        for convention in ("shared", "remapped"):
            sub = [r for r in orig if r["construction"] == construction and r["convention"] == convention]
            realization[f"{construction}|{convention}"] = {"attempted": len(sub),
                                                           "hop0_realized": sum(r["hop0_realized"] for r in sub),
                                                           "local_realized0": sum(bool(r.get("local_realized0")) for r in sub),
                                                           "complete_chains": sum(len(r["plans"]) == 4 for r in sub)}

    def retention_at(sub, hop):
        return {r["lineage_id"]: float(r["retention"][hop]) for r in sub if len(r["plans"]) > hop}

    def decay(sub):
        r3, r1 = retention_at(sub, 3), retention_at(sub, 1)
        return {u: r3[u] - r1[u] for u in r3 if u in r1}

    curves, primary_diffs, decays = {}, {}, {}
    for construction in ("director", "brief"):
        for convention in ("shared", "remapped"):
            sub = [r for r in orig if r["construction"] == construction and r["convention"] == convention and r["hop0_realized"]]
            curves[f"{construction}|{convention}"] = {str(h): (sum(retention_at(sub, h).values()) / max(1, len(retention_at(sub, h))))
                                                      for h in range(4)}
            decays[f"{construction}|{convention}"] = decay(sub)
            primary_diffs[f"{construction}|{convention}"] = s4_lib.cluster_bootstrap_ci(decays[f"{construction}|{convention}"], SEED + 1)
    # the frozen primary (s4_cards): retention at hop 3 minus hop 1, SHARED minus REMAPPED
    # convention, director construction, paired by chain; positive means the shared
    # convention carries the upstream constraint further through the relay
    d_sh, d_rm = decays["director|shared"], decays["director|remapped"]
    primary = s4_lib.cluster_bootstrap_ci({u: d_sh[u] - d_rm[u] for u in d_sh if u in d_rm}, SEED + 4)
    # convention effect at hop 3 (shared minus remapped, director)
    sh = retention_at([r for r in orig if r["construction"] == "director" and r["convention"] == "shared" and r["hop0_realized"]], 3)
    rm = retention_at([r for r in orig if r["construction"] == "director" and r["convention"] == "remapped" and r["hop0_realized"]], 3)
    convention_effect = s4_lib.cluster_bootstrap_ci({u: sh[u] - rm[u] for u in sh if u in rm}, SEED + 2)
    # causal reach: flipped chains satisfy the flipped constraint at hop 3 minus original chains satisfying it
    flips = [r for r in recs if r["flipped"] and r["hop0_realized"] and len(r["plans"]) == 4]
    reach = {}
    for fr in flips:
        o = chains.get(fr["key"].replace("|flip", "|orig"))
        if o and o["hop0_realized"] and len(o["plans"]) == 4:
            reach[fr["lineage_id"]] = float(s4_worlds.plan_satisfies(fr["plans"][3], fr["constrained"], fr["floor"])) - \
                float(s4_worlds.plan_satisfies(o["plans"][3], fr["constrained"], fr["floor"]))
    reach_ci = s4_lib.cluster_bootstrap_ci(reach, SEED + 3)
    # local contribution: does hop k's top free item follow hop 0's local preference?
    local = {}
    for r in orig:
        if r["hop0_realized"] and r.get("local_realized0") and len(r["plans"]) == 4:
            local.setdefault(f"{r['construction']}|{r['convention']}", []).append(
                [float(t == r["local_pref"]) for t in r["top_free_item"]])
    local_follow = {k: {"by_hop": [sum(x[h] for x in v) / len(v) for h in range(4)], "n_chains": len(v)}
                    for k, v in local.items()}
    rows = [r for r in run.rows() if r["valid"]]
    downstream = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("correct")))}
                          for r in rows if r["factors"].get("task") == "downstream"], ["construction", "convention"])
    attribution = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("correct")))}
                           for r in rows if r["factors"].get("task") == "attribution"], ["construction", "convention"])
    threshold = run.design.get("thresholds", {}).get("H01", 0.05) or 0.05
    realized_ok = all(v["hop0_realized"] / max(1, v["attempted"]) >= REALIZATION_FLOOR for v in realization.values())
    if not realized_ok:
        verdict = {"outcome": "INSTRUMENT_FAILED", "reason": "hop-zero realization under 0.80 in a cell; decay not interpreted"}
    else:
        verdict = run.classify(primary, threshold)
    run.finish({"realization": realization, "retention_curves": curves, "hop3_minus_hop1": primary_diffs,
                "primary_shared_minus_remapped_decay_director": primary,
                "decay_director_shared": primary_diffs["director|shared"],
                "convention_effect_hop3": convention_effect,
                "causal_reach_flip": reach_ci, "local_preference_followed_by_hop": local_follow,
                "downstream_prediction_accuracy": downstream, "attribution_accuracy": attribution,
                "cell_counts": cell_counts(run.rows(), ["construction", "convention", "task"])},
               {"exec": "COMPLETE", "primary": "constraint retention hop 3 minus hop 1, shared minus remapped convention, director",
                **verdict}, gpu_s)
    return 0


# ── H02 ───────────────────────────────────────────────────────────────────────────────

HIST_DESC = {"stable": "one steady secondary aim throughout",
             "gradual": "a secondary aim that shifted gradually to another",
             "abrupt": "a secondary aim that switched abruptly halfway",
             "marker_removed": "a steady secondary aim that stopped being stated halfway",
             "fresh_final": "a maker who only ever held the later secondary aim"}


def arm_h02() -> int:
    run = CardRun("H02", "s4_run_h.py")
    with s4_lib.GpuSession("s4_h02") as gs:
        for reader in run.readers:
            model, tok, _ = s4_lib.load_model(reader)
            try:
                for domain in ("workshop", "civic"):
                    for i, lid in enumerate(run.units(domain)):
                        if run.is_done(reader, lid):
                            continue
                        run.check_deadline()
                        rng = random.Random(SEED + 300 + i)
                        # the unit's identity is its shared draw sequence, which the stable
                        # history carries in full (the other types differ only in markers)
                        run.register_world(lid, s4_worlds.make_history_world(lid, domain, "stable"))
                        for htype in s4_worlds.HISTORY_TYPES:
                            hw = s4_worlds.make_history_world(lid, domain, htype)
                            f = {"domain": domain, "history": htype}
                            post = s4_worlds.weight_grid_posterior(hw, 12)
                            # later-decision prediction from the first nine steps
                            tgt = hw["steps"][11]
                            for access, upto_text in (("ordered_history", s4_worlds.history_record(hw, 9, True)),
                                                      ("artifact_only", s4_worlds.history_record(hw, 9, False).split("\n")[-4:])):
                                rec = upto_text if isinstance(upto_text, str) else "\n".join(upto_text)
                                body = (f"A maker's record:\n{rec}\nThe maker now faces: {tgt['context']}\nWhich option will it choose?")
                                r = s4_lib.likelihood_choice(model, tok, body, tgt["options"], rng)
                                run.row(reader, lid, lid, f"later|{htype}|{access}", {**f, "access": access, "task": "later_decision"},
                                        tgt["draw"], "realized_draw", access, r,
                                        s4_lib.log_score(r["probs"], tgt["draw"]) if r["valid"] else None,
                                        extra={"exact_posterior_second_half": post["second_half"]})
                                # history-type recovery
                                body = (f"A maker's record:\n{rec}\nEvery decision kept {hw['primary']} first. Which describes the "
                                        f"maker's secondary aims over the record?")
                                r2 = s4_lib.likelihood_choice(model, tok, body, dict(HIST_DESC), rng)
                                run.row(reader, lid, lid, f"type|{htype}|{access}", {**f, "access": access, "task": "history_type"},
                                        htype, "construction", access, r2,
                                        s4_lib.log_score(r2["probs"], htype) if r2["valid"] else None,
                                        extra={"correct": r2["valid"] and r2["pred"] == htype,
                                               "p_stable": r2["probs"].get("stable") if r2["valid"] else None,
                                               "p_marker_removed": r2["probs"].get("marker_removed") if r2["valid"] else None})
                        run.L.mark_inspected([lid])
                        run.unit_complete(reader, lid)
            finally:
                s4_lib.free_model(model)
    return _h02_analyze(run, gs.held_s)


def _h02_analyze(run: CardRun, gpu_s: float) -> int:
    rows = [r for r in run.rows() if r["valid"]]
    typ = [r for r in rows if r["factors"]["task"] == "history_type"]
    later = [r for r in rows if r["factors"]["task"] == "later_decision"]

    def ba_by_unit(rs):
        out = {}
        for u in {r["unit_id"] for r in rs}:
            sub = [r for r in rs if r["unit_id"] == u]
            out[u] = s4_lib.balanced_accuracy([r["pred"] for r in sub], [r["truth"] for r in sub], list(s4_worlds.HISTORY_TYPES))
        return out

    with_h = ba_by_unit(select_rows(typ, access="ordered_history"))
    art = ba_by_unit(select_rows(typ, access="artifact_only"))
    primary = s4_lib.cluster_bootstrap_ci({u: with_h[u] - art[u] for u in with_h if u in art}, SEED + 4)
    # collision control: stable vs marker_removed under artifact-only must be at chance
    coll = [r for r in typ if r["factors"]["history"] in ("stable", "marker_removed")]
    coll_acc = {}
    for access in ("artifact_only", "ordered_history"):
        sub = [r for r in coll if r["factors"]["access"] == access and r["extra"]["p_stable"] is not None]
        hits = 0
        for r in sub:
            guess = "stable" if r["extra"]["p_stable"] >= r["extra"]["p_marker_removed"] else "marker_removed"
            hits += guess == r["truth"]
        coll_acc[access] = {"pairwise_accuracy": hits / max(1, len(sub)), "n": len(sub)}
    later_ls = mean_by(later, ["history", "access"])
    type_acc = mean_by([{"factors": r["factors"], "primary_score": float(bool(r["extra"].get("correct")))} for r in typ], ["history", "access"])
    threshold = run.design.get("thresholds", {}).get("H02", 0.05) or 0.05
    verdict = run.classify(primary, threshold)
    if coll_acc.get("artifact_only", {}).get("pairwise_accuracy", 0) > 0.6:
        verdict["outcome"] = "INSTRUMENT_FAILED"
        verdict["reason"] = "artifact-only reader separates the exact-collision pair above 0.6: a leak"
    run.finish({"primary_history_minus_artifact_only_balanced_accuracy": primary, "collision_control": coll_acc,
                "later_decision_log_score": later_ls, "history_type_accuracy": type_acc,
                "note": "relative subsidiary weights only; temperature fixed at the environment's TEMP, so scale and noise are not identified",
                "cell_counts": cell_counts(run.rows(), ["history", "access", "task"])},
               {"exec": "COMPLETE", "primary": "history-type recovery, ordered history minus artifact-only", **verdict}, gpu_s)
    return 0


# ── H03 (CPU) ─────────────────────────────────────────────────────────────────────────

def arm_h03() -> int:
    import numpy as np                                                            # noqa: PLC0415
    import pandas as pd                                                           # noqa: PLC0415
    from datasets import load_from_disk                                           # noqa: PLC0415
    from sklearn.feature_extraction.text import TfidfVectorizer                   # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression                           # noqa: PLC0415
    from scipy.sparse import hstack, csr_matrix                                   # noqa: PLC0415
    run = CardRun("H03", "s4_run_h.py")
    t0 = time.time()
    ds = load_from_disk(str(REPO / "results" / "scholawrite" / "dataset"))
    df = ds["all_sorted"].to_pandas()
    df["ts"] = pd.to_numeric(df["timestamp"], errors="coerce")
    df = df.sort_values(["project", "ts"]).reset_index(drop=True)
    projects = sorted(df["project"].dropna().unique().tolist())
    # audit: chronology, fields, spans, author overlap
    audit = {"n_events": int(len(df)), "n_projects": len(projects),
             "authors_per_project": {p: sorted(df[df.project == p]["author"].unique().tolist()) for p in projects},
             "timestamp_monotone_within_project": bool(all((df[df.project == p]["ts"].diff().dropna() >= 0).all() for p in projects)),
             "labels": sorted(df["label"].dropna().unique().tolist())}
    overlap = {}
    for p in projects:
        others = set(df[df.project != p]["author"].unique().tolist())    # Python scalars
        overlap[p] = sorted(set(audit["authors_per_project"][p]) & others)
    audit["author_overlap_with_other_projects"] = overlap
    # runs and boundaries
    df["prev_label"] = df.groupby("project")["label"].shift(1)
    df["boundary"] = (df["label"] != df["prev_label"]).astype(int)
    df["next_boundary"] = df.groupby("project")["boundary"].shift(-1)
    run_len = []
    cur = 0
    last = None
    for p, lab in zip(df["project"], df["label"]):
        if last is None or p != last[0] or lab != last[1]:
            cur = 0
        cur += 1
        run_len.append(cur)
        last = (p, lab)
    df["run_len"] = run_len
    df["gap"] = df.groupby("project")["ts"].diff().fillna(0).clip(lower=0)
    df["log_gap"] = np.log1p(df["gap"] / 1000.0)
    df["delta"] = [a[len(b):] if a.startswith(b) else a for a, b in zip(df["after text"].fillna(""), df["before text"].fillna(""))]
    audit["run_length_mean"] = float(df["run_len"].mean())
    audit["boundary_rate"] = float(df["boundary"].mean())
    # leave-one-project-out
    per_project = {}
    for hold in projects:
        tr = df[(df.project != hold) & df["next_boundary"].notna()]
        te = df[(df.project == hold) & df["next_boundary"].notna()]
        if len(te) < 20:
            continue
        ytr, yte = tr["next_boundary"].astype(int).values, te["next_boundary"].astype(int).values
        # task 1 baselines: majority; duration-aware (run_len, log_gap, label one-hot)
        maj = int(ytr.mean() >= 0.5)
        maj_bacc = 0.5
        maj_ll = -float(np.mean(np.log(np.clip(np.where(yte == 1, ytr.mean(), 1 - ytr.mean()), 1e-9, 1))))
        labs = sorted(df["label"].dropna().unique().tolist())

        def tab(d):
            X = np.zeros((len(d), 2 + len(labs)))
            X[:, 0] = d["run_len"].values
            X[:, 1] = d["log_gap"].values
            for j, lab in enumerate(labs):
                X[:, 2 + j] = (d["label"] == lab).astype(float).values
            return X
        Xtr, Xte = tab(tr), tab(te)
        dur = LogisticRegression(max_iter=1000, class_weight="balanced").fit(Xtr, ytr)
        p_dur = dur.predict_proba(Xte)[:, 1]
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=5, max_features=4000)
        Ttr = vec.fit_transform(tr["delta"].fillna(""))
        Tte = vec.transform(te["delta"].fillna(""))
        both = LogisticRegression(max_iter=500, class_weight="balanced", C=0.5,
                                  solver="liblinear").fit(hstack([csr_matrix(Xtr), Ttr]), ytr)
        p_both = both.predict_proba(hstack([csr_matrix(Xte), Tte]))[:, 1]

        def ll(p):
            return -float(np.mean(np.log(np.clip(np.where(yte == 1, p, 1 - p), 1e-9, 1))))

        def bacc(p):
            pred = (p >= 0.5).astype(int)
            tpr = float(np.mean(pred[yte == 1] == 1)) if (yte == 1).any() else 0.0
            tnr = float(np.mean(pred[yte == 0] == 0)) if (yte == 0).any() else 0.0
            return (tpr + tnr) / 2
        # task 2: next distinct intention at true boundaries (oracle boundary)
        tr_b = tr[tr["next_boundary"] == 1]
        te_b = te[te["next_boundary"] == 1]
        nxt_tr = df.loc[tr_b.index + 1, "label"].values if len(tr_b) else np.array([])
        nxt_te = df.loc[te_b.index + 1, "label"].values if len(te_b) else np.array([])
        task2 = {}
        if len(te_b) and len(tr_b):
            from collections import Counter, defaultdict                          # noqa: PLC0415
            m1 = defaultdict(Counter)
            for cur_l, n_l in zip(tr_b["label"].values, nxt_tr):
                m1[cur_l][n_l] += 1
            majority_next = Counter(nxt_tr).most_common(1)[0][0]
            # oracle previous label
            pred_or = [m1[c].most_common(1)[0][0] if m1[c] else majority_next for c in te_b["label"].values]
            # previous label predicted without held-out annotations: a text model's own label read
            from sklearn.multiclass import OneVsRestClassifier                    # noqa: PLC0415
            lab_clf = OneVsRestClassifier(LogisticRegression(max_iter=500, C=0.5, solver="liblinear")).fit(Ttr, tr["label"].values)
            te_lab_pred = lab_clf.predict(Tte)
            te_b_pos = [te.index.get_loc(ix) for ix in te_b.index]
            pred_pr = [m1[te_lab_pred[k]].most_common(1)[0][0] if m1[te_lab_pred[k]] else majority_next for k in te_b_pos]
            task2 = {"n_boundaries": int(len(te_b)),
                     "majority": float(np.mean(nxt_te == majority_next)),
                     "markov_oracle_prev": float(np.mean(np.array(pred_or) == nxt_te)),
                     "markov_predicted_prev": float(np.mean(np.array(pred_pr) == nxt_te)),
                     "prev_label_read_accuracy": float(np.mean(te_lab_pred == te["label"].values))}
        per_project[hold] = {"n": int(len(te)), "authors": audit["authors_per_project"][hold],
                             "task1": {"majority_logloss": maj_ll, "majority_balanced_acc": maj_bacc, "majority_class": maj,
                                       "duration_logloss": ll(p_dur), "duration_balanced_acc": bacc(p_dur),
                                       "text_plus_duration_logloss": ll(p_both), "text_plus_duration_balanced_acc": bacc(p_both)},
                             "task2": task2}
    # primary: text+duration minus duration on balanced accuracy, cluster = project
    diffs = {p: v["task1"]["text_plus_duration_balanced_acc"] - v["task1"]["duration_balanced_acc"] for p, v in per_project.items()}
    primary = s4_lib.cluster_bootstrap_ci(diffs, SEED + 5)
    ll_diff = {p: v["task1"]["duration_logloss"] - v["task1"]["text_plus_duration_logloss"] for p, v in per_project.items()}
    threshold = run.design.get("thresholds", {}).get("H03", 0.05) or 0.05
    verdict = run.classify(primary, threshold)
    verdict["note"] = "five projects; author overlap disclosed; generalization capped by project count"
    run.finish({"audit": audit, "per_project": per_project, "primary_text_plus_duration_minus_duration_bacc": primary,
                "logloss_improvement": s4_lib.cluster_bootstrap_ci(ll_diff, SEED + 6),
                "cpu_minutes": round((time.time() - t0) / 60, 2)},
               {"exec": "COMPLETE", "primary": "online next-boundary forecast beyond duration and persistence", **verdict}, 0.0)
    write_json(run.out / "audit.json", audit)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["H01", "H02", "H03"])
    a = ap.parse_args()
    try:
        return {"H01": arm_h01, "H02": arm_h02, "H03": arm_h03}[a.card]()
    except DeadlineReached:
        print(f"{a.card}: deadline reached; rows checkpointed")
        return 3


if __name__ == "__main__":
    sys.exit(main())
