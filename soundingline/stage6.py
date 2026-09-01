"""Stage 6 shared schema and bookkeeping (brief: docs/design/PHASE_2_4_STAGE_6_CONTEXT.md).

Everything the 104 cards and 24 attacks share that is not a model call, built ON the
Stage-4/5 machinery (soundingline/s4.py, soundingline/stage5.py) rather than beside it:
the run contract with the ONE immutable 168-hour clock (started at the discarded pilot,
surviving restarts; §11.1), the lineage ledger with the four lanes plus the attack lane,
the queue manifest over the eight trunks and the attack matrix, the packet guard (one
curator-facing file, refused before the deadline; §11.1), the registries (§12), and the
Stage-6 additions: the versioned `maker_state` object (§4.2) with its eight realization
gates (§4.3), the architecture codes (§6), the compute-budget ledger fields (I07), and
the understanding criterion's bands (§10.1).

Stage 1-5 code and results are immutable; this module only subclasses and moves paths.
The run-until-empty ruling (2026-08-28) is carried as: the 168-hour deadline is a REAL
stop for admitting new work (unlike Stage 5's accounting-only 24 hours, §11.1 makes the
window the contract), but the queue inside the window runs continuously with no idle;
exhaustion before hour 156 writes SHORT_RUN.json with the honest cause (§11.3).
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from soundingline import s4 as _s4
from soundingline.s4 import (EXEC_STATES, OUTCOMES, PURSUIT, WARRANT,              # noqa: F401
                             ClaimLedger, ContractError, FreshnessViolation, Lineages,
                             Manifest, PacketGuard, RealizationError, RunContract,
                             SplitViolation, aggregate_equal, append_jsonl, canonical,
                             check_marker, classify_outcome, code_hash, completion_marker,
                             coverage, expand_expected_cells, now_iso, read_json,
                             read_jsonl, sha256_file, sha256_text, validate_expected,
                             write_json)
from soundingline.stage5 import (OUTCOMES5, calibration_slope, ece,                # noqa: F401
                                 selective_risk_coverage)

__all__ = ['EXEC_STATES', 'OUTCOMES', 'PURSUIT', 'WARRANT', 'ClaimLedger', 'ContractError',
           'FreshnessViolation', 'Lineages', 'Manifest', 'PacketGuard', 'RealizationError',
           'RunContract', 'SplitViolation', 'aggregate_equal', 'append_jsonl', 'canonical',
           'check_marker', 'classify_outcome', 'code_hash', 'completion_marker', 'coverage',
           'expand_expected_cells', 'now_iso', 'read_json', 'read_jsonl', 'sha256_file',
           'sha256_text', 'validate_expected', 'write_json', 'OUTCOMES5', 'ece',
           'calibration_slope', 'selective_risk_coverage']

REPO = Path(__file__).resolve().parents[1]
STAGE = os.environ.get("S6_STAGE", "phase_2_4_stage_6")
S6 = Path(os.environ["S6_ROOT"]) if os.environ.get("S6_ROOT") else REPO / "results" / STAGE
CONTRACT_VERSION = "6.0.0"
RUN_HOURS = float(os.environ.get("S6_RUN_HOURS", "168"))
CLOSURE_HOUR = float(os.environ.get("S6_CLOSURE_HOUR", "144"))   # confirmation freeze (§10.3)
FLOOR_HOUR = 156.0                                               # a run exhausting earlier is SHORT (§11.3)
SMOKE = bool(os.environ.get("S6_SMOKE"))

SPLITS = ("pilot", "discovery", "transfer", "confirmation", "attack")
_s4.SPLITS = SPLITS

# ── the card inventory (§8): eight trunks, 104 mandatory cards ────────────────────────
TRUNKS = {"I": 10, "M": 16, "C": 12, "A": 14, "V": 14, "F": 12, "P": 12, "T": 10, "B": 4}
CARDS = [f"{t}{i:02d}" for t, n in TRUNKS.items() for i in range(1, n + 1)]
assert len(CARDS) == 104, len(CARDS)
ATTACKS = [f"X{i:02d}" for i in range(1, 25)]
TRACK_OF = {c: {"I": "integrity", "M": "realization", "C": "control", "A": "history",
                "V": "value", "F": "foraging", "P": "prospective", "T": "records",
                "B": "closure"}[c[0]] for c in CARDS}
TRACK_OF.update({a: "attack" for a in ATTACKS})

# ── the nine architecture arms (§6) ───────────────────────────────────────────────────
ARCHITECTURES = ("D", "L", "LD", "TT", "GS", "EX", "AD", "CR", "OR")
ARCH_NAMES = {"D": "direct monolithic reader", "L": "label-only augmented inverse planning",
              "LD": "label plus fixed definition", "TT": "free-language weighted particles",
              "GS": "grammar-constrained semantic state", "EX": "synthesized executable maker model",
              "AD": "adaptive structure expansion", "CR": "Sounding contextual realization",
              "OR": "exact/oracle structured state (ceiling, never a competitor)"}

OUTCOMES6 = OUTCOMES5   # the Stage-5 bands are exhaustive and carry over unchanged

# §10.1 default positive floor: the fraction of the oracle-minus-best-cheap-baseline
# log-score gap an architecture must close; frozen before model data, void if the gap dies
ORACLE_GAP_FLOOR = 0.20

SEED_CONTRACT = {
    "stage": STAGE,
    "reviewed_commit": "b31ffda",
    "brief": "docs/design/PHASE_2_4_STAGE_6_CONTEXT.md",
    "run_duration_hours": 168,
    "duration_basis": "elapsed_wall_clock_from_pilot_start",
    "continuous_run": True,
    "stop_at_deadline": True,                        # §11.1: the window IS the contract
    "deadline_is_accounting_only": False,
    "run_until_queue_empty": True,                   # inside the window: no idle
    "short_run_floor_hour": FLOOR_HOUR,
    "deadline_persists_on_resume": True,
    "curator_packet_policy": "final_only_after_deadline",
    "early_curator_packets": False,
    "confirmation_freeze_hour": CLOSURE_HOUR,
    "max_substantive_confirmations": 2,
    "max_cpu_workers_while_ghost_live": 2,           # §11.5
    "cards": list(CARDS),
    "attacks": list(ATTACKS),
    "architectures": list(ARCHITECTURES),
    "lanes": list(SPLITS),
    "oracle_gap_floor": ORACLE_GAP_FLOOR,
    "oracle_bypass_is_end_to_end_success": False,
    "pilot_outputs_promotable": False,
    "late_split_of_old_data_is_confirmation": False,
    "cloud_or_paid_api_authorized": False,
    "agent_delegation_authorized": False,
    "human_participants_authorized": False,
    "ghost_v14_boundary": "read-only status/coverage; landed rulers only via the B03 bridge ledger; no writes, kills, or V15",
    "claim_class": "model-reader engineering and bounded recorded-process inference",
}


# ── the Stage-6 records: same classes, Stage-6 paths ──────────────────────────────────

class RunContract6(RunContract):
    PATH = S6 / "RUN_CONTRACT.json"

    @classmethod
    def create(cls, extra: dict | None = None, path: Path | None = None) -> "RunContract6":
        p = path or cls.PATH
        if p.exists():
            return cls.load(p)
        data = dict(SEED_CONTRACT)
        data.update({"contract_version": CONTRACT_VERSION, "created_at": now_iso(),
                     "frozen": {}, "lost_time": [], "run_hours": RUN_HOURS,
                     "closure_hour": CLOSURE_HOUR,
                     "gear": "second, continuous through the week (his order 2026-08-30)"})
        if extra:
            data.update(extra)
        c = cls(data, p)
        c.save()
        return c

    @classmethod
    def load(cls, path: Path | None = None) -> "RunContract6 | None":
        p = path or cls.PATH
        if not p.exists():
            return None
        return cls(read_json(p), p)


class Lineages6(Lineages):
    PATH = S6 / "SOURCE_LINEAGES.json"


class Manifest6(Manifest):
    PATH = S6 / "QUEUE_MANIFEST.json"

    def set_outcome(self, cell_id: str, outcome: str, detail=None) -> None:
        assert outcome in OUTCOMES6, outcome
        self.cells[cell_id]["outcome"] = outcome
        if detail is not None:
            self.cells[cell_id]["detail"] = detail
        self.save()

    def add(self, cell_id: str, card: str, depends_on: list[str], produces: str,
            est_minutes: float, gpu: bool, why: str) -> None:
        if cell_id in self.cells:
            return
        self.cells[cell_id] = {
            "cell_id": cell_id, "card": card, "track": TRACK_OF[card],
            "exec_state": "PLANNED", "outcome": "NOT_RUN", "depends_on": depends_on,
            "produces": produces, "est_minutes": est_minutes, "gpu": gpu, "why": why,
            "reason": None, "budget_charged_min": 0.0, "gpu_lock_min": 0.0,
            "attempts": 0, "started_at": None, "finished_at": None, "detail": None}
        self.save()


class ClaimLedger6(ClaimLedger):
    PATH = S6 / "CLAIM_LEDGER.json"


def card_dir(card: str) -> Path:
    p = S6 / card
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_packet(text: str, contract: RunContract, exhausted: bool) -> Path:
    """The one curator-facing file (§11.1); any other packet path is refused, and the
    scheduler additionally refuses this one before hour 168 plus validation."""
    return _s4.write_packet(text, contract, exhausted, path=S6 / "CURATOR_PACKET_FINAL.md")


def refuse_packet_path(path: Path) -> None:
    if Path(path).name != "CURATOR_PACKET_FINAL.md" or Path(path).parent != S6:
        raise PacketGuard(f"{path} is not the one permitted curator packet path")


# ── the maker_state object (§4.2) and its realization gates (§4.3) ────────────────────

MAKER_STATE_FIELDS = (
    "proposal_id", "artifact_context", "episode_goal", "control_state",
    "maintained_intentions", "process_model", "expertise_state", "selection_history",
    "standing_tendencies", "source_model", "evidence_scope", "decision_likelihoods",
    "counterfactual_predictions", "stop_model", "uncertainty")
# fields that may not alias one another (test 8: separate representation of the seven)
DISTINCT_FIELDS = ("episode_goal", "maintained_intentions", "control_state",
                   "selection_history", "expertise_state", "artifact_context",
                   "standing_tendencies")
STATE_VERSION = "s6-maker-state-1.0"


class MakerStateError(ValueError):
    pass


def maker_state(**fields) -> dict:
    """One versioned realized state. Required: proposal_id, evidence_scope,
    decision_likelihoods (dict target -> normalized distribution), stop_model
    (dict with 'p_stop' in [0,1] per opportunity or a scalar), uncertainty (dict with
    'posterior_weight' and 'abstain'). Optional fields must use the declared names;
    unknown names raise. Distributions are normalized here; an empty one raises."""
    out = {"version": STATE_VERSION}
    for k, v in fields.items():
        if k not in MAKER_STATE_FIELDS:
            raise MakerStateError(f"unknown maker_state field {k}")
        out[k] = v
    for req in ("proposal_id", "evidence_scope", "decision_likelihoods", "stop_model", "uncertainty"):
        if req not in out:
            raise MakerStateError(f"maker_state missing {req}")
    dl = out["decision_likelihoods"]
    if not isinstance(dl, dict) or not dl:
        raise MakerStateError("decision_likelihoods empty")
    norm = {}
    for target, dist in dl.items():
        if not isinstance(dist, dict) or not dist:
            raise MakerStateError(f"decision_likelihoods[{target}] empty")
        tot = float(sum(dist.values()))
        if tot <= 0 or any(p < 0 for p in dist.values()):
            raise MakerStateError(f"decision_likelihoods[{target}] not a distribution")
        norm[target] = {k: float(p) / tot for k, p in dist.items()}
    out["decision_likelihoods"] = norm
    u = out["uncertainty"]
    if not isinstance(u, dict) or "posterior_weight" not in u or "abstain" not in u:
        raise MakerStateError("uncertainty needs posterior_weight and abstain")
    return out


def check_state_fields_distinct(state: dict) -> None:
    """Test 8: the seven representational fields may not share one mutable object; an
    aggregation that writes one into another is a schema violation."""
    seen = {}
    for name in DISTINCT_FIELDS:
        v = state.get(name)
        if v is None or isinstance(v, (str, int, float, bool, tuple)):
            continue
        ident = id(v)
        if ident in seen:
            raise MakerStateError(f"{name} shares its object with {seen[ident]}")
        seen[ident] = name


def state_log_score(state: dict, target: str, truth: str, floor: float = 1e-9) -> float | None:
    dist = (state.get("decision_likelihoods") or {}).get(target)
    if not dist:
        return None
    return math.log(max(float(dist.get(truth, 0.0)), floor))


REALIZATION_GATES = ("parses", "normalized", "predicts_withheld", "counterfactual_named",
                     "context_sensitive", "paraphrase_stable", "exposes_uncertainty",
                     "evidence_receipt")


def realization_report(state: dict | None, *, parse_error: str | None = None,
                       counterfactual_named: bool = False, context_sensitive: bool | None = None,
                       paraphrase_stable: bool | None = None) -> dict:
    """The eight-gate realization record (§4.3). Gates 1, 2, 3, 7, 8 are checked from the
    state object here; 4 is the caller's flag (a named counterfactual its nearest rival
    can dispute); 5 and 6 are batch properties (M14, M15) recorded when measured, None
    until then. A state failing any checked gate is an unrealized proposal."""
    if state is None:
        return {"realized": False, "gates": {g: False for g in REALIZATION_GATES},
                "parse_error": parse_error or "no state emitted"}
    gates = {"parses": True, "normalized": True,
             "predicts_withheld": bool(state.get("decision_likelihoods")),
             "counterfactual_named": bool(counterfactual_named or state.get("counterfactual_predictions")),
             "context_sensitive": context_sensitive,
             "paraphrase_stable": paraphrase_stable,
             "exposes_uncertainty": isinstance(state.get("uncertainty"), dict),
             "evidence_receipt": bool((state.get("evidence_scope") or {}).get("observed"))}
    hard = [g for g in ("parses", "normalized", "predicts_withheld", "counterfactual_named",
                        "exposes_uncertainty", "evidence_receipt") if not gates[g]]
    return {"realized": not hard, "gates": gates, "failed": hard, "parse_error": None}


# ── the compute-budget ledger (§6, I07) ───────────────────────────────────────────────

def budget_row(model_calls: int = 0, tokens_in: int = 0, tokens_out: int = 0,
               forward_passes: int = 0, wall_s: float = 0.0, peak_mem_mb: float | None = None,
               solver_enumerations: int = 0) -> dict:
    return {"model_calls": model_calls, "tokens_in": tokens_in, "tokens_out": tokens_out,
            "forward_passes": forward_passes, "wall_s": round(wall_s, 3),
            "peak_mem_mb": peak_mem_mb, "solver_enumerations": solver_enumerations}


def add_budget(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if v is None:
            continue
        out[k] = (out.get(k) or 0) + v if k != "peak_mem_mb" else max(out.get(k) or 0, v)
    return out


# ── registries (§12) ──────────────────────────────────────────────────────────────────

REGISTRIES = ("STRUCTURAL_LOCK", "WORKLOAD_LOCK", "SCIENTIFIC_LOCK", "EXPECTED_CELLS",
              "ARCHITECTURES", "CONSTRUCTION_IDENTITIES", "SOURCE_LINEAGES_AUDIT",
              "SPLIT_RECEIPT", "ATTACK_MATRIX", "RUNTIME", "COVERAGE", "COMPLETION",
              "CONFIRMATION_REGISTRY", "PREPARED", "SCHEDULER_STATUS", "SHORT_RUN",
              "PILOT", "GHOST_BRIDGE", "CORPUS_DISPOSITIONS", "COEXISTENCE")


def write_registry(name: str, obj) -> Path:
    assert name in REGISTRIES, name
    S6.mkdir(parents=True, exist_ok=True)
    p = S6 / f"{name}.json"
    write_json(p, obj)
    return p


def read_registry(name: str):
    p = S6 / f"{name}.json"
    return read_json(p) if p.exists() else None


def workload_locked() -> bool:
    w = read_registry("WORKLOAD_LOCK")
    return bool(w and w.get("tier"))


def scientific_locked() -> bool:
    w = read_registry("SCIENTIFIC_LOCK")
    return bool(w and w.get("locked"))


# ── the Ghost V14 boundary (§2.2, §11.5): read-only ───────────────────────────────────

GHOST_ROOT = (REPO.parent.parent / "AI and Intentionality" / "Ghost Scale Simulation"
              / "ghost-scale-sim")
GHOST_V14 = GHOST_ROOT / "results" / "v14"


def ghost_status(max_age_min: float = 30.0) -> dict:
    """The coexistence governor's read (read-only): RUNNER_STATUS.json's heartbeat and
    stage. `live` is True when the heartbeat is fresh; the CPU cap for Sounding is 2
    whenever `live` (§11.5; COEXISTENCE samples are not a spare-capacity signal)."""
    import datetime as _dt                                                        # noqa: PLC0415
    p = GHOST_V14 / "RUNNER_STATUS.json"
    out = {"path": str(p), "exists": p.exists(), "live": False, "heartbeat": None, "stage": None}
    if not p.exists():
        return out
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        out["error"] = repr(e)
        out["live"] = True                        # unreadable status is treated as live (fail safe)
        return out
    out["heartbeat"] = d.get("heartbeat")
    out["stage"] = d.get("stage")
    out["pid"] = d.get("pid")
    try:
        hb = _dt.datetime.fromisoformat(str(d.get("heartbeat")))
        age_min = (_dt.datetime.now() - hb).total_seconds() / 60
        out["age_min"] = round(age_min, 1)
        out["live"] = age_min <= max_age_min
    except (TypeError, ValueError):
        out["live"] = True                        # unparseable heartbeat: assume live
    return out


def ghost_coverage() -> dict | None:
    p = GHOST_V14 / "COVERAGE.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ── prospective scores (§14.1) ────────────────────────────────────────────────────────

def brier(dist: dict, truth: str) -> float:
    """Multiclass Brier score of a normalized distribution against the truth."""
    s = 0.0
    keys = set(dist) | {truth}
    for k in keys:
        p = float(dist.get(k, 0.0))
        s += (p - (1.0 if k == truth else 0.0)) ** 2
    return s


def hazard_log_score(p_stop_seq: list[float], stopped_at: int | None, floor: float = 1e-9) -> float:
    """Discrete-time stopping log score: the summed log likelihood of the observed
    continue/stop sequence under per-opportunity stop probabilities. `stopped_at` is the
    index of the opportunity at which the maker stopped (None = censored: continued past
    the last scored opportunity, each contributing its continue term; §14.1)."""
    total = 0.0
    for i, p in enumerate(p_stop_seq):
        p = min(max(float(p), floor), 1 - floor)
        if stopped_at is not None and i == stopped_at:
            return total + math.log(p)
        total += math.log(1 - p)
        if stopped_at is not None and i > stopped_at:
            break
    return total


def span_score(pred: dict, truth: dict) -> float:
    """Hierarchical proper score for next-edit location (P02, M11): the log probability
    mass the prediction puts on the true section, plus, within it, on the true slot.
    pred: {"sections": {name: p}, "slots": {section: {slot: p}}}."""
    sec = truth.get("section")
    slot = truth.get("slot")
    ps = max(float((pred.get("sections") or {}).get(sec, 0.0)), 1e-9)
    total = math.log(ps)
    slots = (pred.get("slots") or {}).get(sec) or {}
    if slot is not None and slots:
        total += math.log(max(float(slots.get(slot, 0.0)), 1e-9))
    return total


def oracle_gap_closed(arch_ls: float, cheap_ls: float, oracle_ls: float) -> float | None:
    """The fraction of the oracle-minus-cheap log-score gap an architecture closes
    (§10.1). None when the gap is nontrivially absent (oracle no better than cheap by
    at least 0.05 nats), in which case the card is VOID rather than re-thresholded."""
    gap = oracle_ls - cheap_ls
    if gap < 0.05:
        return None
    return (arch_ls - cheap_ls) / gap
