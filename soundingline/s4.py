"""Stage 4 shared schema and bookkeeping (brief: docs/design/PHASE_2_4_STAGE_4_CONTEXT.md).

One home for everything the eighteen cards share that is not a model call: the run
contract with its persisted start and deadline, the source-lineage allocator (splits are
assigned at allocation, before any scoring), the queue manifest with execution states kept
apart from scientific outcome classes, the row-level provenance record, GPU-lock-held
metering beside elapsed wall time, completion markers that carry the contract version and
input/output hashes, coverage, the claim ledger, and the final-packet guard.

Rules from the brief and the method shelf that this module enforces in code rather than
prose:
  - the deadline is written once and survives restarts (§5.1, verification 10);
  - execution state and scientific outcome are separate fields (§8.3);
  - outcome classification has exhaustive interval bands with no silent gap (§8.3, L73);
  - a lineage inspected or used for fitting can never be labeled fresh (§7 F01,
    verification 4); derived items inherit their parent's split and cluster (§6.2);
  - aggregation is a mean of per-unit means, order-invariant, every eligible reader
    weighted equally (L236, verification 5);
  - the packet writer refuses before the deadline unless the run is exhausted (§5.3,
    verification 11);
  - ground truth must be a realized draw or a realized choice, never an assigned
    instruction (L137, verification 6).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STAGE = "phase_2_4_stage_4"
# S4_ROOT lets a smoke test run the whole machinery against a scratch root; the real run
# never sets it
S4 = Path(os.environ["S4_ROOT"]) if os.environ.get("S4_ROOT") else REPO / "results" / STAGE
CONTRACT_VERSION = "1.0.0"
# the window and the closure hour are the brief's 24 and 20; the environment overrides
# exist so a scratch-root smoke can run the whole loop, closure block and packet
# included, inside a compressed window (the real run never sets them, and the contract
# persists whatever it was created with)
RUN_HOURS = float(os.environ.get("S4_RUN_HOURS", "24"))
CLOSURE_HOUR = float(os.environ.get("S4_CLOSURE_HOUR", "20"))

EXEC_STATES = ("PLANNED", "RUNNING", "COMPLETE", "FAILED", "BLOCKED", "DEFERRED")
OUTCOMES = ("SUPPORT_CANDIDATE", "COUNTEREVIDENCE", "VALID_NULL", "INCONCLUSIVE",
            "HETEROGENEOUS", "INSTRUMENT_FAILED", "VOID", "NOT_RUN")
PURSUIT = ("OPENED", "PROMISING", "STALLED", "EXHAUSTED", "PROMOTE")
WARRANT = ("NONE", "INSTRUMENT_ONLY", "BOUNDED_MODEL_EFFECT", "CONFIRMATION_CANDIDATE",
           "CONFIRMED_MODEL_BOUNDED")
SPLITS = ("pilot", "discovery", "confirmation")
ACCESS_LEVELS = ("artifact_only", "artifact_plus_context", "unordered_process",
                 "ordered_history", "oracle_latent")
CARDS = ["I01", "I02", "I03", "C01", "C02", "C03", "A01", "A02", "A03",
         "T01", "T02", "T03", "H01", "H02", "H03", "P01", "P02", "F01"]
TRACK_OF = {c: {"I": "integrity", "C": "context", "A": "appraisal", "T": "transmission",
                "H": "hierarchy", "P": "physical", "F": "confirmation"}[c[0]] for c in CARDS}
# the GPU-work preservation order (§5.2) and the CPU card list live on the card
# registry (runners/s4_cards.py), their one home

DEFAULT_THRESHOLDS = {"balanced_accuracy": 0.05, "log_score_nats": 0.03,
                      "true_advice_loss_pp": 0.03}

SEED_CONTRACT = {
    "stage": STAGE,
    "reviewed_commit": "858f83ae2ea8cc607a5d43ae33cc8646a1f1caca",
    "run_duration_hours": 24,
    "duration_basis": "elapsed_wall_clock",
    "continuous_run": True,
    "deadline_persists_on_resume": True,
    "gpu_run_budget_hours": 24,
    "curator_packet_policy": "final_only",
    "early_curator_packets": False,
    "daily_curator_packets": False,
    "confirmation_and_closure_start_hour": 20,
    "physical_cpu_budget_hours": 2,
    "other_cpu_budget_hours": 4,
    "max_cpu_workers": 2,
    "max_substantive_confirmations": 2,
    "default_discovery_worlds_per_domain": 64,
    "default_confirmation_worlds_per_domain": 128,
    "default_domains": 2,
    "construction_seeds": 3,
    "cards": list(CARDS),
    "late_split_of_old_data_is_confirmation": False,
    "oracle_bypass_is_end_to_end_success": False,
    "old_stage3_debts_closed_by_new_scope": False,
    "cloud_or_paid_api_authorized": False,
}


# ── small utilities ───────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _json_default(o):
    """numpy scalars and arrays serialize as their Python values (an H03 metrics file
    died on an int64 inside a set intersection during the smoke); anything else is a
    real error."""
    try:
        import numpy as np                                                        # noqa: PLC0415
    except ImportError:                                                           # pragma: no cover
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def write_json(p: Path, obj) -> None:
    """Atomic write via a temp file. On Windows the final replace fails with a sharing
    violation while another process holds the target open for reading (the live run's
    freeze cell died once this way while a CPU card was loading the lineage file, and
    the scheduler's retry carried it); the replace is retried for a few seconds before
    the error is raised."""
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=_json_default),
                   encoding="utf-8", newline="\n")
    for attempt in range(20):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.25)


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def append_jsonl(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, default=_json_default) + "\n")


def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


class ContractError(RuntimeError):
    pass


class PacketGuard(RuntimeError):
    """The final packet was requested before the run's contract allowed it."""


class FreshnessViolation(RuntimeError):
    """A lineage that was inspected or used for fitting was claimed as fresh."""


class SplitViolation(RuntimeError):
    """A derived item would cross the discovery/confirmation boundary."""


class RealizationError(RuntimeError):
    """An assigned instruction was offered as ground truth without a realized choice."""


# ── the run contract ──────────────────────────────────────────────────────────────────

class RunContract:
    PATH = S4 / "RUN_CONTRACT.json"

    def __init__(self, data: dict, path: Path | None = None):
        self.data = data
        self.path = path or self.PATH

    @classmethod
    def load(cls, path: Path | None = None) -> "RunContract | None":
        p = path or cls.PATH
        if not p.exists():
            return None
        return cls(read_json(p), p)

    @classmethod
    def create(cls, extra: dict | None = None, path: Path | None = None) -> "RunContract":
        p = path or cls.PATH
        if p.exists():
            return cls.load(p)
        data = dict(SEED_CONTRACT)
        data.update({"contract_version": CONTRACT_VERSION, "created_at": now_iso(),
                     "frozen": {}, "lost_time": [], "run_hours": RUN_HOURS,
                     "closure_hour": CLOSURE_HOUR, "thresholds": dict(DEFAULT_THRESHOLDS),
                     "gear": "second (his call 2026-08-27)"})
        if extra:
            data.update(extra)
        c = cls(data, p)
        c.save()
        return c

    def save(self) -> None:
        write_json(self.path, self.data)

    # timing: written once; a restart keeps it (verification 10)
    def start(self) -> None:
        if self.data.get("execution_start_epoch") is None:
            t = time.time()
            self.data["execution_start_epoch"] = t
            self.data["execution_start"] = now_iso()
            self.data["deadline_epoch"] = t + self.data["run_hours"] * 3600
            self.data["deadline"] = time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.localtime(self.data["deadline_epoch"]))
            self.save()

    @property
    def started(self) -> bool:
        return self.data.get("execution_start_epoch") is not None

    def elapsed_h(self, now: float | None = None) -> float:
        if not self.started:
            return 0.0
        return ((now or time.time()) - self.data["execution_start_epoch"]) / 3600

    def remaining_h(self, now: float | None = None) -> float:
        return max(0.0, self.data["run_hours"] - self.elapsed_h(now))

    @property
    def stops_at_deadline(self) -> bool:
        """Second gear has no time window: it runs until the queue is empty (his standing
        ruling, 2026-08-28). The 24-hour deadline stays in the contract as ACCOUNTING (elapsed
        against the brief's window is still reported) and stops nothing unless a contract
        sets stop_at_deadline true explicitly."""
        return bool(self.data.get("stop_at_deadline", False))

    def deadline_passed(self, now: float | None = None) -> bool:
        """True only when the contract stops at its deadline and that time has come; the
        accounting question (has the window elapsed) is window_elapsed()."""
        return self.stops_at_deadline and self.window_elapsed(now)

    def window_elapsed(self, now: float | None = None) -> bool:
        return self.started and (now or time.time()) >= self.data["deadline_epoch"]

    def closure_due(self, now: float | None = None) -> bool:
        """The closure block (F01) begins at the closure hour under a windowed contract; under
        run-until-empty it begins when the admitted work and the ladder are exhausted, which
        the scheduler detects itself."""
        return self.stops_at_deadline and self.started and self.elapsed_h(now) >= self.data["closure_hour"]

    def record_lost_time(self, reason: str, seconds: float) -> None:
        self.data.setdefault("lost_time", []).append(
            {"at": now_iso(), "reason": reason, "seconds": round(seconds, 1)})
        self.save()

    # freezing: a substantive definition is written once; changing it needs a new version
    def freeze(self, section: str, payload) -> str:
        frozen = self.data.setdefault("frozen", {})
        h = sha256_text(canonical(payload))
        if section in frozen:
            if frozen[section]["hash"] == h:
                return h
            raise ContractError(
                f"{section} is frozen at {frozen[section]['hash'][:12]}; a changed "
                f"definition needs a new contract version and resets confirmation "
                f"eligibility (brief I03)")
        frozen[section] = {"hash": h, "frozen_at": now_iso(), "payload": payload}
        self.save()
        return h

    def frozen(self, section: str):
        f = self.data.get("frozen", {}).get(section)
        return None if f is None else f["payload"]

    def hash(self) -> str:
        volatile = {"lost_time", "created_at"}
        core = {k: v for k, v in self.data.items() if k not in volatile}
        return sha256_text(canonical(core))[:16]

    def duration_report(self, gpu_lock_seconds: float) -> dict:
        el = self.elapsed_h()
        lost = sum(x["seconds"] for x in self.data.get("lost_time", [])) / 3600
        return {"elapsed_hours": round(el, 3),
                "gpu_lock_held_hours": round(gpu_lock_seconds / 3600, 3),
                "lost_hours_recorded": round(lost, 3),
                "run_hours_contract": self.data["run_hours"],
                "completed_full_window": self.window_elapsed(),
                "stops_at_deadline": self.stops_at_deadline}


