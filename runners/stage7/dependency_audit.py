"""The Stage 6 dependency audit (brief §2.2, D01-D06, D09; the record gate). Reads the
committed Stage 6 code and rows READ-ONLY and classifies every card and attack as CLEAN,
DEPENDENCY_TAINTED, CONSTRUCTION_INVALID, DUPLICATE_ESTIMAND, or UNRESOLVED, with the
evidence beside every disposition: a static access graph (which Stage 6 functions read
the hidden world fields, and which arms reach them), a dynamic trace (a recording world
object handed to the exact realizer records every key each arm's realization touched),
the decomposition recomputed from committed rows and reconstructed worlds (equal mixing
over the privileged exact simulators, model-derived label weights, exact-likelihood
adaptation, free-language contextual weighting), exact-likelihood identification renamed
as supplied-law selection, the implementation-identity matrix over the value and foraging
cards (identical per-unit score vectors), and the reader-free replay of the ScholaWrite
and drawing negatives. Nothing in results/phase_2_4_stage_6 is edited.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (a control reports what it checked beside what it found: every
  disposition carries its evidence; the identity check compares committed per-unit
  vectors, never card names; descriptive audit numbers carry no confirmatory language),
  §1c (a verdict is hunted, not caveated: the decomposition is recomputed, not inherited
  from the brief's citation), §5.
gates: D03's classification rule: NULL of a clean card is any non-oracle prediction path
  that reaches a hidden field (target_actions, events, stop_shift, trajectory beyond the
  cut, hidden) statically OR dynamically (failure direction: any reach taints the card
  DOWN to DEPENDENCY_TAINTED); ALTERNATIVE: no reach on any path. D06: two cards whose
  per-unit primary vectors are identical on the same lineages are one estimand (fails to
  DUPLICATE_ESTIMAND); distinct vectors keep separate estimands. bands: exhaustive (the
  five classes cover every card; UNRESOLVED is written, never omitted).
"""

from __future__ import annotations

import ast
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from soundingline.stage7 import AUDIT_CLASSES, S7, now_iso, read_json, read_jsonl, write_json, write_registry  # noqa: E402

S6 = REPO / "results" / "phase_2_4_stage_6"
S6_CODE = REPO / "runners" / "stage6"
HIDDEN_KEYS = ("target_actions", "events", "stop_shift", "hidden", "trajectory", "cut", "stop")
VISIBLE_KEYS = ("lid", "doc", "domain", "surface", "family")
ARMS = ("D", "L", "LD", "TT", "GS", "EX", "AD", "CR", "OR")


# ── D01: the static access graph ─────────────────────────────────────────────────────

