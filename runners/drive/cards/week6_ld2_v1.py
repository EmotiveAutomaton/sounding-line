"""LD2. Who outranks whom when someone criticises me? Claim A3.

DESIGN CHECK (LESSONS 2–5). Freeze support and the rank coding on an
outcome-free projection. Literal repeats of whole people must reproduce the
weighted logistic and raw-rating fits. A missing secondary moderator, a
failed role check, and a singular outcome each retain their own disposition.
All six events and the three comparison feelings are fixed by the packet.
"""
import numpy as np

from . import week6_lattice_bindings_v1 as binding
from . import week6_lattice_diagnostics_v1 as diagnostics
from . import week6_ld12_common_v1 as core
from .week6_lattice_diary_v1 import InvalidFit


FEELINGS = diagnostics.OUTCOMES
EVENTS = binding.STATUS
MODERATORS = ("leadership", "selfesteem", "superior")
GROUPS = ("peers", "below", "above")
PRODUCT_COLUMNS = ("intercept", *EVENTS, "moderator", "criticism_product",
                   *("mean_" + name for name in EVENTS), "mean_moderator")
ROLE_COLUMNS = ("intercept", *EVENTS, "criticised_x_below", "criticised_x_above",
                "below", "above", *("mean_" + name for name in EVENTS))
RAW_PRODUCT_COLUMNS = (*EVENTS, "moderator", "criticism_product")
FIT_ERRORS = (InvalidFit, np.linalg.LinAlgError)


def _observed_gate(data, keep):
    if not keep.any():
        return dict(strata={name: dict(criticised_prompts=0, people=0)
                            for name in ("below", "above")}, support_passes=False,
                    coding_passes=False, inferentially_eligible=False,
                    lead_below_minus_above=None, other_codes={})
    return binding.role_support(data.units[keep],
                                *(data.values[k][keep] for k in
                                  ("partner_count", "role", "criticised", "leadership")))


def _panel(projection, keep, events, moderator=None, role=None):
    data = projection.values
    return dict(units=projection.units[keep], events=np.column_stack([data[x][keep] for x in events]),
                outcomes={name: data[name][keep] for name in FEELINGS},
                moderator=None if moderator is None else data[moderator][keep],
                role=None if role is None else role[keep])


def _register_product(p, name, counts, member):
    for form, names in (("O", PRODUCT_COLUMNS), ("L", RAW_PRODUCT_COLUMNS)):
        for feeling in FEELINGS:
            for column in names:
                core.metric(p, f"{name}.{form}.{feeling}.{column}",
                            f"{name} model, {feeling}, {column} coefficient ({form})", counts)
        registered = form == "O" and (name == "leadership" or
                                      (name == "superior" and member == "0057"))
        core.metric(p, f"{name}.{form}.anger_minus_fear",
                    f"Criticism by {name}, angry minus mean anxious, ashamed and insecure ({form})",
                    counts, role="primary" if registered else "diagnostic",
                    bar=.05 if registered else None)


def _register_roles(p, member, counts, strata, disposition):
    for feeling in FEELINGS:
        for column in ROLE_COLUMNS:
            core.metric(p, f"role.O.{feeling}.coef.{column}",
                        f"Role model, {feeling}, {column} coefficient", counts,
                        disposition=disposition)
        for group in GROUPS:
            for event in EVENTS:
                for form in ("O", "L"):
                    core.metric(p, f"role.{form}.{group}.{feeling}.{event}",
                                f"{group}, {feeling} slope for {event} ({form})",
                                counts if form == "O" else strata[group],
                                disposition=disposition)
    for form in ("O", "L"):
        for group in GROUPS:
            core.metric(p, f"role.{form}.{group}.anger_minus_fear",
                        f"{group}, criticism, anger minus the three fear-like feelings ({form})",
                        counts if form == "O" else strata[group], disposition=disposition)
        registered = member == "0057" and form == "O"
        core.metric(p, f"role.{form}.below_minus_above",
                    f"Difference of the criticism contrast for roles below and above ({form})",
                    counts, role="primary" if registered else "diagnostic",
                    bar=.40 if registered else None, disposition=disposition)