RUN_LABELS = ("COMPLETE_24H", "SHORT_RUN", "RUN_TO_EMPTY")


def validate_run_label(contract: RunContract, label: str) -> None:
    """Verification 10: a short run may not be labeled a completed 24-hour run; a
    run-until-empty run carries its own label with the elapsed hours beside it."""
    if label == "COMPLETE_24H" and not contract.window_elapsed():
        raise ContractError("run labeled COMPLETE_24H before its window elapsed; use SHORT_RUN")
    if label not in RUN_LABELS:
        raise ContractError(f"unknown run label {label!r}")


# ── source lineages ───────────────────────────────────────────────────────────────────

LINEAGE_LOCK_TIMEOUT_S = 60.0
LINEAGE_LOCK_STALE_S = 120.0


class Lineages:
    """The source-lineage ledger. Every mutation is a LOCK-HELD RELOAD-MODIFY-WRITE: the
    2026-08-28 concurrency audit found the lost-update shape (each runner held a whole-file
    snapshot from its own start-up and wrote the whole dict back, the same class _fresh()
    closes for RunContract). It had not fired, because no two lineage-writing cards ever
    overlapped; this makes it unable to. The in-memory rows are a cache that every
    mutation refreshes; rows are never deleted, so a merge is add-missing with the
    file's flags winning."""
    PATH = S4 / "SOURCE_LINEAGES.json"

    def __init__(self, path: Path | None = None):
        self.path = path or self.PATH
        self.rows: dict[str, dict] = read_json(self.path) if self.path.exists() else {}

    def reload(self) -> "Lineages":
        self.rows = read_json(self.path) if self.path.exists() else {}
        return self

    def _transact(self, fn) -> None:
        lock = self.path.with_name(self.path.name + ".lock")
        t0 = time.time()
        while True:
            try:
                fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except FileExistsError:
                try:
                    age = time.time() - lock.stat().st_mtime
                except OSError:
                    age = 0.0
                if age > LINEAGE_LOCK_STALE_S:
                    try:
                        lock.unlink()
                    except OSError:
                        pass
                    continue
                if time.time() - t0 > LINEAGE_LOCK_TIMEOUT_S:
                    raise ContractError(f"{lock} held for over {LINEAGE_LOCK_TIMEOUT_S:g}s; "
                                        f"nothing was written")
                time.sleep(0.05)
        try:
            fresh: dict[str, dict] = read_json(self.path) if self.path.exists() else {}
            for lid, r in self.rows.items():
                fresh.setdefault(lid, r)
            fn(fresh)
            write_json(self.path, fresh)
            self.rows = fresh
        finally:
            try:
                lock.unlink()
            except OSError:
                pass

    def save(self) -> None:
        self._transact(lambda rows: None)

    @staticmethod
    def make_id(card: str, domain: str, seed: int, world: int, split: str) -> str:
        return f"{card}|{domain}|s{seed}|w{world:04d}|{split}"

    def allocate(self, card: str, domain: str, seeds: list[int], n_worlds: int,
                 split: str, world_offset: int = 0) -> list[str]:
        """Allocate n_worlds lineage ids for a card/domain, round-robin over seeds,
        with the split fixed here and never changed. Returns the ids in world order."""
        assert split in SPLITS, split
        out = []
        for i in range(n_worlds):
            w = world_offset + i
            out.append(self.make_id(card, domain, seeds[i % len(seeds)], w, split))

        def add(rows):
            for i, lid in enumerate(out):
                if lid not in rows:
                    rows[lid] = {"id": lid, "card": card, "domain": domain,
                                 "construction_seed": seeds[i % len(seeds)],
                                 "world_index": world_offset + i,
                                 "split": split, "allocated_at": now_iso(),
                                 "generation_hash": None, "fit_use": [],
                                 "inspected": False, "confirmation_access": None,
                                 "parent": None}
        self._transact(add)
        return out

    def derive(self, parent: str, tag: str, card: str | None = None) -> str:
        """A paraphrase, hop, edit, or reader variant of a world stays in its split and
        cluster (§6.2). The child's id carries the parent's id; a card that reuses another
        card's worlds (A02 on A01's, T02 on T01's) gets children carrying its own card
        name so the cluster is shared and the tests are never counted as independent."""
        lid = f"{parent}|{tag}"
        if lid in self.rows:
            return lid

        def add(rows):
            p = rows[parent]
            if lid not in rows:
                rows[lid] = {**p, "id": lid, "parent": parent, "generation_hash": None,
                             "fit_use": [], "inspected": False,
                             "allocated_at": now_iso(), "card": card or p["card"]}
        self._transact(add)
        return lid

    def check_same_split(self, a: str, b: str) -> None:
        if self.rows[a]["split"] != self.rows[b]["split"]:
            raise SplitViolation(f"{a} ({self.rows[a]['split']}) and {b} "
                                 f"({self.rows[b]['split']}) may not be joined")

    def mark_generated(self, lid: str, content_hash: str) -> None:
        """Record the construction's content hash (verification 3). Idempotent: an
        unchanged hash costs no write."""
        if self.rows.get(lid, {}).get("generation_hash") == content_hash:
            return

        def mark(rows):
            rows[lid]["generation_hash"] = content_hash
        self._transact(mark)

    def mark_inspected(self, lids) -> None:
        lids = list(lids)

        def mark(rows):
            for lid in lids:
                rows[lid]["inspected"] = True
        self._transact(mark)

    def mark_fit_use(self, lids, what: str) -> None:
        lids = list(lids)

        def mark(rows):
            for lid in lids:
                rows[lid]["fit_use"].append(what)
        self._transact(mark)

    def check_fresh(self, lids) -> None:
        """Verification 4: a lineage that was inspected or fit on is never fresh."""
        for lid in lids:
            r = self.rows[lid]
            if r["inspected"] or r["fit_use"] or r["split"] != "confirmation":
                raise FreshnessViolation(
                    f"{lid}: inspected={r['inspected']} fit_use={r['fit_use']} "
                    f"split={r['split']}")

    def open_confirmation(self, lids, who: str) -> None:
        lids = list(lids)
        self.reload()
        self.check_fresh(lids)

        def mark(rows):
            for lid in lids:
                rows[lid]["confirmation_access"] = {"by": who, "at": now_iso()}
        self._transact(mark)

    def duplicate_content(self) -> list[tuple[str, str]]:
        """Verification 3: two lineages with identical generated content are one unit.
        Meaningful only where generation_coverage() says the card is checked."""
        seen: dict[str, str] = {}
        dups = []
        for lid, r in sorted(self.rows.items()):
            h = r.get("generation_hash")
            if not h or r.get("parent"):
                continue
            if h in seen:
                dups.append((seen[h], lid))
            else:
                seen[h] = lid
        return dups

    def generation_coverage(self) -> dict:
        """Per card and split: how many root lineages carry a content hash, how many
        distinct hashes, and whether the duplicate control was able to look at every unit
        of that split (a discovery card is checked once its discovery roots are all hashed;
        its confirmation reserve is a separate line, hashed only when F01 generates it).
        The 2026-08-28 audit found the control returning no duplicates because nothing had
        ever been marked; a packet must say checked or not checked, never infer."""
        by: dict = {}
        for lid, r in self.rows.items():
            if r.get("parent"):
                continue
            c = by.setdefault(f"{r['card']}|{r['split']}", {"roots": 0, "hashed": 0, "hashes": set()})
            c["roots"] += 1
            if r.get("generation_hash"):
                c["hashed"] += 1
                c["hashes"].add(r["generation_hash"])
        return {card: {"roots": c["roots"], "hashed": c["hashed"],
                       "distinct": len(c["hashes"]),
                       "duplicates": c["hashed"] - len(c["hashes"]),
                       "checked": c["hashed"] == c["roots"] and c["roots"] > 0}
                for card, c in sorted(by.items())}


