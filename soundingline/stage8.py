"""Stage 8 shared schema and bookkeeping (brief: docs/design/PHASE_2_4_STAGE_8_CONTEXT.md).

Built ON the Stage 7 machinery (soundingline/stage7.py), never beside it: the Stage 8 launcher
sets S7_STAGE=phase_2_4_stage_8 (and the 48-hour ceiling through S7_RUN_HOURS) so every Stage 7
record class, capsule path, registry, and validator resolves under results/phase_2_4_stage_8.
This module adds what the brief adds: the 44 questions and 12 attacks over seven trunks, the
reader and arm codes of §4, the useful-work target (36 to 42 hours under a 48-hour ceiling,
§12), the closure hour (the confirmation freeze, the ceiling minus the closure reserve), the
new registries (adapters, training curves, tail thresholds, the frontier dollar ledger with
its hard cap, the theory-change interrupts, the re-lock, the testbed), the Stage 8 manifest
(its own track map), and the seed contract with the reviewed heads.

Stage 1 to 7 code and raw results stay immutable: the registry list is EXTENDED at import by
rebinding the Stage 7 module's tuple (its writer reads the global at call time), and nothing in
runners/stage7 is edited.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3 (blind floors follow the truth marginal: every ratio and gap here is
  void under the minimum gap, never re-thresholded; a criterion must be able to fail: the
  frontier cap is a hard stop tested by the guard suite with a planted overspend), §5 (one
  manifest writer; produces guards; the deadline persists across restarts; the ledger cell
  runs after what it counts).
gates: the frontier cap: NULL (an overspend attempt) is a call whose projected dollars would
  cross the cap and it RAISES before the request (fails DOWN: the cell closes INSTRUMENT_FAILED
  at the cap, never over it); ALTERNATIVE: the projected total stays under the cap and the call
  proceeds. The ratio void rule as in Stage 7 (denominator under 0.05 nats gives None).
bands: exhaustive (under the cap / at the cap; None under the floor / a number at it).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from soundingline import stage7 as S7M
from soundingline.stage7 import (EXEC_STATES, OUTCOMES7, SPLITS, ContractError,        # noqa: F401
                                 Lineages7, Manifest, PacketGuard, RunContract7,
                                 aggregate_equal, append_jsonl, canonical,
                                 canonical_prediction, prediction_sha, classify_outcome, code_hash, completion_marker,
                                 evidence_sha, gate_state, ghost_status, now_iso,
                                 normalize, oracle_gap, read_json, read_jsonl,
                                 read_registry, set_gate, sha256_file, sha256_text,
                                 tv, update_registry, validate_prediction,
                                 validate_visible_evidence, write_json, write_registry)

__all__ = ["S8", "STAGE", "RUN_HOURS", "CLOSURE_HOUR", "FLOOR_HOUR", "USEFUL_TARGET_H", "SMOKE",
           "MIN_GAP_NATS", "DEFAULT_GAIN_FLOOR", "EXPERTISE_BAND_NATS", "GENERATION_PERCENTILE",
           "TAIL_PERCENTILE", "FRONTIER_CAP_USD", "QUESTIONS", "ATTACKS", "TRUNKS", "TRACK_OF",
           "SYSTEMS", "PURPOSES", "SHAPES", "SEED_CONTRACT", "RunContract8", "Manifest8", "Lineages8",
           "card_dir", "write_packet", "refuse_packet_path", "frontier_charge", "FrontierCap",
           "record_interrupt", "interrupts", "adapter_hash", "EXEC_STATES", "OUTCOMES7", "SPLITS",
           "ContractError", "PacketGuard", "RunContract7", "aggregate_equal", "append_jsonl",
           "canonical", "canonical_prediction", "prediction_sha", "classify_outcome", "code_hash", "completion_marker", "evidence_sha",
           "gate_state", "ghost_status", "now_iso", "normalize", "oracle_gap", "read_json",
           "read_jsonl", "read_registry", "set_gate", "sha256_file", "sha256_text", "tv",
           "update_registry", "validate_prediction", "validate_visible_evidence", "write_json",
           "write_registry"]

REPO = Path(__file__).resolve().parents[1]
STAGE = "phase_2_4_stage_8"
S8 = S7M.S7                                       # the launcher points S7_STAGE here; tests use S7_ROOT
RUN_HOURS = float(os.environ.get("S7_RUN_HOURS", "48"))
CLOSURE_HOUR = float(os.environ.get("S7_CLOSURE_HOUR", "40"))     # the freeze: ceiling minus the closure reserve
FLOOR_HOUR = 36.0                                                 # exhausting earlier is SHORT (§12.2)
USEFUL_TARGET_H = (36.0, 42.0)
SMOKE = bool(os.environ.get("S7_SMOKE"))
MIN_GAP_NATS = S7M.MIN_GAP_NATS
DEFAULT_GAIN_FLOOR = S7M.DEFAULT_GAIN_FLOOR                       # a fifth of the relevant gap (§6)
EXPERTISE_BAND_NATS = 0.05                                        # E03: FM within DOM - 0.05 nats
GENERATION_PERCENTILE = 20                                        # E04: at or above the real logs' 20th percentile
TAIL_PERCENTILE = 80                                              # tau: the 80th percentile of the POP per-event gap
FRONTIER_CAP_USD = 40.0                                           # §12.5, a hard stop

# ── the question inventory (§7): seven trunks, 44 questions, 12 attacks ─────────────
TRUNKS = {"I": 8, "E": 8, "D": 6, "G": 8, "A": 5, "T": 5, "B": 4}
QUESTIONS = [f"{t}{i:02d}" for t, n in TRUNKS.items() for i in range(1, n + 1)]
assert len(QUESTIONS) == 44, len(QUESTIONS)
ATTACKS = [f"X{i:02d}" for i in range(1, 13)]
TRACK_OF = {q: {"I": "isolation", "E": "expertise", "D": "difference", "G": "purpose",
                "A": "accumulation", "T": "testbed", "B": "closure"}[q[0]] for q in QUESTIONS}
TRACK_OF.update({a: "attack" for a in ATTACKS})

# ── the systems (§4) ─────────────────────────────────────────────────────────────────
SYSTEMS = ("U", "PERS", "DOM", "DIR0", "FM", "FMP", "FMN", "SOL", "FR", "OR")
SYSTEM_NAMES = {"U": "uniform over the live option set", "PERS": "persistence and position",
                "DOM": "the frozen common-domain model, refit on the population corpus",
                "DIR0": "the Stage 7 direct reader, untrained, letter readout",
                "FM": "the trained forward-model reader (a low-rank adapter on the base reader, trained on population process logs; generative option readout)",
                "FMP": "the forward model conditioned on an inferred or supplied purpose",
                "FMN": "the forward model with N earlier artifacts of the same maker in context",
                "SOL": "the capsule solver executing a supplied state (the Stage 7 ceiling comparator; tail contrast only)",
                "FR": "the frontier probe: one API reasoning model, thinking on, one-call verbalized distribution, capped in dollars",
                "OR": "the exact oracle (construction ceiling, never a reader)"}
PURPOSES = ("persuade", "document", "explore", "teach")
SHAPES = ("structured", "essay", "free")                          # the artful gradient (§5)

SEED_CONTRACT = {
    "stage": STAGE,
    "reviewed_commit": "41eab74e",
    "ghost_reviewed_commit": "ce4c06b",
    "brief": "docs/design/PHASE_2_4_STAGE_8_CONTEXT.md",
    "run_duration_hours": 48,
    "useful_work_target_hours": list(USEFUL_TARGET_H),
    "duration_basis": "elapsed_wall_clock_from_pilot_start",
    "continuous_run": True,
    "stop_at_deadline": True,
    "deadline_is_accounting_only": False,
    "run_until_queue_empty": True,
    "short_run_floor_hour": FLOOR_HOUR,
    "deadline_persists_on_resume": True,
    "curator_packet_policy": "final_only_after_closure_and_validation",
    "early_curator_packets": False,
    "confirmation_freeze_hour": CLOSURE_HOUR,
    "max_substantive_confirmations": 3,
    "max_cpu_workers_while_ghost_live": 2,
    "isolation_mechanism": "interpreter capsule (his ruling 2026-09-02), interpreter-level; the adapters are loaded by the loopback server from a frozen path whose hash is in the manifest and in every response (the capsule imports no torch)",
    "external_sources_policy": "read-only clones in the sibling reference workspace, pinned; corpora as manifests under the fetch discipline; never vendored, never on a capsule path",
    "questions": list(QUESTIONS),
    "attacks": list(ATTACKS),
    "systems": list(SYSTEMS),
    "purposes": list(PURPOSES),
    "shapes": list(SHAPES),
    "lanes": list(SPLITS),
    "oracle_gap_floor": DEFAULT_GAIN_FLOOR,
    "min_gap_nats": MIN_GAP_NATS,
    "expertise_band_nats": EXPERTISE_BAND_NATS,
    "generation_percentile": GENERATION_PERCENTILE,
    "tail_percentile": TAIL_PERCENTILE,
    "frontier_cap_usd": FRONTIER_CAP_USD,
    "frontier_provider": "Gemini (the one key present; the cheapest thinking-capable model that passes the pilot's calibration fixture)",
    "training_policy": "only the population's standard process is installed (makers marginalized by sampling; purposes and the four Stage 7 goals in the goal slot; the artful shapes; earlier-artifact contexts by fresh sampled makers); nothing maker-specific is ever trained in",
    "oracle_bypass_is_end_to_end_success": False,
    "pilot_outputs_promotable": False,
    "late_split_of_old_data_is_confirmation": False,
    "cloud_or_paid_api_authorized": "the frontier probe only, capped at 40 dollars, after the local readers' same cells",
    "agent_delegation_authorized": False,
    "human_participants_authorized": False,
    "ghost_v15_boundary": "read-only status, commit, and completion; no import of partial outcomes",
    "claim_class": "bounded model-reader capability under an expertise gate; goal-as-purpose recovery; surprise localization of the maker's share; accumulation across artifacts; testbed expansion",
}

# ── registries: Stage 7's plus the Stage 8 additions (rebinding the module global) ──
EXTRA_REGISTRIES = ("ADAPTERS", "TRAINING", "TAIL_THRESHOLDS", "FRONTIER_LEDGER", "INTERRUPTS",
                    "RELOCK", "TESTBED", "EXPERTISE_GATE", "GENERATION_GATE", "TESTBED_SOURCES",
                    "CORPUS_MANIFESTS", "CONSTRUCTION_FACTS", "POP_CORPUS")
S7M.REGISTRIES = tuple(S7M.REGISTRIES) + tuple(r for r in EXTRA_REGISTRIES if r not in S7M.REGISTRIES)


class RunContract8(RunContract7):
    PATH = S8 / "RUN_CONTRACT.json"

    @classmethod
    def create(cls, extra: dict | None = None, path: Path | None = None) -> "RunContract8":
        p = path or cls.PATH
        if p.exists():
            return cls.load(p)
        data = dict(SEED_CONTRACT)
        data.update({"contract_version": "8.0.0", "created_at": now_iso(), "frozen": {}, "lost_time": [],
                     "run_hours": RUN_HOURS, "closure_hour": CLOSURE_HOUR,
                     "gear": "second (his order 2026-09-04: build it, set it up, start running)"})
        if extra:
            data.update(extra)
        c = cls(data, p)
        c.save()
        return c

    @classmethod
    def load(cls, path: Path | None = None) -> "RunContract8 | None":
        p = path or cls.PATH
        if not p.exists():
            return None
        return cls(read_json(p), p)


class Lineages8(Lineages7):
    PATH = S8 / "SOURCE_LINEAGES.json"


class Manifest8(Manifest):
    PATH = S8 / "QUEUE_MANIFEST.json"

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


def card_dir(card: str) -> Path:
    p = S8 / card
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_packet(text: str, contract, exhausted: bool) -> Path:
    return S7M.write_packet(text, contract, exhausted)


def refuse_packet_path(path: Path) -> None:
    S7M.refuse_packet_path(path)


# ── the frontier dollar ledger (§12.5): counted per call, a hard stop at the cap ─────

class FrontierCap(RuntimeError):
    pass


def frontier_total() -> float:
    led = read_registry("FRONTIER_LEDGER") or {}
    return float(led.get("total_usd") or 0.0)


def frontier_charge(cell: str, model: str, tokens_in: int, tokens_out: int, tokens_thought: int,
                    price_in_per_m: float, price_out_per_m: float, projected: bool = False) -> float:
    """Charge one call to the ledger (or check a PROJECTED call before it is made). Raises
    FrontierCap when the total would cross the cap; nothing is charged past it."""
    usd = tokens_in / 1e6 * price_in_per_m + (tokens_out + tokens_thought) / 1e6 * price_out_per_m
    def upd(led):
        led = dict(led or {})
        total = float(led.get("total_usd") or 0.0)
        if total + usd > FRONTIER_CAP_USD:
            raise FrontierCap(f"the frontier cap ({FRONTIER_CAP_USD} USD) would be crossed: {total:.4f} + {usd:.4f}")
        if projected:
            return led
        led["total_usd"] = round(total + usd, 6)
        led["cap_usd"] = FRONTIER_CAP_USD
        led.setdefault("calls", []).append({"cell": cell, "model": model, "tokens_in": tokens_in, "tokens_out": tokens_out,
                                            "tokens_thought": tokens_thought, "usd": round(usd, 6), "at": now_iso()})
        led["calls"] = led["calls"][-5000:]
        by = led.setdefault("by_cell", {})
        by[cell] = round(float(by.get(cell, 0.0)) + usd, 6)
        return led
    update_registry("FRONTIER_LEDGER", upd)
    return usd


# ── theory-change interrupts (§9.1) ──────────────────────────────────────────────────

def record_interrupt(name: str, consequence: str, blocks: list[str], detail: dict | None = None) -> None:
    """The coding agent stops the gated branch, writes the theory-group consequence, and the
    packet carries it for the curator's ruling; everything not gated on it continues (an
    unattended two-day run cannot idle on a ruling)."""
    def upd(reg):
        reg = dict(reg or {})
        reg.setdefault("interrupts", []).append({"name": name, "consequence": consequence, "blocks": list(blocks),
                                                 "detail": detail or {}, "at": now_iso(), "ruled": False})
        return reg
    update_registry("INTERRUPTS", upd)


def interrupts() -> list[dict]:
    return list((read_registry("INTERRUPTS") or {}).get("interrupts") or [])


def adapter_hash(path: Path) -> str:
    """The hash of a frozen adapter directory: every file's bytes in sorted name order."""
    h = hashlib.sha256()
    p = Path(path)
    if p.is_file():
        return sha256_file(p)[:16]
    for f in sorted(x for x in p.rglob("*") if x.is_file()):
        h.update(f.name.encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()[:16]
