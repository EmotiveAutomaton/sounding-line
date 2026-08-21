"""Phase 2.3 shared process-record schema (Stage 0; design brief §6.2, §3.2, §11).

Every constructed Phase 2.3 case carries an external behavioral record in this schema.
A model's generated rationale or hidden chain of thought is never ground truth; only
recorded operations are. Three curator rulings are enforced in code rather than prose:

1. FAILURE TO NOTICE (brief §2.1): if the relevant feature was perceptually available,
   non-recognition is exactly ONE decision event at episode resolution; physical or
   perceptual inability to receive the feature is a separate exception and NEVER a
   decision event. Divided attention, exhaustion, absent expertise are context fields.
2. CONTRIBUTION IS A NETWORK (brief §3.2): proposal, recognition, selection, veto,
   integration, repair, surface realization, downstream leverage are separate per-actor
   relations. No author-share scalar exists; asking for one raises.
3. ANOMALY STATE IS MULTILABEL AND SEQUENTIAL (brief §11): access, awareness, origin,
   handling, recurrence, secondary goal, final status, and reader-model consequence are
   separate axes that may coexist. There is no single exclusive "mistake type" field.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

OPERATIONS = {
    "propose", "perceive", "notice", "select", "reject", "veto",
    "revise", "integrate", "repair", "conceal", "retain", "exploit",
    "realize_surface", "external_perturbation", "outline", "critique",
}

CONTRIBUTION_ROLES = (
    "proposal", "recognition", "selection", "veto",
    "integration", "repair", "surface_realization", "downstream_leverage",
)

ANOMALY_AXES: dict[str, set[str]] = {
    "perceptual_access": {"available", "blocked", "unknown"},
    "awareness": {"noticed", "not_noticed", "unknown"},
    "origin": {"planned", "unintended", "stochastic_or_physical", "unknown"},
    "handling": {"repair", "conceal", "compensate", "retain", "exploit", "none",
                 "unknown"},
    "recurrence": {"isolated", "repeated", "generalized", "unknown"},
    "secondary_goal": {"resource_conservation", "primary_goal_protection", "status",
                       "aesthetics", "compliance", "other", "unknown"},
    "final_status": {"removed", "locally_preserved", "integrated_downstream",
                     "unresolved", "unknown"},
    "reader_model": {"local_exception", "model_revision", "false_mistake", "unknown"},
}


class PerceptualAccessViolation(RuntimeError):
    """A non-recognition decision event was recorded where no perceptual access
    existed — the curator's §2.1 ruling forbids coding inability as a decision."""


class ContributionCollapse(RuntimeError):
    """Someone asked the network for an author-share scalar. It does not exist."""


@dataclass
class ProcessEvent:
    event_id: str
    order: int
    actor_id: str
    operation: str
    target: str = ""
    parent_event_ids: list[str] = field(default_factory=list)
    primary_goal_id: str | None = None
    secondary_goal_candidates: list[str] = field(default_factory=list)
    constraint_ids: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)     # shown or available
    perceptual_access: bool | None = None                     # only anomaly-relevant
    noticed: bool | None = None                               # only anomaly-relevant
    visible_in_final: str = "unknown"                         # yes / partial / no / unknown
    ground_truth_source: str = "construction"
    payload: dict = field(default_factory=dict)               # intermediates, verbatim

    def validate(self) -> None:
        if self.operation not in OPERATIONS:
            raise ValueError(f"operation {self.operation!r} outside the recorded "
                             f"vocabulary")
        if self.operation == "notice" and self.perceptual_access is False:
            raise PerceptualAccessViolation(
                "a notice event with perceptual_access=False codes inability as a "
                "decision; record the blockage as context, not as an event")
        if self.visible_in_final not in ("yes", "partial", "no", "unknown"):
            raise ValueError("visible_in_final out of vocabulary")


@dataclass
class ProcessCase:
    case_id: str
    lineage_id: str
    domain: str
    medium: str
    brief_id: str
    declared_context: dict
    participants: dict                       # actor_id -> participant_type
    route_family: str                        # the candidate process family label
    events: list[ProcessEvent] = field(default_factory=list)
    artifact_final: str = ""
    artifact_versions: list[str] = field(default_factory=list)
    exact_equivalence_group: str | None = None
    near_equivalence_group: str | None = None
    split: str = "discovery"
    construction_seed: int | None = None
    context_fields: dict = field(default_factory=dict)        # exhaustion, deadline, ...

    def validate(self) -> None:
        ids = [e.event_id for e in self.events]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate event_ids in one case")
        known = set(ids)
        for e in self.events:
            e.validate()
            for p in e.parent_event_ids:
                if p not in known:
                    raise ValueError(f"event {e.event_id} parents unknown event {p!r}")
        # ruling §2.1: at most one non-recognition decision event per case at episode
        # resolution, and never where access was blocked
        non_rec = [e for e in self.events if e.noticed is False]
        if len(non_rec) > 1:
            raise ValueError("more than one non-recognition event: the ruling grants "
                             "exactly one decision at episode resolution")
        for e in non_rec:
            if e.perceptual_access is False:
                raise PerceptualAccessViolation(
                    f"event {e.event_id}: non-recognition recorded without access")

    def to_dict(self) -> dict:
        self.validate()
        d = asdict(self)
        return d


@dataclass
class ContributionNetwork:
    """Per-actor, per-role relations. Roles never sum (brief §3.2)."""
    case_id: str
    relations: dict = field(default_factory=dict)   # actor_id -> {role: value}

    def validate(self) -> None:
        for actor, roles in self.relations.items():
            for r in roles:
                if r not in CONTRIBUTION_ROLES:
                    raise ValueError(f"role {r!r} outside the network vocabulary "
                                     f"(actor {actor})")

    def author_share(self, *_args, **_kw):
        raise ContributionCollapse(
            "no contribution ratio may be computed by counting recovered events as "
            "exchangeable units (theory errata; brief §3.2)")


@dataclass
class AnomalyTrajectory:
    """Multilabel, sequential anomaly state (brief §11). Axes coexist; none is 'the'
    mistake type."""
    anomaly_id: str
    case_id: str
    axes: dict = field(default_factory=dict)        # axis -> value
    event_ids: list[str] = field(default_factory=list)

    def validate(self) -> None:
        for axis, value in self.axes.items():
            if axis not in ANOMALY_AXES:
                raise ValueError(f"unknown anomaly axis {axis!r}")
            if value not in ANOMALY_AXES[axis]:
                raise ValueError(f"axis {axis!r} value {value!r} out of vocabulary")
        # coherence of the §2.1 ruling across axes
        if (self.axes.get("perceptual_access") == "blocked"
                and self.axes.get("awareness") == "not_noticed"):
            raise PerceptualAccessViolation(
                "blocked access with a not-noticed awareness label codes inability as "
                "non-recognition; awareness is 'unknown' when access is blocked")
