"""Stage 7 shared schema and bookkeeping (brief: docs/design/PHASE_2_4_STAGE_7_CONTEXT.md).

Everything the 100 questions and 24 attacks share that is not a model call, built ON the
Stage-4/5/6 machinery (soundingline/s4.py, stage5.py, stage6.py) rather than beside it:
the run contract with ONE immutable 72-hour ceiling (started at the discarded pilot,
surviving restarts; §13.2), the lineage ledger with six lanes, the queue manifest over the
eight trunks and the attack matrix, the packet guard (one curator-facing file, refused
before closure plus validation; §13.2, §19), the registries (§14), and the Stage-7
additions: the three artifacts of §6.1 (VisibleEvidenceV1 as an ALLOWLIST, OracleBundleV1
for constructors and scorers only, PredictionV1 emitted by readers without a world object),
the canonical maker-model factor names of §3 (seven factors plus the bounded persistent
tendency rival; expertise OWNS the transition law, process is the realized path), the
system codes of §8, the capability ratios U_state and R_j with their void rule, and the
Ghost V15 read-only boundary.

Stage 1-6 code and results are immutable; this module only subclasses and moves paths.
The run-until-empty ruling (2026-08-28) is carried as in Stage 6: the 72-hour ceiling is a
REAL stop for admitting new work; inside it the queue runs continuously; exhaustion before
FLOOR_HOUR writes SHORT_RUN.json with the honest cause (§13.2).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3 (blind floors follow the truth marginal: every ratio here is void
  when its denominator is under the minimum gap, never re-thresholded; the criterion must
  be able to fail: the allowlist validator has planted-canary tests in tools/test_s7.py),
  §5 (one manifest writer; produces guards; the deadline persists across restarts).
gates: the ratio void rule: NULL (no usable oracle gap) gives a denominator under 0.05
  nats and the ratio is None, the question VOID; ALTERNATIVE (a live ruler) gives a
  denominator at or above 0.05 and a finite ratio; failure direction guarded: a small or
  negative denominator would otherwise inflate a ratio upward, so the void fires BELOW the
  floor. bands: exhaustive (None below the floor, a number at or above it); the engines'
  verdict bands are stated there.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import time
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
from soundingline.stage6 import brier, hazard_log_score, span_score               # noqa: F401

__all__ = ['EXEC_STATES', 'OUTCOMES', 'PURSUIT', 'WARRANT', 'ClaimLedger', 'ContractError',
           'FreshnessViolation', 'Lineages', 'Manifest', 'PacketGuard', 'RealizationError',
           'RunContract', 'SplitViolation', 'aggregate_equal', 'append_jsonl', 'canonical',
           'check_marker', 'classify_outcome', 'code_hash', 'completion_marker', 'coverage',
           'expand_expected_cells', 'now_iso', 'read_json', 'read_jsonl', 'sha256_file',
           'sha256_text', 'validate_expected', 'write_json', 'OUTCOMES5', 'ece',
           'calibration_slope', 'selective_risk_coverage', 'brier', 'hazard_log_score',
           'span_score']

REPO = Path(__file__).resolve().parents[1]
STAGE = os.environ.get("S7_STAGE", "phase_2_4_stage_7")
S7 = Path(os.environ["S7_ROOT"]) if os.environ.get("S7_ROOT") else REPO / "results" / STAGE
CONTRACT_VERSION = "7.0.0"
RUN_HOURS = float(os.environ.get("S7_RUN_HOURS", "72"))          # the ceiling (§13.2)
CLOSURE_HOUR = float(os.environ.get("S7_CLOSURE_HOUR", "64"))    # confirmation freeze (§12.5, §13.5)
FLOOR_HOUR = 54.0                                                # exhausting earlier is SHORT (§13.2)
USEFUL_TARGET_H = (54.0, 66.0)
SMOKE = bool(os.environ.get("S7_SMOKE"))
MIN_GAP_NATS = 0.05                                              # the ratio void floor
DEFAULT_GAIN_FLOOR = 0.20                                        # §12.4: 20 percent of the oracle gap

SPLITS = ("pilot", "discovery", "transfer", "confirmation", "conformance", "attack")
_s4.SPLITS = SPLITS

# ── the question inventory (§10): eight trunks, 100 mandatory questions ──────────────
TRUNKS = {"I": 16, "D": 10, "K": 16, "R": 16, "A": 16, "P": 14, "V": 6, "B": 6}
QUESTIONS = [f"{t}{i:02d}" for t, n in TRUNKS.items() for i in range(1, n + 1)]
assert len(QUESTIONS) == 100, len(QUESTIONS)
ATTACKS = [f"X{i:02d}" for i in range(1, 25)]
TRACK_OF = {q: {"I": "isolation", "D": "dependency", "K": "supplied_state", "R": "reconstruction",
                "A": "architecture", "P": "prospective", "V": "history", "B": "closure"}[q[0]]
            for q in QUESTIONS}
TRACK_OF.update({a: "attack" for a in ATTACKS})

# ── the canonical maker model (§3): seven factors and the bounded rival ──────────────
FACTORS = ("external_context", "belief_state", "expertise_law", "maker_context",
           "subjective_action_space", "proximal_goal", "history_residue")
FACTOR_SYMBOL = {"external_context": "C_ext", "belief_state": "B", "expertise_law": "K",
                 "maker_context": "C_m", "subjective_action_space": "A_tilde",
                 "proximal_goal": "G", "history_residue": "H"}
RIVAL_FACTOR = "persistent_tendency"                               # V: carried, never presumed recovered
REALIZED_PROCESS = "realized_process"                              # tau: K is not tau (§3)

# ── the systems (§8) ─────────────────────────────────────────────────────────────────
SYSTEMS = ("U", "PERS", "DOM", "DIR", "KL", "SLJ", "OR")
SYSTEM_NAMES = {"U": "uniform or opportunity-marginal baseline",
                "PERS": "persistence, last-event, and position baselines",
                "DOM": "frozen common-domain process model",
                "DIR": "direct model reader",
                "KL": "known-law Bayesian selector among supplied executable laws",
                "SLJ": "Sounding joint reader (proposes and revises factors, predicts through the solver)",
                "OR": "exact oracle (construction ceiling, never a competing reader)"}
# external families (§5): admitted under the published name only after conformance; the
# descriptive local name is the default and the only name the packet uses otherwise
EXTERNAL_FAMILIES = {
    "laip": {"published": "LLM-Augmented Inverse Planning", "local": "weighted_language_hypotheses",
             "defining": "the language model proposes hypotheses AND likelihood functions; an external Bayesian component computes the posterior"},
    "thought_tracing": {"published": "ThoughtTracing", "local": "sequential_hypothesis_particles",
                        "defining": "preprocess into state/action/perception steps; initialize, propagate, weight, ESS-resample, diversity-check, rejuvenate natural-language hypotheses"},
    "autotom": {"published": "AutoToM", "local": "adaptive_factor_expansion",
                "defining": "propose an initial causal agent model; explicit Bayesian inference; utility-driven latent addition and time-window extension"},
    "liras": {"published": "LIRAS-style paper reproduction", "local": "synthesized_agent_model",
              "defining": "synthesize and validate a situation-specific environment model, agent model, parsed state/action sequence, and inverse-planning computation"},
    "inverse_planning": {"published": "InversePlanning.jl", "local": "known_law_inverse_planning",
                         "defining": "probabilistic inverse planning over explicit plans/actions with a known model (exact independently checked equivalent admitted by §10 A12)"},
    "labtom": {"published": "LaBToM.jl", "local": "epistemic_translation",
               "defining": "translate epistemic language into a compositional epistemic representation evaluated against Bayesian mental-state inference"},
}

OUTCOMES7 = OUTCOMES5
AUDIT_CLASSES = ("CLEAN", "DEPENDENCY_TAINTED", "CONSTRUCTION_INVALID", "DUPLICATE_ESTIMAND", "UNRESOLVED")

SEED_CONTRACT = {
    "stage": STAGE,
    "reviewed_commit": "5936b0b",
    "ghost_reviewed_commit": "ce4c06b",
    "brief": "docs/design/PHASE_2_4_STAGE_7_CONTEXT.md",
    "run_duration_hours": 72,
    "useful_work_target_hours": list(USEFUL_TARGET_H),
    "duration_basis": "elapsed_wall_clock_from_pilot_start",
    "continuous_run": True,
    "stop_at_deadline": True,                        # §13.2: the ceiling is real
    "deadline_is_accounting_only": False,
    "run_until_queue_empty": True,
    "short_run_floor_hour": FLOOR_HOUR,
    "deadline_persists_on_resume": True,
    "curator_packet_policy": "final_only_after_closure_and_validation",
    "early_curator_packets": False,
    "confirmation_freeze_hour": CLOSURE_HOUR,
    "max_substantive_confirmations": 3,
    "max_cpu_workers_while_ghost_live": 2,
    "isolation_mechanism": "interpreter capsule (his ruling 2026-09-02): fresh isolated python, capsule-only path, scrubbed environment, raising audit hook, loopback model endpoint",
    "external_sources_policy": "read-only clones in the sibling reference workspace, pinned in SOURCE_MANIFEST.json (his ruling 2026-09-02); never vendored, never on the capsule path",
    "questions": list(QUESTIONS),
    "attacks": list(ATTACKS),
    "systems": list(SYSTEMS),
    "factors": list(FACTORS),
    "lanes": list(SPLITS),
    "oracle_gap_floor": DEFAULT_GAIN_FLOOR,
    "min_gap_nats": MIN_GAP_NATS,
    "oracle_bypass_is_end_to_end_success": False,
    "pilot_outputs_promotable": False,
    "late_split_of_old_data_is_confirmation": False,
    "cloud_or_paid_api_authorized": False,
    "agent_delegation_authorized": False,
    "human_participants_authorized": False,
    "ghost_v15_boundary": "read-only status, commit, and completion; no import of partial outcomes; no V16",
    "claim_class": "instrument repair, bounded model-reader capability, prospective process inference, process-discontinuity localization",
}


# ── the Stage-7 records: same classes, Stage-7 paths ──────────────────────────────────

class RunContract7(RunContract):
    PATH = S7 / "RUN_CONTRACT.json"

    @classmethod
    def create(cls, extra: dict | None = None, path: Path | None = None) -> "RunContract7":
        p = path or cls.PATH
        if p.exists():
            return cls.load(p)
        data = dict(SEED_CONTRACT)
        data.update({"contract_version": CONTRACT_VERSION, "created_at": now_iso(),
                     "frozen": {}, "lost_time": [], "run_hours": RUN_HOURS,
                     "closure_hour": CLOSURE_HOUR,
                     "gear": "second (his order 2026-09-02: build the whole thing and set it to run in gear two)"})
        if extra:
            data.update(extra)
        c = cls(data, p)
        c.save()
        return c

    @classmethod
    def load(cls, path: Path | None = None) -> "RunContract7 | None":
        p = path or cls.PATH
        if not p.exists():
            return None
        return cls(read_json(p), p)


class Lineages7(Lineages):
    PATH = S7 / "SOURCE_LINEAGES.json"


class Manifest7(Manifest):
    PATH = S7 / "QUEUE_MANIFEST.json"

    def set_outcome(self, cell_id: str, outcome: str, detail=None) -> None:
        assert outcome in OUTCOMES7 or outcome == "NOT_RUN", outcome
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


class ClaimLedger7(ClaimLedger):
    PATH = S7 / "CLAIM_LEDGER.json"


def card_dir(card: str) -> Path:
    p = S7 / card
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_packet(text: str, contract: RunContract, exhausted: bool) -> Path:
    """The one curator-facing file (§13.2, §19); any other packet path is refused."""
    return _s4.write_packet(text, contract, exhausted, path=S7 / "CURATOR_PACKET_FINAL.md")


def refuse_packet_path(path: Path) -> None:
    if Path(path).name != "CURATOR_PACKET_FINAL.md" or Path(path).parent != S7:
        raise PacketGuard(f"{path} is not the one permitted curator packet path")


# ── registries (§14) ──────────────────────────────────────────────────────────────────

REGISTRIES = ("STAGE6_DEPENDENCY_AUDIT", "SOURCE_MANIFEST", "INFORMATION_BOUNDARY",
              "STRUCTURAL_LOCK", "WORKLOAD_LOCK", "SCIENTIFIC_LOCK", "EXPECTED_CELLS",
              "ATTACK_MATRIX", "SPLIT_RECEIPT", "COMPUTE_LEDGER", "RUNTIME", "COVERAGE",
              "COMPLETION", "CONFIRMATION_REGISTRY", "PREPARED", "SCHEDULER_STATUS",
              "SHORT_RUN", "PILOT", "GHOST_BRIDGE", "CORPUS_DISPOSITIONS", "COEXISTENCE",
              "ACCESS_RECEIPT", "KEYSTONE_LOCK", "IDENTITY_HASHES", "GATES", "CONFORMANCE",
              "DOM_FROZEN", "REPAIRS")


def write_registry(name: str, obj) -> Path:
    assert name in REGISTRIES, name
    S7.mkdir(parents=True, exist_ok=True)
    p = S7 / f"{name}.json"
    write_json(p, obj)
    return p


def read_registry(name: str):
    p = S7 / f"{name}.json"
    if not p.exists():
        return None
    for attempt in range(20):
        try:
            return read_json(p)
        except (PermissionError, OSError, ValueError):
            if attempt == 19:
                raise
            time.sleep(0.25)          # a writer is mid-replace; the file is whole a moment later


class registry_lock:
    """A directory lock over one registry (os.mkdir is atomic on every platform here): the
    read-modify-write of a shared registry by parallel cells is serialized through it; a lock
    older than two minutes is treated as abandoned by a dead cell and broken."""

    def __init__(self, name: str, timeout_s: float = 90.0):
        self.path = S7 / f".lock_{name}"
        self.timeout_s = timeout_s

    def __enter__(self):
        S7.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        while True:
            try:
                os.mkdir(self.path)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 120:
                        os.rmdir(self.path)
                        continue
                except OSError:
                    pass
                if time.time() - t0 > self.timeout_s:
                    raise TimeoutError(f"registry lock {self.path.name} held for over {self.timeout_s:.0f} s")
                time.sleep(0.2)

    def __exit__(self, *exc):
        try:
            os.rmdir(self.path)
        except OSError:
            pass
        return False


def update_registry(name: str, fn):
    """Read-modify-write under the registry lock: fn receives the current object (or {}) and
    returns the object to write."""
    with registry_lock(name):
        obj = fn(read_registry(name) or {})
        write_registry(name, obj)
        return obj


def workload_locked() -> bool:
    w = read_registry("WORKLOAD_LOCK")
    return bool(w and w.get("tier"))


def scientific_locked() -> bool:
    w = read_registry("SCIENTIFIC_LOCK")
    return bool(w and w.get("locked"))


def gate_state(name: str) -> dict | None:
    """§12.1: a gate's VERDICT, read by the engines before dependent cells (LESSONS §3: a
    gate dependency is the verdict, not the file)."""
    g = read_registry("GATES") or {}
    return g.get(name)


def set_gate(name: str, passed: bool, detail: dict | None = None) -> None:
    update_registry("GATES", lambda g: {**g, name: {"passed": bool(passed), "at": now_iso(), "detail": detail or {}}})


# ── the three artifacts (§6.1) ────────────────────────────────────────────────────────

EVIDENCE_VERSION = "VisibleEvidenceV1"
ORACLE_VERSION = "OracleBundleV1"
PREDICTION_VERSION = "PredictionV1"

# the allowlist: what a VisibleEvidenceV1 may carry, by field; a condition declares the
# subset it supplies and the validator rejects everything else (recursively: no callables,
# no unknown top-level keys, JSON scalars/lists/dicts only)
EVIDENCE_FIELDS = {
    "version": "the schema tag",
    "unit_ref": "an opaque lineage identifier generated independently of hidden truth",
    "condition_ref": "an opaque condition identifier",
    "domain": "the artifact domain name",
    "brief": "the task brief genuinely supplied to the reader",
    "artifact_state": "the current artifact state (sections and filled slots) through the cut",
    "process_prefix": "observed actions through the cut, in order",
    "objective_options": "the objective option list at the cut when the condition supplies it",
    "demonstrations": "prior demonstrations or dated works assigned to that evidence condition",
    "supplied_factors": "explicitly supplied maker factors when the rung requires them (executable or language form)",
    "candidate_laws": "a bounded set of executable maker laws when the rung is known-law selection",
    "query": "the target vocabulary and option set the reader must answer over",
    "history": "a revision history with anonymized actor-blind events (mixed-control conditions)",
    "regime": "the evidence regime label: cold, domain_expert, maker_familiar",
    "render": "the surface renderer name (matched across conditions)",
}
# key names that must never appear anywhere in a visible-evidence object (I10 canaries):
# exact names, plus a few substrings no honest field carries
FORBIDDEN_KEYS = {"target", "targets", "truth", "hidden", "future", "future_tail", "stop_shift", "stopped_at", "stop_next",
                  "oracle", "seed", "lid", "lineage", "lineage_id", "tail", "tail_stop", "answer", "answer_hint",
                  "label_true", "controller", "goal_true", "belief_true", "law_true", "counterfactual",
                  "changed_context_truth", "boundary_true", "actor", "actor_role", "regime_true", "hypothesis_tag",
                  "equivalence_class", "unavailable_ids", "subjective_ids", "names", "state_names", "state_at_cut",
                  "rejected_alternative", "change_point", "regimes", "style_shift_at", "cut"}
FORBIDDEN_SUBSTRINGS = ("truth", "hidden", "oracle", "canary", "secret")


class EvidenceViolation(ValueError):
    pass


def _walk(obj, path: str, problems: list[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                problems.append(f"{path}: non-string key")
                continue
            kl = k.lower()
            if kl in FORBIDDEN_KEYS:
                problems.append(f"{path}.{k}: forbidden key {kl!r}")
            else:
                for w in FORBIDDEN_SUBSTRINGS:
                    if w in kl:
                        problems.append(f"{path}.{k}: forbidden key substring {w!r}")
            _walk(v, f"{path}.{k}", problems)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _walk(v, f"{path}[{i}]", problems)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return
    else:
        problems.append(f"{path}: non-JSON value of type {type(obj).__name__}")


def validate_visible_evidence(ev: dict, allowed: set[str] | None = None) -> list[str]:
    """Allowlist validation (I03): every top-level key must be in EVIDENCE_FIELDS and in
    the condition's declared subset; nested objects may hold only JSON scalars, lists, and
    dicts; forbidden key words anywhere fail. Returns the problem list (empty = valid)."""
    problems: list[str] = []
    if not isinstance(ev, dict):
        return ["evidence is not an object"]
    if ev.get("version") != EVIDENCE_VERSION:
        problems.append(f"version {ev.get('version')!r} is not {EVIDENCE_VERSION}")
    allowed_keys = set(EVIDENCE_FIELDS) if allowed is None else (set(allowed) | {"version", "unit_ref", "condition_ref"})
    for k in ev:
        if k not in EVIDENCE_FIELDS:
            problems.append(f"undeclared field {k!r}")
        elif k not in allowed_keys:
            problems.append(f"field {k!r} is not in this condition's allowlist")
    _walk({k: v for k, v in ev.items() if k != "version"}, "$", problems)
    return problems


def evidence_sha(ev: dict) -> str:
    return hashlib.sha256(canonical(ev).encode("utf-8")).hexdigest()[:16]


def _round(obj, nd: int = 6):
    if isinstance(obj, float):
        return round(obj, nd)
    if isinstance(obj, dict):
        return {k: _round(v, nd) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple)):
        return [_round(v, nd) for v in obj]
    return obj


def canonical_prediction(pred: dict) -> bytes:
    """The canonical serialization the mutation attacks compare byte for byte (§6.3):
    sorted keys, floats rounded to six places, compute receipt and timing excluded."""
    core = {k: v for k, v in pred.items() if k not in ("compute", "at", "wall_s")}
    return json.dumps(_round(core), sort_keys=True, separators=(",", ":")).encode("utf-8")


def prediction_sha(pred: dict) -> str:
    return hashlib.sha256(canonical_prediction(pred)).hexdigest()[:16]


def validate_prediction(pred: dict) -> list[str]:
    """I11: every reader emits a normalized PredictionV1: a version tag, the evidence hash it
    answered, one normalized distribution per declared target (a hazard as a probability),
    an equivalence-class list, an abstention flag, and a confidence in [0, 1]."""
    problems: list[str] = []
    if not isinstance(pred, dict):
        return ["prediction is not an object"]
    if pred.get("version") != PREDICTION_VERSION:
        problems.append("version")
    if not isinstance(pred.get("evidence_sha"), str):
        problems.append("evidence_sha")
    t = pred.get("targets")
    if not isinstance(t, dict) or not t:
        problems.append("targets empty")
    else:
        for name, dist in t.items():
            if isinstance(dist, dict):
                if not dist:
                    problems.append(f"{name}: empty distribution")
                    continue
                tot = sum(float(v) for v in dist.values())
                if any(float(v) < 0 for v in dist.values()) or abs(tot - 1.0) > 1e-6:
                    problems.append(f"{name}: not normalized ({tot:.6f})")
            elif isinstance(dist, (int, float)):
                if not 0.0 <= float(dist) <= 1.0:
                    problems.append(f"{name}: probability outside [0,1]")
            else:
                problems.append(f"{name}: neither distribution nor probability")
    if not isinstance(pred.get("equivalence_class"), list):
        problems.append("equivalence_class")
    if not isinstance(pred.get("abstain"), bool):
        problems.append("abstain")
    c = pred.get("confidence")
    if not isinstance(c, (int, float)) or not 0.0 <= float(c) <= 1.0:
        problems.append("confidence")
    return problems


def normalize(dist: dict, floor: float = 0.0) -> dict:
    d = {k: max(float(v), floor) for k, v in dist.items()}
    z = sum(d.values())
    if z <= 0:
        n = len(d) or 1
        return {k: 1.0 / n for k in d}
    return {k: v / z for k, v in d.items()}


# ── the compute-budget ledger (§8, I13) ───────────────────────────────────────────────

def budget_row(model_calls: int = 0, tokens_in: int = 0, tokens_out: int = 0,
               forward_passes: int = 0, wall_s: float = 0.0, peak_mem_mb: float | None = None,
               solver_operations: int = 0, retries: int = 0, cache_hits: int = 0) -> dict:
    return {"model_calls": model_calls, "tokens_in": tokens_in, "tokens_out": tokens_out,
            "forward_passes": forward_passes, "wall_s": round(wall_s, 3),
            "peak_mem_mb": peak_mem_mb, "solver_operations": solver_operations,
            "retries": retries, "cache_hits": cache_hits}


def add_budget(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if v is None:
            continue
        out[k] = (out.get(k) or 0) + v if k != "peak_mem_mb" else max(out.get(k) or 0, v)
    return out


# ── the Ghost V15 boundary (§0, B04): read-only ───────────────────────────────────────

GHOST_ROOT = (REPO.parent.parent / "AI and Intentionality" / "Ghost Scale Simulation"
              / "ghost-scale-sim")
GHOST_V15 = GHOST_ROOT / "results" / "v15"
GHOST_V14 = GHOST_ROOT / "results" / "v14"


def ghost_status(max_age_min: float = 30.0) -> dict:
    """The coexistence governor's read (read-only): V15's RUNNER_STATUS.json heartbeat (V14's
    when V15 has none). `live` when the heartbeat is fresh; the CPU cap is 2 whenever live."""
    import datetime as _dt                                                        # noqa: PLC0415
    p = GHOST_V15 / "RUNNER_STATUS.json"
    if not p.exists():
        p = GHOST_V14 / "RUNNER_STATUS.json"
    out = {"path": str(p), "exists": p.exists(), "live": False, "heartbeat": None, "stage": None}
    if not p.exists():
        return out
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        out["error"] = repr(e)
        out["live"] = True
        return out
    out["heartbeat"] = d.get("heartbeat")
    out["stage"] = d.get("stage") or d.get("phase")
    out["pid"] = d.get("pid")
    out["program"] = d.get("program")
    try:
        hb = _dt.datetime.fromisoformat(str(d.get("heartbeat")))
        age_min = (_dt.datetime.now() - hb).total_seconds() / 60
        out["age_min"] = round(age_min, 1)
        out["live"] = age_min <= max_age_min
    except (TypeError, ValueError):
        out["live"] = True
    return out


def ghost_receipt() -> dict:
    """B04's status/hash bridge: the repository head (read-only git query), whether a V15
    completion record exists, and the hashes of the files whose byte identity test 27
    checks. Nothing is imported."""
    out = {"root": str(GHOST_ROOT), "exists": GHOST_ROOT.exists(), "head": None,
           "v15_complete": False, "files": {}}
    if not GHOST_ROOT.exists():
        return out
    try:
        out["head"] = subprocess.run(["git", "-C", str(GHOST_ROOT), "rev-parse", "--short", "HEAD"],
                                     capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as e:                                                        # noqa: BLE001
        out["head_error"] = repr(e)
    comp = GHOST_V15 / "COMPLETION.json"
    if comp.exists():
        try:
            d = json.loads(comp.read_text(encoding="utf-8"))
            out["v15_complete"] = bool(d.get("complete") or d.get("final") or d.get("closed"))
            out["v15_completion_keys"] = sorted(d)[:12]
        except (OSError, ValueError):
            pass
    for name in ("RUNNER_STATUS.json", "COMPLETION.json", "COVERAGE.json", "DEADLINE.json"):
        p = GHOST_V15 / name
        if p.exists():
            out["files"][name] = sha256_file(p)[:16]
    return out


# ── the capability ratios (§8) ────────────────────────────────────────────────────────

def oracle_gap(s_or: float, s_dom: float) -> float | None:
    """S_OR minus S_DOM; None (void) under the minimum gap."""
    g = s_or - s_dom
    return g if g >= MIN_GAP_NATS else None


def u_state(s_true_state: float, s_dom: float, s_or: float) -> float | None:
    """U_state = (S_true_state - S_DOM) / (S_OR - S_DOM); void when the oracle gap is under
    the floor (denominator nonpositive or too small: the ratio would inflate upward)."""
    g = oracle_gap(s_or, s_dom)
    if g is None:
        return None
    return (s_true_state - s_dom) / g


def r_ratio(s_j: float, s_dom: float, s_true_state: float) -> float | None:
    """R_j = (S_j - S_DOM) / (S_true_state - S_DOM); void when the supplied-state advantage
    is under the floor."""
    g = s_true_state - s_dom
    if g < MIN_GAP_NATS:
        return None
    return (s_j - s_dom) / g


# ── the extra scores (§16.1) ──────────────────────────────────────────────────────────

def log_score(dist: dict, truth, floor: float = 1e-9) -> float:
    return math.log(max(float(dist.get(truth, 0.0)), floor))


def changepoint_log_score(post: dict, truth, floor: float = 1e-9) -> float:
    """The full posterior over boundary locations (keys: position strings and 'none');
    the log mass on the true location (or on 'none')."""
    return math.log(max(float(post.get(str(truth), 0.0)), floor))


def expected_boundary_error(post: dict, truth, n: int) -> float | None:
    """Expected absolute boundary error under the posterior, in events; 'none' mass counts
    as the full span (the worst location). None when the truth is 'none'."""
    if str(truth) == "none":
        return None
    t = int(truth)
    e = 0.0
    for k, p in post.items():
        d = n if k == "none" else abs(int(k) - t)
        e += float(p) * d
    return e


def tv(a: dict, b: dict) -> float:
    return 0.5 * sum(abs(float(a.get(k, 0.0)) - float(b.get(k, 0.0))) for k in set(a) | set(b))


def entropy(dist: dict) -> float:
    return -sum(float(p) * math.log(max(float(p), 1e-12)) for p in dist.values())
