"""Stage 5 shared schema and bookkeeping (brief: docs/design/PHASE_2_4_STAGE_5_CONTEXT.md,
filed there once implemented; at the repository root while the build runs).

Everything the twenty-nine cards share that is not a model call, built ON the Stage-4
machinery (soundingline/s4.py) rather than beside it: the run contract with its persisted
start and accounting deadline, the lineage ledger (lock-held, content-hashed, with the
brief's four lanes), the queue manifest, completion markers, exhaustive outcome bands, the
order-invariant aggregation, the packet guard, plus what Stage 5 adds: the constrained
latent record with an explicit `unknown` and evidence-span references (§4.1), the
construction-identity, route-information, workload-lock, completion, and confirmation
registries (§9), and the run-until-empty rule (his standing ruling 2026-08-28: the brief's
24-hour window is accounting, the queue runs to its natural end).

Stage 4's module is not edited; Stage 4 is a closed record. The subclasses here only move
the paths and the card registry.
"""

from __future__ import annotations

import os
from pathlib import Path

from soundingline import s4 as _s4
from soundingline.s4 import (ACCESS_LEVELS, EXEC_STATES, OUTCOMES, PURSUIT, WARRANT,   # noqa: F401
                             ClaimLedger, ContractError, FreshnessViolation, Lineages,
                             Manifest, PacketGuard, RealizationError, RunContract,
                             SplitViolation, aggregate_equal, append_jsonl, canonical,
                             check_marker, classify_outcome, code_hash, completion_marker,
                             coverage, expand_expected_cells, now_iso, packet_allowed,
                             read_json, read_jsonl, require_realized_truth, sha256_file,
                             sha256_text, validate_expected, validate_run_label,
                             verdict_gate, write_json)

REPO = Path(__file__).resolve().parents[1]
STAGE = os.environ.get("S5_STAGE", "phase_2_4_stage_5")   # the second contract runs as phase_2_4_stage_5r
S5 = Path(os.environ["S5_ROOT"]) if os.environ.get("S5_ROOT") else REPO / "results" / STAGE
CONTRACT_VERSION = "5.0.0"
RUN_HOURS = float(os.environ.get("S5_RUN_HOURS", "24"))
CLOSURE_HOUR = float(os.environ.get("S5_CLOSURE_HOUR", "20"))
SMOKE = bool(os.environ.get("S5_SMOKE"))

# the brief's four lanes (§5); the Stage-4 ledger knew three, so its module-level tuple is
# extended here (the allocator asserts against it by reference)
SPLITS = ("pilot", "discovery", "transfer", "confirmation")
_s4.SPLITS = SPLITS

CARDS = ["I01", "I02", "I03", "I04",
         "B01", "B02", "B03",
         "J01", "J02", "J03", "J04", "J05",
         "A01", "A02", "A03", "A04", "A05",
         "R01", "R02", "R03", "R04",
         "P01", "P02", "P03",
         "F01", "F02", "F03",
         "C01", "C02"]
TRACK_OF = {c: {"I": "integrity", "B": "bridge", "J": "joint", "A": "appraisal",
                "R": "route", "P": "process", "F": "foraging", "C": "confirmation"}[c[0]]
            for c in CARDS}
ALLOCATION_HOURS = {"integrity": 2.0, "bridge": 3.0, "joint": 4.5, "appraisal": 4.5,
                    "route": 2.0, "process": 1.5, "foraging": 2.0, "confirmation": 4.5}
DEFAULT_THRESHOLDS = {"log_score_nats": 0.03, "balanced_accuracy": 0.05,
                      "route_information_floor_nats": 0.05, "true_advice_loss_pp": 0.03}

SEED_CONTRACT = {
    "stage": STAGE,
    "reviewed_commit": "8230a933fab805a4ee39c256f1e189fe46314dfe",
    "brief": "PHASE_2_4_STAGE_5_CONTEXT.md",
    "run_duration_hours": 24,
    "duration_basis": "elapsed_wall_clock",
    "continuous_run": True,
    "stop_at_deadline": False,
    "design_version": os.environ.get("S5_DESIGN", "1"),
    "deadline_is_accounting_only": True,
    "run_until_queue_empty": True,
    "deadline_persists_on_resume": True,
    "curator_packet_policy": "final_only",
    "early_curator_packets": False,
    "confirmation_freeze_hour": 20,
    "max_substantive_confirmations": 2,
    "max_cpu_workers": 2,
    "allocation_hours": dict(ALLOCATION_HOURS),
    "cards": list(CARDS),
    "lanes": list(SPLITS),
    "oracle_bypass_is_end_to_end_success": False,
    "pilot_outputs_promotable": False,
    "late_split_of_old_data_is_confirmation": False,
    "cloud_or_paid_api_authorized": False,
    "agent_delegation_authorized": False,
    "human_participants_authorized": False,
    "claim_class": "bounded model-reader, controlled-artifact, method, and dataset results only",
}

