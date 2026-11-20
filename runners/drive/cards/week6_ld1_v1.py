"""LD1. Does failure shame more in company than alone? Claim T4.

DESIGN CHECK (LESSONS 2–5). The registered comparison uses identical prompts
for ashamed and sad. A missing secondary item cannot move that comparison.
The primary and raw-rating fits retain the noise and floor worlds in the
original qualification. A failed/separated equation or zero denominator has
no estimate. The bootstrap/replay caller supplies complete-source person
multiplicities and obtains one value per estimand, in a fixed roster.
"""
from dataclasses import dataclass, field

import numpy as np

from . import week6_ld12_common_v1 as core
from . import week6_lattice_source_v1 as source
from .week6_lattice_diary_v1 import InvalidFit


FIT_ERRORS = (InvalidFit, np.linalg.LinAlgError)
PAIRED = ("ashamed", "insecure", "anxious", "angry", "lonely")
CONTEXTS = {"company": ("alone", "in company"),
            "in_person": ("by phone or chat", "in person"),
            "one_partner": ("with multiple partners", "with one partner")}
# The source-specific codebook identity and literal category codes are
# supplied by the reviewed source binding. The primary needs no mode code.
MODE_BINDINGS = {member: dict(in_person=[1], remote=[2], labels=core.COMMUNICATION_LABELS,
                              partner_codes=list(core.PARTNER_COUNT_CODES), five_includes_more=True,
                              codebook_sha256=digest)
                 for member, digest in core.CODEBOOK_HASHES.items()}


@dataclass
class ContextModel:
    units: np.ndarray
    failure: np.ndarray
    comparison: np.ndarray
    responses: dict = field(default_factory=dict)


def _contexts(projection, member):
    v = projection.values
    company = v["company"]
    partner = v["no_interactionpartner"]
    mode = v["communication"]
    one_partner = np.full(len(company), np.nan)
    use = (company == 1) & np.isfinite(partner)
    one_partner[use] = (partner[use] == 1).astype(float)
    in_person = np.full(len(company), np.nan)
    binding = MODE_BINDINGS[member]
    in_person[(company == 1) & np.isin(mode, binding["remote"])] = 0.
    in_person[(company == 1) & np.isin(mode, binding["in_person"])] = 1.
    reasons = {}
    for diagnostic, key, column in (("in_person", "communication", in_person),
                                    ("one_partner", "no_interactionpartner", one_partner)):
        if projection.counts["invalid_optional_codes"][key]:
            column.fill(np.nan)
            reasons[diagnostic] = "values_outside_frozen_codebook"
    return {"company": company, "in_person": in_person, "one_partner": one_partner}, reasons