# ── the queue manifest ────────────────────────────────────────────────────────────────

class Manifest:
    PATH = S4 / "QUEUE_MANIFEST.json"

    def __init__(self, path: Path | None = None):
        self.path = path or self.PATH
        self.cells: dict[str, dict] = read_json(self.path) if self.path.exists() else {}

    def save(self) -> None:
        write_json(self.path, self.cells)

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

    def set_exec(self, cell_id: str, state: str, reason: str | None = None) -> None:
        assert state in EXEC_STATES, state
        c = self.cells[cell_id]
        c["exec_state"] = state
        if reason is not None:
            c["reason"] = reason
        if state == "RUNNING":
            c["started_at"] = now_iso()
            c["attempts"] += 1
        if state in ("COMPLETE", "FAILED", "BLOCKED", "DEFERRED"):
            c["finished_at"] = now_iso()
        self.save()

    def set_outcome(self, cell_id: str, outcome: str, detail=None) -> None:
        assert outcome in OUTCOMES, outcome
        self.cells[cell_id]["outcome"] = outcome
        if detail is not None:
            self.cells[cell_id]["detail"] = detail
        self.save()

    def charge(self, cell_id: str, minutes: float, gpu_lock_minutes: float = 0.0) -> None:
        c = self.cells[cell_id]
        c["budget_charged_min"] = round(c["budget_charged_min"] + minutes, 2)
        c["gpu_lock_min"] = round(c["gpu_lock_min"] + gpu_lock_minutes, 2)
        self.save()

    def deps_complete(self, cell_id: str) -> bool:
        return all(self.cells[d]["exec_state"] == "COMPLETE"
                   for d in self.cells[cell_id]["depends_on"])

    def deps_dead(self, cell_id: str) -> bool:
        return any(self.cells[d]["exec_state"] in ("FAILED", "BLOCKED", "DEFERRED")
                   for d in self.cells[cell_id]["depends_on"])

    def state_counts(self) -> dict:
        out: dict[str, int] = {}
        for c in self.cells.values():
            out[c["exec_state"]] = out.get(c["exec_state"], 0) + 1
        return out

    def total_gpu_lock_seconds(self) -> float:
        return sum(c["gpu_lock_min"] for c in self.cells.values()) * 60