__all__ = ['ACCESS_LEVELS', 'ContractError', 'EXEC_STATES', 'FreshnessViolation', 'Lineages', 'Manifest', 'OUTCOMES', 'PURSUIT', 'PacketGuard', 'RealizationError', 'RunContract', 'SplitViolation', 'WARRANT', 'aggregate_equal', 'append_jsonl', 'canonical', 'check_marker', 'classify_outcome', 'code_hash', 'completion_marker', 'coverage', 'expand_expected_cells', 'now_iso', 'packet_allowed', 'read_json', 'read_jsonl', 'require_realized_truth', 'sha256_file', 'sha256_text', 'validate_expected', 'validate_run_label', 'verdict_gate', 'write_json']



# ── the Stage-5 records: same classes, Stage-5 paths and registry ─────────────────────

class RunContract5(RunContract):
    PATH = S5 / "RUN_CONTRACT.json"

    @classmethod
    def create(cls, extra: dict | None = None, path: Path | None = None) -> "RunContract5":
        p = path or cls.PATH
        if p.exists():
            return cls.load(p)
        data = dict(SEED_CONTRACT)
        data.update({"contract_version": CONTRACT_VERSION, "created_at": now_iso(),
                     "frozen": {}, "lost_time": [], "run_hours": RUN_HOURS,
                     "closure_hour": CLOSURE_HOUR, "thresholds": dict(DEFAULT_THRESHOLDS),
                     "gear": "second (his call 2026-08-29; run until empty)"})
        if extra:
            data.update(extra)
        c = cls(data, p)
        c.save()
        return c

    @classmethod
    def load(cls, path: Path | None = None) -> "RunContract5 | None":
        p = path or cls.PATH
        if not p.exists():
            return None
        return cls(read_json(p), p)


class Lineages5(Lineages):
    PATH = S5 / "SOURCE_LINEAGES.json"


# Stage-5 outcomes: the Stage-4 bands plus two labels that are not evidence about a
# hypothesis and must never be counted as absent evidence (VOID): an infrastructure card that
# passed, and a descriptive card that has no outcome band by design
OUTCOMES5 = tuple(OUTCOMES) + ("INFRASTRUCTURE", "DESCRIPTIVE")


class Manifest5(Manifest):
    PATH = S5 / "QUEUE_MANIFEST.json"

    def set_outcome(self, cell_id: str, outcome: str, detail=None) -> None:
        assert outcome in OUTCOMES5, outcome
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


class ClaimLedger5(ClaimLedger):
    PATH = S5 / "CLAIM_LEDGER.json"


def card_dir(card: str) -> Path:
    p = S5 / card
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_packet(text: str, contract: RunContract, exhausted: bool) -> Path:
    """The one curator-facing file (§8.1); any other packet path is refused."""
    return _s4.write_packet(text, contract, exhausted, path=S5 / "CURATOR_PACKET_FINAL.md")


def refuse_packet_path(path: Path) -> None:
    """Verification 12: no curator packet may exist at any other path."""
    if Path(path).name != "CURATOR_PACKET_FINAL.md" or Path(path).parent != S5:
        raise PacketGuard(f"{path} is not the one permitted curator packet path")


# ── the constrained latent record (§4.1) ──────────────────────────────────────────────

LATENTS = ("episode_goal", "process_plan", "standing_preference", "maker_belief",
           "maker_appraisal", "audience_effect_goal", "communicative_goal",
           "content_support", "source_reliability", "reader_response", "reader_uptake")
TRIPLE = ("episode_goal", "process_plan", "standing_preference")
OWNER_VARIABLES = ("reader_response", "audience_effect_goal", "maker_appraisal",
                   "content_support", "communicative_goal", "source_reliability",
                   "reader_uptake")
COMMUNICATIVE_GOALS = ("inform", "assist", "warn", "impress", "recruit", "conceal", "mislead")
UNKNOWN = "unknown"


class LatentRecordError(ValueError):
    pass


def latent_record(**fields) -> dict:
    """One structured record: for every latent named, a dict {candidates: {name: mass},
    unknown: mass, confidence, evidence: [span ids]}; latents not named are absent (never
    silently filled). Masses over candidates plus unknown sum to one."""
    rec = {}
    for name, v in fields.items():
        if name not in LATENTS:
            raise LatentRecordError(f"unknown latent {name}")
        cand = dict(v.get("candidates", {}))
        unk = float(v.get("unknown", 0.0))
        total = sum(cand.values()) + unk
        if total <= 0:
            raise LatentRecordError(f"{name}: no mass")
        rec[name] = {"candidates": {k: float(c) / total for k, c in cand.items()},
                     "unknown": unk / total,
                     "confidence": float(v.get("confidence", max(list(cand.values()) + [unk]) / total)),
                     "evidence": list(v.get("evidence", []))}
    return rec


