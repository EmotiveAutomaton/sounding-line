"""G160 — the trajectory reconstruction profile (Phase 2.2B; brief §9) with structural
interface guards.

The typed schema every Phase 2.2 reading writes. Two rules are enforced in code rather
than prose: (1) every field belongs to a declared input interface, and a reading emitted
for the final-artifact interface (I1) may not carry any field whose interface requires
paired-delta (I2) or process records (I3) — the leak the contract's §3b and the 2.2
pre-mortem item 4 name; (2) the claim boundary is mandatory: no reading exists without
its four boundary statements, so "human-coherent route supported" can never silently
drift into a provenance or causal claim.

Fields follow the brief §9 structure. Names are agent-owned; distinctions are not
discarded. Provenance and reconstruction remain separate outputs forever.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum


class Interface(str, Enum):
    I1_FINAL_ARTIFACT = "I1"
    I2_PAIRED_DELTA = "I2"
    I3_PROCESS_AWARE = "I3"


# which interface each profile section REQUIRES at inference time. A section may appear
# in a reading only when the reading's interface grants at least its requirement
# (I1 < I2 < I3 in access order).
_ACCESS_ORDER = {Interface.I1_FINAL_ARTIFACT: 0, Interface.I2_PAIRED_DELTA: 1,
                 Interface.I3_PROCESS_AWARE: 2}

SECTION_REQUIRES: dict[str, Interface] = {
    "proximal": Interface.I1_FINAL_ARTIFACT,
    "trajectory": Interface.I1_FINAL_ARTIFACT,
    "historical": Interface.I1_FINAL_ARTIFACT,
    "anomaly": Interface.I1_FINAL_ARTIFACT,
    "anomaly_handling_observed": Interface.I2_PAIRED_DELTA,   # repair/concealment needs deltas
    "realization_ground_truth": Interface.I3_PROCESS_AWARE,   # verified labels are process facts
    # Phase 2.3 sections (design brief §3.4). The reader's own constructions are I1;
    # anything read off records is I3 by definition.
    "reader_enactable_route": Interface.I1_FINAL_ARTIFACT,    # the reader's OWN route,
    #   always reported separately from any historical-process claim (brief §3.1)
    "contribution_hypothesis": Interface.I1_FINAL_ARTIFACT,   # inferred network, hypothesis
    "contribution_network_observed": Interface.I3_PROCESS_AWARE,  # from logs only
}


class HandlingState(str, Enum):
    NO_ANOMALY = "no_anomaly"
    UNEXPLAINED_ORDER = "unexplained_order"
    APPARENT_ERROR = "apparent_error"
    CONFIRMED_ERROR = "confirmed_error"
    REPAIRED = "repaired"
    CONCEALED = "concealed"
    UNNOTICED = "unnoticed"
    REPEATED = "repeated"
    FALSE_MISTAKE = "false_mistake"
    UNKNOWN = "unknown"


class Realization(str, Enum):
    ASSIGNED = "assigned"
    REALIZED = "realized"
    UNREALIZED = "unrealized"
    SPONTANEOUS = "spontaneous"
    AMBIGUOUS = "ambiguous"


@dataclass
class RankedCandidate:
    label: str
    rank: int
    evidence_spans: list[str] = field(default_factory=list)
    confidence: float | None = None


@dataclass
class ClaimBoundary:
    """Mandatory. The four statements every reading carries (brief §9)."""
    human_coherent_route_supported: bool
    process_correspondence: str      # "supported" | "unavailable" | "contradicted"
    provenance: str                  # "known_from_records" | "not_inferred"
    causal_process: str = "unknown"  # fixed unless a process record proves otherwise

    def validate(self) -> None:
        if self.provenance not in ("known_from_records", "not_inferred"):
            raise ValueError("provenance is either known from records or not inferred; "
                             "a reading never infers it")
        if self.process_correspondence not in ("supported", "unavailable", "contradicted"):
            raise ValueError("process_correspondence out of vocabulary")


@dataclass
class ReadingProfile:
    # reading identity
    artifact_id: str
    reader_id: str
    reader_config: dict
    interface: Interface
    declared_context: dict
    candidate_family: str
    baseline_family: str
    claim_boundary: ClaimBoundary

    # proximal reconstruction (I1)
    proximal: list[RankedCandidate] = field(default_factory=list)
    abstained: bool = False
    abstention_reason: str | None = None

    # trajectory reconstruction (I1)
    trajectory: dict = field(default_factory=dict)
    # keys used: route_candidates, constraints_active, constraints_forced_by_context,
    # expertise_assumptions, alternatives_suppressed

    # historical traces (I1; lifetime formation history is never identified)
    historical: dict = field(default_factory=dict)

    # anomaly profile (I1 for presence; I2 for observed handling)
    anomaly: list[dict] = field(default_factory=list)
    anomaly_handling_observed: list[dict] = field(default_factory=list)

    # realization (labels are process facts: I3)
    realization_ground_truth: list[dict] = field(default_factory=list)

    # Phase 2.3: the reader-enactable route (I1; never a historical claim) and the
    # contribution network in both its hypothesis (I1) and observed (I3) forms
    reader_enactable_route: dict = field(default_factory=dict)
    contribution_hypothesis: dict = field(default_factory=dict)
    contribution_network_observed: dict = field(default_factory=dict)

    # validation status
    validation: dict = field(default_factory=dict)

    def validate(self) -> None:
        """The interface guard: raise on any section whose requirement exceeds the
        reading's declared interface, and on a missing/invalid claim boundary."""
        self.claim_boundary.validate()
        mine = _ACCESS_ORDER[self.interface]
        for section, req in SECTION_REQUIRES.items():
            content = getattr(self, section, None)
            if content and _ACCESS_ORDER[req] > mine:
                raise InterfaceLeak(
                    f"section {section!r} requires {req.value} but this reading is "
                    f"declared {self.interface.value}: a process-informed field may "
                    f"never appear in a lower interface's output")
        if self.historical and not self.historical.get(
                "lifetime_history_not_identified", False):
            raise ValueError("historical traces must carry the explicit statement that "
                             "lifetime formation history is not identified")

    def to_dict(self) -> dict:
        self.validate()
        d = asdict(self)
        d["interface"] = self.interface.value
        return d


class InterfaceLeak(RuntimeError):
    """A field trained or populated with process metadata reached a lower interface."""