# ── provenance rows ───────────────────────────────────────────────────────────────────

@dataclass
class ProvenanceRow:
    card: str
    cell_id: str
    unit_id: str                  # independent unit (world / chain / drawing)
    lineage_id: str
    split: str
    model_id: str
    model_revision: str
    construction_seed: int
    treatment: str
    factors: dict
    attempted: bool
    realized: bool
    valid: bool
    validity_reason: str
    truth: str | dict | None
    truth_provenance: str         # "realized_draw" | "realized_choice" | "construction" | ...
    access_level: str
    raw_ref: str | None
    label_mapping: dict
    parser_version: str
    probs: dict | None
    primary_score: float | None
    intervention: dict | None
    code_hash: str
    contract_hash: str
    compute_charged_s: float
    extra: dict = field(default_factory=dict)

    def validate(self) -> None:
        assert self.split in SPLITS, self.split
        assert self.access_level in ACCESS_LEVELS, self.access_level
        if self.truth is not None and self.truth_provenance == "assigned_instruction":
            raise RealizationError(
                f"{self.unit_id}: an assigned instruction is not ground truth (L137)")

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)


def require_realized_truth(row: dict) -> None:
    """Verification 6, on a stored row: truth provenance must be a realized draw or
    realized choice or the construction's own known process, never an assignment."""
    prov = row.get("truth_provenance")
    if prov not in ("realized_draw", "realized_choice", "construction", "recorded_human",
                    "recorded_drawing"):
        raise RealizationError(f"row {row.get('unit_id')}: truth provenance {prov!r}")