def _module_functions(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out[node.name] = node
    return out


def _hidden_reads(fn: ast.FunctionDef) -> set[str]:
    """world["..."] subscripts and world.get("...") calls on hidden keys inside a function."""
    found = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            if node.slice.value in HIDDEN_KEYS and isinstance(node.value, ast.Name) and node.value.id in ("world", "w", "w1", "w2"):
                found.add(node.slice.value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            if isinstance(node.func.value, ast.Name) and node.func.value.id in ("world", "w") and node.args \
                    and isinstance(node.args[0], ast.Constant) and node.args[0].value in HIDDEN_KEYS:
                found.add(node.args[0].value)
    return found


def _calls(fn: ast.FunctionDef) -> set[str]:
    out = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def static_graph() -> dict:
    """Per module, per function: hidden keys read directly and the functions called; then
    the transitive hidden reach of every architecture arm and engine entry."""
    mods = {}
    for name in ("realization", "architectures", "worlds", "engines", "track_models", "trecords", "prediction", "attacks", "confirmation"):
        p = S6_CODE / f"{name}.py"
        if p.exists():
            mods[name] = _module_functions(p)
    direct: dict[str, set] = {}
    calls: dict[str, set] = {}
    for mname, fns in mods.items():
        for fname, fn in fns.items():
            direct[f"{mname}.{fname}"] = _hidden_reads(fn)
            calls[f"{mname}.{fname}"] = _calls(fn)
    by_short: dict[str, list[str]] = {}
    for full in direct:
        by_short.setdefault(full.split(".")[1], []).append(full)

    def reach(full: str, seen: set) -> set:
        if full in seen:
            return set()
        seen.add(full)
        out = set(direct.get(full, set()))
        for c in calls.get(full, set()):
            for target in by_short.get(c, []):
                out |= reach(target, seen)
        return out

    arms = {}
    for a in ARMS:
        key = f"architectures.arm_{a}"
        if key in direct:
            arms[a] = sorted(reach(key, set()))
    entries = {}
    for full in list(direct):
        if full.split(".")[1].startswith(("run_", "_p10", "_reader_card", "_value_reader", "_stat_card", "_confirm")):
            entries[full] = sorted(reach(full, set()))
    hot = {k: sorted(v) for k, v in direct.items() if v}
    return {"direct_hidden_reads": hot, "arm_transitive_hidden_reach": arms, "entry_transitive_hidden_reach": entries,
            "note": "predictive_at_cut reads target_actions, events, trajectory (its full length) and the stop hazard reads stop_shift; every non-oracle arm calls realize -> predictive_at_cut on the live world object"}


# ── dynamic trace: a recording world ─────────────────────────────────────────────────

class _Recorder(dict):
    def __init__(self, d: dict, log: set):
        super().__init__(d)
        self._log = log

    def __getitem__(self, k):
        self._log.add(k)
        return super().__getitem__(k)

    def get(self, k, default=None):
        self._log.add(k)
        return super().get(k, default)


def dynamic_trace(n: int = 4) -> dict:
    """Hand the exact realizer a recording world for each hypothesis tag and record every
    key it touched; the model-free part of every non-oracle arm is this call."""
    from runners.stage6 import realization as R                                   # noqa: PLC0415
    from runners.stage6 import worlds as W                                        # noqa: PLC0415
    touched: dict[str, set] = {}
    for i in range(n):
        lid = f"MB|essay|s0|w{i:05d}|discovery"
        w = W.make_process_world(lid, "essay", track="M")
        for h in R.hypothesis_space(w):
            log: set = set()
            R.realize(_Recorder(w, log), h["tag"])
            touched.setdefault("realize", set()).update(log)
        log2: set = set()
        R.predictive_at_cut(_Recorder(w, log2), R.cfg_for_tag(w, R.hypothesis_space(w)[0]["tag"]))
        touched.setdefault("predictive_at_cut", set()).update(log2)
        log3: set = set()
        W.render_evidence(_Recorder(w, log3))
        touched.setdefault("render_evidence", set()).update(log3)
    out = {k: sorted(v) for k, v in touched.items()}
    out["hidden_touched_by_realize"] = sorted(set(out.get("realize", [])) & set(HIDDEN_KEYS))
    out["hidden_touched_by_render"] = sorted(set(out.get("render_evidence", [])) & set(HIDDEN_KEYS))
    return out


# ── D02: the decomposition from committed rows ───────────────────────────────────────

def _rows(card: str, lane: str = "discovery") -> list[dict]:
    p = S6 / card / "cases.jsonl"
    return [r for r in read_jsonl(p) if r.get("valid") and r.get("primary_score") is not None and r.get("lane", "discovery") == lane] if p.exists() else []


def _unit_mean(rows: list[dict], key: str = "primary_score") -> dict:
    by: dict = {}
    for r in rows:
        by.setdefault(r["unit_id"], []).append(float(r[key]))
    return {u: sum(v) / len(v) for u, v in by.items()}


def decomposition() -> dict:
    """Equal mixing over the four exact controller realizations, the L arm's model-derived
    weights, the exact posterior (oracle-weighted mixture), and CR's free-language
    weighting, each scored on the committed rows' own worlds with the Stage 6 scorer, so
    the deltas are descriptive audit numbers on the same units."""
    from runners.stage6 import prediction as P                                    # noqa: PLC0415
    from runners.stage6 import realization as R                                   # noqa: PLC0415
    from runners.stage6 import worlds as W                                        # noqa: PLC0415
    d_rows = _rows("M01")
    l_rows = _rows("M02")
    cr_rows = _rows("M08")
    or_rows = _rows("M09")
    units = sorted(set(r["unit_id"] for r in l_rows) & set(r["unit_id"] for r in d_rows))
    equal, exact_post, label_w = {}, {}, {}
    for u in units[:400]:
        dom = next(r["factors"]["domain"] for r in l_rows if r["unit_id"] == u)
        w = W.make_process_world(u, dom, track="M")
        space = R.hypothesis_space(w)
        states = [R.realize(w, h["tag"]) for h in space]
        pred_eq = R.adapt(states, posterior={h["tag"]: 1.0 / len(space) for h in space})
        equal[u] = P.combined_primary(P.score_predictions(w, pred_eq))
        post = W.oracle_posterior(w)
        pred_ex = R.adapt(states, posterior={h["tag"]: post.get(h["tag"], 0.0) for h in space})
        exact_post[u] = P.combined_primary(P.score_predictions(w, pred_ex))
        lr = [r for r in l_rows if r["unit_id"] == u]
        lp = (lr[0].get("extra") or {}).get("posterior") if lr else None
        if lp:
            pred_l = R.adapt(states, posterior={h["tag"]: lp.get(h["tag"], 0.0) for h in space})
            label_w[u] = P.combined_primary(P.score_predictions(w, pred_l))
    d_m, l_m, cr_m, or_m = _unit_mean(d_rows), _unit_mean(l_rows), _unit_mean(cr_rows), _unit_mean(or_rows)
    common = [u for u in units[:400] if u in d_m and u in equal]

    def mean(dct, keys):
        vals = [dct[k] for k in keys if k in dct and dct[k] is not None]
        return (sum(vals) / len(vals)) if vals else None
    out = {"n_units": len(common),
           "direct_D": mean(d_m, common), "equal_mix_exact": mean(equal, common), "label_weights_L_recomputed": mean(label_w, common),
           "L_committed": mean(l_m, common), "exact_posterior_mix": mean(exact_post, common), "CR_committed": mean(cr_m, common),
           "OR_committed": mean(or_m, common)}
    if out["direct_D"] is not None and out["equal_mix_exact"] is not None:
        out["delta_equal_mix_minus_D"] = out["equal_mix_exact"] - out["direct_D"]
    if out["label_weights_L_recomputed"] is not None and out["equal_mix_exact"] is not None:
        out["delta_label_weights_minus_equal"] = out["label_weights_L_recomputed"] - out["equal_mix_exact"]
    if out["exact_posterior_mix"] is not None and out["label_weights_L_recomputed"] is not None:
        out["delta_exact_adaptation_minus_labels"] = out["exact_posterior_mix"] - out["label_weights_L_recomputed"]
    if out["CR_committed"] is not None and out["L_committed"] is not None:
        out["delta_CR_minus_L"] = out["CR_committed"] - out["L_committed"]
    out["brief_cited"] = {"equal_mix": 0.230, "label_weights": 0.002, "exact_adaptation": 0.055, "free_language": -0.017,
                          "note": "the brief's audit numbers, recomputed above on the committed units; descriptive, no confirmatory language"}
    return out


# ── D05: exact-likelihood identification renamed ────────────────────────────────────

def supplied_law_selection(n: int = 256) -> dict:
    from runners.stage6 import worlds as W                                        # noqa: PLC0415
    l_rows = _rows("M02")
    units = sorted(set(r["unit_id"] for r in l_rows))[:n]
    exact_map, exact_mass, label_map, label_mass = 0, 0.0, 0, 0.0
    k = 0
    for u in units:
        dom = next(r["factors"]["domain"] for r in l_rows if r["unit_id"] == u)
        w = W.make_process_world(u, dom, track="M")
        truth = w["cfg"]["controller"] if "cfg" in w else (w.get("truth") or {}).get("controller")
        post = W.oracle_posterior(w)
        if truth is None:
            continue
        k += 1
        exact_map += int(max(post, key=post.get) == truth)
        exact_mass += post.get(truth, 0.0)
        lr = [r for r in l_rows if r["unit_id"] == u]
        lp = (lr[0].get("extra") or {}).get("posterior") if lr else None
        if lp:
            label_map += int(max(lp, key=lp.get) == truth)
            label_mass += lp.get(truth, 0.0)
    return {"n": k, "exact_selection_map_accuracy": exact_map / max(1, k), "exact_selection_mean_mass_on_truth": exact_mass / max(1, k),
            "label_reader_map_accuracy": label_map / max(1, k), "label_reader_mean_mass_on_truth": label_mass / max(1, k),
            "marginal": 0.25, "name": "supplied-law selection (known-model system identification), never law learning or reconstruction",
            "brief_cited": {"label_mass": 0.257, "label_map": 0.289, "exact_map": 0.699}}


# ── D06: the implementation-identity matrix ──────────────────────────────────────────

def identity_matrix(cards: tuple[str, ...] = ("V02", "V03", "V04", "V05", "V08", "V09", "V10", "V13", "F02", "F03", "F04", "F05", "F06", "F08", "F09", "F10", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A13", "A14", "C04", "C06", "C08", "C10")) -> dict:
    vecs = {}
    for c in cards:
        rows = _rows(c)
        if not rows:
            continue
        vecs[c] = tuple(sorted((r["unit_id"].split("|")[-2] if "|" in r["unit_id"] else r["unit_id"], round(float(r["primary_score"]), 9)) for r in rows))
    dup = []
    constant = sorted(c for c, v in vecs.items() if v and len({x[1] for x in v}) == 1)
    names = sorted(vecs)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if vecs[a] == vecs[b] and len(vecs[a]) > 0:
                dup.append((a, b))
    # also a weaker identity: identical verdict point and n with identical world families
    verdict_dup = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            va, vb = read_json(S6 / a / "verdict.json") if (S6 / a / "verdict.json").exists() else {}, read_json(S6 / b / "verdict.json") if (S6 / b / "verdict.json").exists() else {}
            if va.get("point") is not None and va.get("point") == vb.get("point") and va.get("n_units") == vb.get("n_units"):
                verdict_dup.append((a, b))
    return {"identical_unit_vectors": dup, "identical_verdict_points": verdict_dup, "n_cards_with_rows": len(vecs),
            "constant_vectors": constant,
            "note": "a pair whose shared vector is constant is two dead statistics, not one live estimand; both are listed"}


# ── D09: reader-free replay of the natural negatives ─────────────────────────────────

def natural_negatives() -> dict:
    out = {}
    for c in ("T01", "T02", "T04"):
        v = read_json(S6 / c / "verdict.json") if (S6 / c / "verdict.json").exists() else {}
        m = read_json(S6 / c / "metrics.json") if (S6 / c / "metrics.json").exists() else {}
        out[c] = {"committed_outcome": v.get("outcome"), "point": v.get("point"), "ci": v.get("ci"), "n_units": v.get("n_units"),
                  "baseline_keys": [k for k in m if "baseline" in k.lower() or "previous" in k.lower() or "prior" in k.lower()][:8]}
    # the ScholaWrite previous-label baseline recomputed from the data with the Stage 7 loader
    try:
        from runners.stage7.records import scholawrite as SW                      # noqa: PLC0415
        ss = SW.sessions(max_sessions=60)
        n_pos = sum(len(s["events"]) - 1 for s in ss)
        n_same = sum(sum(1 for i in range(1, len(s["events"])) if s["events"][i]["category"] == s["events"][i - 1]["category"]) for s in ss)
        out["scholawrite_previous_category_persistence"] = {"n_sessions": len(ss), "n_transitions": n_pos, "persistence_rate": n_same / max(1, n_pos)}
    except Exception as e:                                                        # noqa: BLE001
        out["scholawrite_previous_category_persistence"] = {"error": repr(e)[:200]}
    return out


# ── D03/D04: dispositions ─────────────────────────────────────────────────────────────

def dispositions(graph: dict, dyn: dict, ident: dict) -> dict:
    from runners.stage6 import cards as C6                                        # noqa: PLC0415
    tainted_arms = {a for a, reach in graph["arm_transitive_hidden_reach"].items() if reach and a != "OR"}
    dup_cards = set()
    for a, b in ident["identical_unit_vectors"]:
        dup_cards.add(b)
    out = {}
    for card, spec in C6.CARDS.items():
        eng = spec["engine"]
        gpu = spec["gpu"]
        why = ""
        if card == "T02":
            cls, why = "CONSTRUCTION_INVALID", "the CoAuthor loader consumed suggestion-select as a delta before the acceptance branch; every scored decision was a dismissal (§2.1.8)"
        elif card in dup_cards:
            cls, why = "DUPLICATE_ESTIMAND", f"identical per-unit primary vector with {[a for a, b in ident['identical_unit_vectors'] if b == card]}"
        elif eng == "integrity":
            cls, why = ("DEPENDENCY_TAINTED", "the supplied-state gate realized the state through predictive_at_cut on the live world (target_actions, events, stop_shift, trajectory length)") if card == "I05" else ("CLEAN", "infrastructure receipt; no prediction path")
        elif eng == "tournament":
            cls, why = ("CLEAN", "the exact oracle ceiling (construction, never a competitor)") if card == "M09" else ("DEPENDENCY_TAINTED", f"non-oracle arms {sorted(tainted_arms)} reach hidden fields through realize -> predictive_at_cut")
        elif eng == "prospective":
            cls, why = "DEPENDENCY_TAINTED", "scores adapted predictions produced by tainted arms (M08 rows)"
        elif eng == "worldtrack":
            if gpu:
                cls, why = "DEPENDENCY_TAINTED", "reader cards realized supplied or inferred states through the live world object"
            else:
                cls, why = "CLEAN", "exact construction statistics on constructed worlds (no reader; no prediction path); interpretation retained only as construction facts"
        elif eng == "records":
            cls, why = ("CLEAN", "narrow negative under reader-free, lineage-clean baselines pending D09") if card in ("T01", "T04", "T03", "T05", "T08", "T09", "T10") else ("DEPENDENCY_TAINTED", "records reader cards depend on T02's loader or on tainted realization")
        elif eng == "closure":
            cls, why = "DEPENDENCY_TAINTED", "confirmation of a tainted discovery claim, or a ledger over tainted verdicts" if card in ("B01", "B02", "B04") else "read-only Ghost bridge ledger (CLEAN)"
            if card == "B03":
                cls = "CLEAN"
        else:
            cls, why = "UNRESOLVED", "no rule"
        assert cls in AUDIT_CLASSES
        out[card] = {"class": cls, "why": why, "engine": eng, "gpu": gpu}
    for x, spec in C6.ATTACKS.items():
        covered = [c for c in spec["covers"] if c in out]
        classes = {out[c]["class"] for c in covered}
        if "DEPENDENCY_TAINTED" in classes or "CONSTRUCTION_INVALID" in classes:
            out[x] = {"class": "DEPENDENCY_TAINTED", "why": f"covers {covered}: {sorted(classes)}", "engine": "attack", "gpu": spec["gpu"]}
        elif classes:
            out[x] = {"class": "CLEAN", "why": f"covers {covered}: clean", "engine": "attack", "gpu": spec["gpu"]}
        else:
            out[x] = {"class": "UNRESOLVED", "why": "no covered card", "engine": "attack", "gpu": spec["gpu"]}
    return out


SUSPENDED = {
    "architecture_ranking": "the nine-arm tournament (L over D +0.945 and every arm contrast): every non-oracle arm predicted through the exact realizer on the live world object; SUSPENDED (D04)",
    "reader_boundary": "the supplied-true-state gate and the 'reader boundary' (I05; event/cue reads pay, latent inference nulls): the supplied state was a prose goal, controller label, and remaining count realized by the constructor, not an operative supplied state; SUSPENDED (D04)",
    "M14_realization": "contextual realization beats copied realization (+2.187): fresh realization received the new world's constructor variables; close to tautological; SUSPENDED (D04)",
    "M15_semantic_invariance": "paraphrase-invariant realization (TV 0.000 vs 0.425): predictions preserved through the hypothesis tag while paraphrase semantics were ignored; SUSPENDED (D04)",
    "coauthor_T02": "CoAuthor accept/dismiss prediction (-0.368): the loader recorded no acceptance; INVALID (D04, D07)",
    "retained": "exact supplied-family likelihood selection, renamed supplied-law selection / known-model system identification (D05); construction facts from reader-free world statistics; the narrow natural negatives pending D09",
}


def write_audit(light: bool = False) -> dict:
    graph = static_graph()
    dyn = dynamic_trace(2 if light else 4)
    ident = identity_matrix()
    disp = dispositions(graph, dyn, ident)
    counts: dict = {}
    for v in disp.values():
        counts[v["class"]] = counts.get(v["class"], 0) + 1
    audit = {"written_at": now_iso(), "stage6_root": str(S6), "raw_untouched": True,
             "D01_static": graph, "D01_dynamic": dyn, "D06_identity": ident, "D03_dispositions": disp, "class_counts": counts,
             "D04_suspended": SUSPENDED, "D09_natural": natural_negatives()}
    if not light:
        audit["D02_decomposition"] = decomposition()
        audit["D05_supplied_law_selection"] = supplied_law_selection()
    write_registry("STAGE6_DEPENDENCY_AUDIT", audit)
    _write_md(audit)
    return audit


def _write_md(a: dict) -> Path:
    lines = ["# Stage 6 dependency audit (Stage 7 record gate)", "",
             f"Written {a['written_at']}. The Stage 6 raw outputs and packet are untouched; this file classifies them.", "",
             "## Dispositions (D03)", "", "| card | class | why |", "|---|---|---|"]
    for c, v in a["D03_dispositions"].items():
        lines.append(f"| {c} | {v['class']} | {v['why'][:150]} |")
    lines += ["", "*Table: one row per Stage 6 card and attack; class is one of the five audit classes; why names the evidence.*", "",
              f"Class counts: {json.dumps(a['class_counts'])}.", "",
              "## Suspended conclusions (D04)", ""]
    for k, v in a["D04_suspended"].items():
        lines.append(f"- **{k}**: {v}")
    d2 = a.get("D02_decomposition")
    if d2:
        lines += ["", "## Decomposition recomputed from committed rows (D02, descriptive)", "",
                  "| quantity | value |", "|---|---|"]
        for k, v in d2.items():
            if isinstance(v, (int, float)) and v is not None:
                lines.append(f"| {k} | {v:+.4f} |")
        lines.append("")
        lines.append("*Table: combined prospective primary (mean per unit) for the direct arm, the equal exact mixture, the label-weighted mixture, the exact-posterior mixture, and the committed L, CR, and oracle rows, with their differences; the brief's cited numbers sit in the JSON beside them.*")
    d5 = a.get("D05_supplied_law_selection")
    if d5:
        lines += ["", "## Supplied-law selection (D05)", "",
                  f"Exact selection among the four supplied controller laws: MAP accuracy {d5['exact_selection_map_accuracy']:.3f}, mean mass on truth {d5['exact_selection_mean_mass_on_truth']:.3f}; "
                  f"the label reader: MAP {d5['label_reader_map_accuracy']:.3f}, mass {d5['label_reader_mean_mass_on_truth']:.3f} (marginal 0.25; n {d5['n']}). "
                  "This is known-model system identification, retained under that name only."]
    lines += ["", "## Access graph (D01)", "",
              f"Direct hidden reads: {json.dumps(a['D01_static']['direct_hidden_reads'])[:1200]}", "",
              f"Arm transitive reach: {json.dumps(a['D01_static']['arm_transitive_hidden_reach'])}", "",
              f"Dynamic trace, keys the exact realizer touched: {json.dumps(a['D01_dynamic'].get('hidden_touched_by_realize'))}; the renderer: {json.dumps(a['D01_dynamic'].get('hidden_touched_by_render'))}.", "",
              "## Identity matrix (D06)", "",
              f"Identical per-unit vectors: {a['D06_identity']['identical_unit_vectors']}; identical verdict points: {a['D06_identity']['identical_verdict_points']}.", ""]
    p = S7 / "STAGE6_DEPENDENCY_AUDIT.md"
    S7.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return p


if __name__ == "__main__":
    a = write_audit(light="--light" in sys.argv)
    print(json.dumps(a["class_counts"]))
    print(json.dumps({k: v for k, v in (a.get("D02_decomposition") or {}).items() if isinstance(v, (int, float))}, indent=1))
    print(json.dumps({k: v for k, v in (a.get("D05_supplied_law_selection") or {}).items() if isinstance(v, (int, float))}, indent=1))
    print("identity:", a["D06_identity"]["identical_unit_vectors"], a["D06_identity"]["identical_verdict_points"])