def prepare(member, path, pin, missing_tokens, guard):
    support = core.source_projection(member, path, pin, missing_tokens, guard, "LD2-support")
    keys = ("partner_count", "role", "criticised", "leadership")
    s = support.values
    complete = np.ones(len(support.units), dtype=bool)
    for key in keys:
        s.setdefault(key, np.empty(0))
        complete &= np.isfinite(s[key])
    gate = _observed_gate(support, complete)
    # No feeling has been materialised when this observed gate is adjudicated.
    guard()
    data = core.source_projection(member, path, pin, missing_tokens, guard, "LD2-product")
    if (support.people != data.people or not np.array_equal(support.units, data.units)
            or not np.array_equal(support.ordinals, data.ordinals)):
        raise ValueError("Support and product source populations differ")
    for name in (*EVENTS, *MODERATORS, *FEELINGS):
        data.values.setdefault(name, np.empty(0))
    if not np.array_equal(data.values["criticised"], s["criticised"], equal_nan=True):
        raise ValueError("Criticism changed between frozen reads")
    if not np.array_equal(data.values["leadership"], s["leadership"], equal_nan=True):
        raise ValueError("Leadership changed between frozen reads")
    metadata = dict(card="LD2", member=member, source_sha256=pin["sha256"],
                    source_counts=data.counts, observed_role_support=gate,
                    role_support_before_feelings=True,
                    complete_role_metadata=core.denominator(data.units, complete),
                    role_metadata_missing_rows=int((~complete).sum()),
                    role_after_complete_cases=None, panels={},
                    numerical_failures="Undefined estimates are retained per metric and draw.",
                    conditional_sensitivity="No qualified conditional person-intercept estimator for this multivariate diary panel.",
                    limits="Leadership, superiority, self-assurance and feelings share one prompt. Unequal answer noise can mimic moderation. Rank refers to the relationship.")
    p = core.Prepared(data.people, metadata)
    common = np.ones(len(data.units), dtype=bool)
    for key in (*EVENTS, *FEELINGS):
        common &= np.isfinite(data.values[key])
    for name in MODERATORS:
        keep = common & np.isfinite(data.values[name])
        counts = core.denominator(data.units, keep)
        p.metadata["panels"][name] = dict(**counts, excluded_incomplete=int((~keep).sum()))
        if keep.any():
            p.panels[name] = _panel(data, keep, EVENTS, moderator=name)
        _register_product(p, name, counts, member)

    empty = np.zeros(len(data.units), bool)
    keep = empty
    disposition = None
    if not gate["support_passes"]:
        disposition = "unsupported_before_outcomes"
    elif not gate["coding_passes"]:
        disposition = "role_codes_do_not_carry_rank"
    else:
        eligible = complete & (s["partner_count"] == 1) & np.isin(s["role"], diagnostics.SCORED_ROLES)
        keep = eligible & common
        after = _observed_gate(support, keep)
        p.metadata["role_after_complete_cases"] = after
        if not after["support_passes"]:
            disposition = "unsupported_after_complete_cases"
        elif not after["coding_passes"]:
            disposition = "role_codes_do_not_carry_rank_after_complete_cases"
        p.metadata["role_model_missing_rows"] = int((eligible & ~common).sum())
        if disposition is None:
            p.panels["role"] = _panel(data, keep, EVENTS, role=s["role"])
    groups = _groups(s["role"])
    strata = {group: core.denominator(data.units, keep & mask) for group, mask in groups.items()}
    counts = core.denominator(data.units, keep)
    p.metadata["panels"]["role"] = dict(**counts, strata=strata,
                                        disposition=disposition or "eligible")
    _register_roles(p, member, counts, strata, disposition)
    return p


def _groups(roles):
    return dict(peers=np.isin(roles, (3, 5, 6, 9)),
                below=np.isin(roles, (2, 7)), above=roles == 1)