def code_hash(*paths: Path) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(Path(p).read_bytes())
    return h.hexdigest()[:16]


# ── GPU-lock metering ─────────────────────────────────────────────────────────────────

class GpuMeter:
    """Accumulates seconds the GPU lock was HELD by this process for a cell, written to
    the manifest by the caller. Elapsed wall time (waits included) is the contract's."""

    def __init__(self):
        self.held_s = 0.0
        self._t0 = None

    def __enter__(self):
        self._t0 = time.time()
        return self

    def __exit__(self, *exc):
        self.held_s += time.time() - self._t0
        self._t0 = None
        return False


# ── completion markers ────────────────────────────────────────────────────────────────

def completion_marker(inputs: dict, outputs: dict, contract: RunContract) -> dict:
    """A verdict's marker: the contract version and hash plus hashes of every input and
    output file it depends on (verification: markers are checked against data, never a
    bare exists())."""
    return {"contract_version": contract.data.get("contract_version"),
            "contract_hash": contract.hash(),
            "inputs": {k: {"path": str(v), "sha256": sha256_file(Path(v))}
                       for k, v in inputs.items()},
            "outputs": {k: {"path": str(v), "sha256": sha256_file(Path(v))}
                        for k, v in outputs.items()},
            "written_at": now_iso()}