def prepare(member, path, pin, missing_tokens, guard):
    data = core.source_projection(member, path, pin, missing_tokens, guard, "LD1",
                                  extra=("communication", "no_interactionpartner"))
    feelings = source.feeling_names(member)
    for name in ("company", "failure", "communication", "no_interactionpartner", *feelings):
        data.values.setdefault(name, np.empty(0))
    contexts, field_reasons = _contexts(data, member)
    metadata = dict(card="LD1", member=member, source_sha256=pin["sha256"],
                    source_counts=data.counts, contexts={}, mode_binding=MODE_BINDINGS.get(member),
                    missing_source_items=[name for name in PAIRED if name not in feelings],
                    denominator_policy="Each feeling slope uses its own complete rows. Each comparison with sad fits both feelings on the same complete rows.",
                    ratios="Signed slope in the comparison over the reference. Denominators at or below 1e-12 in magnitude are undefined.",
                    success_occurrence="Failure equals seven minus success. Success occurrence is perfectly separated by design.",
                    conditional_sensitivity="No qualified conditional person-intercept estimator for the multivariate LD diary.",
                    limit="Failure and feeling share a prompt. Unequal answer noise across the two contexts can produce the registered contrast.")
    prepared = core.Prepared(data.people, metadata)
    models, outputs = [], {}
    prepared.panels.update(models=models, outputs=outputs)
    failure = data.values["failure"]
    for name, context in contexts.items():
        guard()
        ref_label, test_label = CONTEXTS[name]
        mask0 = np.isfinite(context) & np.isfinite(failure)
        arm = dict(reference=core.denominator(data.units, mask0 & (context == 0)),
                   comparison=core.denominator(data.units, mask0 & (context == 1)),
                   excluded=int((~mask0).sum()), role="primary" if name == "company" else "diagnostic")
        reason = field_reasons.get(name)
        if reason:
            arm["disposition"] = reason
        metadata["contexts"][name] = arm
        by_mask = {}

        def model_for(mask, items):
            token = mask.tobytes()
            if token not in by_mask:
                by_mask[token] = len(models)
                models.append(ContextModel(data.units[mask], failure[mask], context[mask]))
            idx = by_mask[token]
            for item in items:
                if item not in models[idx].responses:
                    models[idx].responses[item] = data.values[item][mask]
            return idx

        for feeling in feelings:
            mask = mask0 & np.isfinite(data.values[feeling])
            counts = core.denominator(data.units, mask)
            model = model_for(mask, (feeling,))
            for form in ("O", "L"):
                disposition = ("perfect_separation_by_construction"
                               if feeling == "success" and form == "O" else reason)
                for stat, label in (("reference", ref_label), ("comparison", test_label),
                                    ("delta", f"{test_label} minus {ref_label}"),
                                    ("ratio", f"{test_label} over {ref_label}")):
                    key = f"{name}.{form}.{feeling}.{stat}"
                    spec_counts = counts
                    if form == "L" and stat in ("reference", "comparison"):
                        spec_counts = core.denominator(data.units, mask & (context == int(stat == "comparison")))
                    core.metric(prepared, key, f"Failure and {feeling}, {label} ({form})",
                                spec_counts, disposition=disposition)
                    outputs[key] = ((model, form, feeling, stat),)
        for feeling in PAIRED:
            if feeling not in feelings:
                continue
            mask = mask0 & np.isfinite(data.values["sad"]) & np.isfinite(data.values[feeling])
            counts = core.denominator(data.units, mask)
            model = model_for(mask, (feeling, "sad"))
            for form in ("O", "L"):
                key = f"{name}.{form}.{feeling}_minus_sad"
                registered = (name, form, feeling) == ("company", "O", "ashamed")
                core.metric(prepared, key, f"Difference in the failure slope, {feeling} minus sad, {test_label} against {ref_label} ({form})",
                            counts, role="primary" if registered else "diagnostic",
                            bar=.10 if registered else None, disposition=reason)
                outputs[key] = ((model, form, feeling, "delta"), (model, form, "sad", "delta"))
    return prepared


def _store(dest, key, reference, comparison, delta):
    for name, value in (("reference", reference), ("comparison", comparison), ("delta", delta)):
        if value is not None:
            dest[(*key, name)] = float(value)
    if comparison is not None and reference is not None and abs(reference) > 1.e-12:
        dest[(*key, "ratio")] = float(comparison / reference)


def _model_outputs(model, idx, count, arithmetic, guard, values):
    within, logit, linear = arithmetic
    ids, f, ctx = model.units, model.failure, model.comparison
    w = count[ids]
    if len(ids) == 0 or w.sum() == 0:
        return
    design = None
    if np.unique(ctx[w > 0]).size == 2:
        try:
            fw, fm, _ = within(f, ids, w)
            z = fw[:, 0]
            design = np.column_stack((np.ones(len(ids)), ctx, z, ctx * z, fm[:, 0]))
        except FIT_ERRORS:
            pass
    raw = {}
    for group in (0, 1):
        mask = ctx == group
        if mask.any() and w[mask].sum() > 0:
            try:
                raw[group] = (mask, within(f[mask], ids[mask], w[mask])[0])
            except FIT_ERRORS:
                pass
    for feeling, y in model.responses.items():
        guard()
        if design is not None and feeling != "success":
            try:
                b = logit(design, y > 1, w)
                _store(values, (idx, "O", feeling), b[2], b[2] + b[3], b[3])
            except FIT_ERRORS:
                pass
        slopes = [None, None]
        for group, (mask, predictor) in raw.items():
            try:
                yw, _, _ = within(y[mask], ids[mask], w[mask])
                slopes[group] = linear(predictor, yw[:, 0], w[mask])[0]
            except FIT_ERRORS:
                pass
        _store(values, (idx, "L", feeling), *slopes, core.contrast(slopes[1], slopes[0]))


def evaluate(prepared, weights, guard, *, verify=False):
    guard()
    count = core.multiplicities(prepared.people, weights)
    arithmetic = core.arithmetic(verify)
    values = {}
    for idx, model in enumerate(prepared.panels["models"]):
        _model_outputs(model, idx, count, arithmetic, guard, values)
    result = {}
    for output, inputs in prepared.panels["outputs"].items():
        first = values.get(inputs[0])
        result[output] = first if len(inputs) == 1 else core.contrast(first, values.get(inputs[1]))
    core.record_point_dispositions(prepared, result, weights)
    return result