def _product(name, panel, counts, arithmetic, out, guard):
    within, logit, linear = arithmetic
    ids, x, moderator = panel["units"], panel["events"], panel["moderator"]
    w = counts[ids]
    try:
        z, mean, _ = within(np.column_stack((x, moderator)), ids, w)
    except FIT_ERRORS:
        return
    interaction = z[:, EVENTS.index("criticised")] * z[:, -1]
    raw_design = np.column_stack((z, interaction))
    design = np.column_stack((np.ones(len(ids)), raw_design, mean))
    for feeling, y in panel["outcomes"].items():
        guard()
        try:
            coefficients = logit(design, y > 1, w)
            for column, value in zip(PRODUCT_COLUMNS, coefficients):
                out[f"{name}.O.{feeling}.{column}"] = float(value)
        except FIT_ERRORS:
            pass
        try:
            yw, _, _ = within(y, ids, w)
            coefficients = linear(raw_design, yw[:, 0], w)
            for column, value in zip(RAW_PRODUCT_COLUMNS, coefficients):
                out[f"{name}.L.{feeling}.{column}"] = float(value)
        except FIT_ERRORS:
            pass
    for form in ("O", "L"):
        out[f"{name}.{form}.anger_minus_fear"] = core.average_difference(
            [out[f"{name}.{form}.{feeling}.criticism_product"] for feeling in FEELINGS])


def _roles(panel, counts, arithmetic, out, guard):
    within, logit, linear = arithmetic
    units, x, roles = panel["units"], panel["events"], panel["role"]
    w = counts[units]
    groups = _groups(roles)
    try:
        z, means, _ = within(x, units, w)
        c = z[:, EVENTS.index("criticised")]
        design = np.column_stack((np.ones(len(units)), z, c * groups["below"],
                                  c * groups["above"], groups["below"], groups["above"], means))
    except FIT_ERRORS:
        design = None
    if design is not None:
        for feeling, y in panel["outcomes"].items():
            guard()
            try:
                values = dict(zip(ROLE_COLUMNS, logit(design, y > 1, w)))
            except FIT_ERRORS:
                continue
            for column, value in values.items():
                out[f"role.O.{feeling}.coef.{column}"] = float(value)
            for group in GROUPS:
                for event in EVENTS:
                    adjustment = values["criticised_x_" + group] if event == "criticised" and group != "peers" else 0.
                    out[f"role.O.{group}.{feeling}.{event}"] = float(values[event] + adjustment)
    # Analogous to LD1's raw diagnostic, each group's Form L uses that
    # group's own within-person scales and all six joint event predictors.
    for group, mask in groups.items():
        if not mask.any():
            continue
        try:
            design_l, _, _ = within(x[mask], units[mask], w[mask])
        except FIT_ERRORS:
            continue
        for feeling, y in panel["outcomes"].items():
            guard()
            try:
                yw, _, _ = within(y[mask], units[mask], w[mask])
                beta = linear(design_l, yw[:, 0], w[mask])
            except FIT_ERRORS:
                continue
            for event, value in zip(EVENTS, beta):
                out[f"role.L.{group}.{feeling}.{event}"] = float(value)
    for form in ("O", "L"):
        for group in GROUPS:
            out[f"role.{form}.{group}.anger_minus_fear"] = core.average_difference(
                [out[f"role.{form}.{group}.{feeling}.criticised"] for feeling in FEELINGS])
        out[f"role.{form}.below_minus_above"] = core.contrast(
            out[f"role.{form}.below.anger_minus_fear"], out[f"role.{form}.above.anger_minus_fear"])


def evaluate(prepared, weights, guard, *, verify=False):
    guard()
    counts = core.multiplicities(prepared.people, weights)
    out = dict.fromkeys(prepared.specs)
    arithmetic = core.arithmetic(verify)
    for name, panel in prepared.panels.items():
        if name == "role":
            _roles(panel, counts, arithmetic, out, guard)
        else:
            _product(name, panel, counts, arithmetic, out, guard)
    core.record_point_dispositions(prepared, out, weights)
    return out