PASS_VERDICTS = ("PASS", "GATE-PASSED", "ANCHOR-STANDS", "STANDS")


def verdict_gate(path: Path, key: str = "gate_pass") -> bool:
    """Verification 7: a downstream gate is the prerequisite's VERDICT, read from the
    file's content; a present file whose verdict failed does not license anything."""
    p = Path(path)
    if not p.exists():
        return False
    try:
        d = read_json(p)
    except Exception:                                                            # noqa: BLE001
        return False
    if key in d:
        return bool(d[key])
    return str(d.get("verdict", "")).upper() in PASS_VERDICTS


def check_marker(verdict: dict) -> list[str]:
    """Returns the list of mismatches (empty means the marker verifies)."""
    m = verdict.get("marker")
    if not m:
        return ["no marker"]
    bad = []
    for group in ("inputs", "outputs"):
        for k, rec in m.get(group, {}).items():
            p = Path(rec["path"]) if isinstance(rec, dict) else Path(k)
            h = rec["sha256"] if isinstance(rec, dict) else rec
            if not p.exists():
                bad.append(f"{group}:{k} missing")
            elif sha256_file(p) != h:
                bad.append(f"{group}:{k} hash changed")
    return bad


# ── outcome classification (§8.3): exhaustive bands, no silent interval ───────────────