def check_owners_distinct(rec: dict) -> None:
    """Verification 6: owner variables are separate keys with separate masses; an
    aggregation that copies one into another is a schema violation. Checked by identity
    of the candidate dicts (the same object under two keys is the overwrite this guards)."""
    seen = {}
    for name in OWNER_VARIABLES:
        if name in rec:
            ident = id(rec[name]["candidates"])
            if ident in seen:
                raise LatentRecordError(f"{name} shares its mass object with {seen[ident]}")
            seen[ident] = name


def merge_records(a: dict, b: dict) -> dict:
    """Combine two readers' records latent by latent under equal weight (never averaging
    across latents or owners; R11: no naive pooling that hides duplicate evidence, so a
    record that carries the same evidence ids as the other contributes once)."""
    out = {}
    for name in set(a) | set(b):
        ra, rb = a.get(name), b.get(name)
        if ra is None or rb is None:
            out[name] = dict(ra or rb)
            continue
        if set(ra["evidence"]) == set(rb["evidence"]) and ra["candidates"] == rb["candidates"]:
            out[name] = dict(ra)          # identical evidence adds no constraint (R11)
            continue
        keys = set(ra["candidates"]) | set(rb["candidates"])
        cand = {k: 0.5 * (ra["candidates"].get(k, 0.0) + rb["candidates"].get(k, 0.0)) for k in keys}
        out[name] = {"candidates": cand, "unknown": 0.5 * (ra["unknown"] + rb["unknown"]),
                     "confidence": max(cand.values()) if cand else 0.0,
                     "evidence": sorted(set(ra["evidence"]) | set(rb["evidence"]))}
    return out


# ── the Stage-5 root registries (§9) ──────────────────────────────────────────────────

def write_registry(name: str, obj) -> Path:
    """CONSTRUCTION_IDENTITIES, ROUTE_INFORMATION, WORKLOAD_LOCK, COMPLETION,
    CONFIRMATION_REGISTRY, EXPECTED_CELLS: one writer each, atomic, under the root."""
    assert name in ("CONSTRUCTION_IDENTITIES", "ROUTE_INFORMATION", "WORKLOAD_LOCK",
                    "COMPLETION", "CONFIRMATION_REGISTRY", "EXPECTED_CELLS", "COVERAGE",
                    "PREPARED", "SCHEDULER_STATUS"), name
    p = S5 / f"{name}.json"
    write_json(p, obj)
    return p


def read_registry(name: str):
    p = S5 / f"{name}.json"
    return read_json(p) if p.exists() else None


def workload_locked() -> bool:
    """§8.3: the workload lock must be written before discovery outputs are opened."""
    w = read_registry("WORKLOAD_LOCK")
    return bool(w and w.get("tier"))


# ── calibration and selective-risk scores (§7.1) ─────────────────────────────────────

def ece(probs_truth: list[tuple[float, bool]], bins: int = 10) -> float:
    """Expected calibration error over (confidence of the chosen option, correct)."""
    if not probs_truth:
        return float("nan")
    tot = len(probs_truth)
    err = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        cell = [(p, c) for p, c in probs_truth if lo <= p < hi or (b == bins - 1 and p == 1.0)]
        if cell:
            conf = sum(p for p, _ in cell) / len(cell)
            acc = sum(1.0 for _, c in cell if c) / len(cell)
            err += abs(conf - acc) * len(cell) / tot
    return err


def calibration_slope(probs_truth: list[tuple[float, bool]]) -> float | None:
    """Slope of correctness on confidence (1 = calibrated, <1 overconfident)."""
    n = len(probs_truth)
    if n < 3:
        return None
    mx = sum(p for p, _ in probs_truth) / n
    my = sum(1.0 for _, c in probs_truth if c) / n
    sxx = sum((p - mx) ** 2 for p, _ in probs_truth)
    if sxx == 0:
        return None
    sxy = sum((p - mx) * ((1.0 if c else 0.0) - my) for p, c in probs_truth)
    return sxy / sxx


def selective_risk_coverage(items: list[tuple[float, float]], coverages=(1.0, 0.8, 0.6, 0.4)) -> dict:
    """items: (confidence, loss). Risk at each coverage when the least confident are
    abstained; the abstention question the joint-reader criterion asks (§7.2)."""
    if not items:
        return {}
    s = sorted(items, key=lambda x: -x[0])
    out = {}
    for cov in coverages:
        k = max(1, int(round(cov * len(s))))
        out[str(cov)] = sum(l for _, l in s[:k]) / k
    return out