def classify_outcome(point: float, ci_low: float, ci_high: float,
                     threshold: float) -> tuple[str, str]:
    """Positive direction is the predicted direction. Bands, checked in order:
      COUNTEREVIDENCE     ci_high < 0                (the interval sits on the wrong side)
      SUPPORT_CANDIDATE   ci_low > 0 and point >= threshold
      INCONCLUSIVE        ci_low > 0 and point < threshold (directional but small; the
                          interval may still reach the threshold)   [reported as such]
      VALID_NULL          ci_low <= 0 and ci_high < threshold (a useful benefit excluded)
      INCONCLUSIVE        ci_low <= 0 and ci_high >= threshold (cannot exclude a useful
                          effect, cannot confirm direction)
    Every (point, ci) lands in exactly one band."""
    assert ci_low <= point <= ci_high or abs(ci_low - ci_high) < 1e-12, (
        point, ci_low, ci_high)
    if ci_high < 0:
        return "COUNTEREVIDENCE", "interval entirely below zero"
    if ci_low > 0:
        if point >= threshold:
            return "SUPPORT_CANDIDATE", "directional support at or above the frozen threshold"
        return "INCONCLUSIVE", "directional support below the practical threshold"
    if ci_high < threshold:
        return "VALID_NULL", "interval includes zero and excludes a practically useful benefit"
    return "INCONCLUSIVE", "interval includes zero and cannot exclude a useful benefit"


def exceeds_threshold_supported(ci_low: float, threshold: float) -> bool:
    """§8.1: the stronger statement (effect exceeds the practical threshold) only when the
    interval's lower bound clears it."""
    return ci_low >= threshold


# ── aggregation (verification 5) ──────────────────────────────────────────────────────

def aggregate_equal(rows, unit_key, group_key, value_key) -> dict:
    """Mean of per-unit means within each group: every eligible row for a unit is
    averaged first (equal weight per reader/variant), then units are averaged. Invariant
    to row order by construction; no dictionary overwrite can select a reader."""
    per_unit: dict = {}
    for r in rows:
        per_unit.setdefault(r[group_key], {}).setdefault(r[unit_key], []).append(
            float(r[value_key]))
    out = {}
    for g, units in per_unit.items():
        means = sorted(sum(v) / len(v) for v in units.values())
        out[g] = {"n_units": len(means), "mean": sum(means) / len(means),
                  "rows": sum(len(v) for v in units.values())}
    return out


# ── expected cells and coverage ───────────────────────────────────────────────────────

def expand_expected_cells(spec: dict) -> list[dict]:
    """spec: {card: {"factors": {name: [levels]}, "domains": [...], "n_units": int,
    "controls": [names]}} -> the fully expanded factorial including control cells."""
    cells = []
    for card, s in spec.items():
        names = list(s["factors"])
        levels = [s["factors"][n] for n in names]

        def rec(i, cur):
            if i == len(names):
                cells.append({"card": card, "factors": dict(cur)})
                return
            for lv in levels[i]:
                cur[names[i]] = lv
                rec(i + 1, cur)
                del cur[names[i]]
        for dom in s["domains"]:
            base = {"domain": dom}
            rec(0, dict(base)) if names else cells.append({"card": card, "factors": base})
        for ctl in s.get("controls", []):
            for dom in s["domains"]:
                cells.append({"card": card, "factors": {"domain": dom, "control": ctl}})
        for c in cells:
            if c["card"] == card:
                c["n_units_required"] = s["n_units"]
    return cells


def validate_expected(spec: dict, expanded: list[dict]) -> list[str]:
    """Verification 2: every factorial corner, domain, and control must be present."""
    want = expand_expected_cells(spec)
    key = lambda c: canonical({"card": c["card"], "factors": c["factors"]})   # noqa: E731
    have = {key(c) for c in expanded}
    return [key(c) for c in want if key(c) not in have]


def coverage(expected: list[dict], realized_counts: dict) -> dict:
    """realized_counts: cell key -> {attempted, realized, valid, scored}. Returns the
    COVERAGE structure with every missing or under-floor cell listed."""
    key = lambda c: canonical({"card": c["card"], "factors": c["factors"]})   # noqa: E731
    missing, under, ok = [], [], 0
    for c in expected:
        k = key(c)
        rc = realized_counts.get(k)
        if not rc:
            missing.append(k)
        elif rc.get("scored", 0) < c["n_units_required"]:
            under.append({"cell": k, "scored": rc.get("scored", 0),
                          "required": c["n_units_required"]})
        else:
            ok += 1
    return {"expected": len(expected), "complete": ok, "missing": missing,
            "under_floor": under, "written_at": now_iso()}


# ── claim ledger and the packet guard ─────────────────────────────────────────────────

class ClaimLedger:
    PATH = S4 / "CLAIM_LEDGER.json"

    def __init__(self, path: Path | None = None):
        self.path = path or self.PATH
        self.claims: list[dict] = read_json(self.path) if self.path.exists() else []

    def add(self, card: str, estimand: str, outcome: str, strongest_rival: str,
            scope: str, pursuit: str, warrant: str, public_wording: str,
            detail: dict | None = None) -> None:
        assert outcome in OUTCOMES and pursuit in PURSUIT and warrant in WARRANT
        self.claims.append({"card": card, "estimand": estimand, "outcome": outcome,
                            "strongest_rival": strongest_rival, "scope": scope,
                            "pursuit": pursuit, "warrant": warrant,
                            "public_wording": public_wording, "detail": detail or {},
                            "at": now_iso()})
        write_json(self.path, self.claims)


def packet_allowed(contract: RunContract, exhausted: bool) -> bool:
    """§5.3 / verification 11: only after a windowed contract's deadline, or on recorded
    exhaustion of all admitted work and its expansion ladder (the run-until-empty end)."""
    return contract.started and (contract.deadline_passed() or exhausted)


def write_packet(text: str, contract: RunContract, exhausted: bool,
                 path: Path | None = None) -> Path:
    if not packet_allowed(contract, exhausted):
        raise PacketGuard("the final packet is the only curator packet and the run's "
                          "deadline has not passed (and no exhaustion is recorded)")
    p = path or (S4 / "CURATOR_PACKET_FINAL.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def refuse_interim_packet(kind: str) -> None:
    raise PacketGuard(f"{kind} packets are disabled for this run (final_only)")
