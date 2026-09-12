"""Public task and elicited forecast contracts.

DESIGN CHECK: LESSONS sections 2-5; CONTROLS section 6.
Under NULL and ALTERNATIVE, well-formed declared tasks and probability vectors
must parse identically. Unexpected fields, duplicate choices, incomplete support,
nonfinite probabilities and malformed replies must fail explicitly. These are
interface checks, not scientific success thresholds. No private evaluation
record is accepted by the model request function.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PublicTask:
    task_id: str
    family: str
    evidence_view: str
    evidence: dict
    question: str
    choices: tuple[tuple[str, str], ...]
    target_time: str
    contributor_role: str
    exposure: str

    def __post_init__(self):
        if not self.task_id or any(c not in "0123456789abcdef" for c in self.task_id) or len(self.task_id) != 32:
            raise ValueError("task_id must be an opaque 32-character hex identifier")
        if self.evidence_view not in {"artifact", "earlier-artifacts", "process-record"}:
            raise ValueError("undeclared evidence view")
        if not isinstance(self.evidence, dict) or not self.question or not self.target_time or not self.contributor_role:
            raise ValueError("incomplete task contract")
        if len(self.choices) < 2 or len({key for key, _ in self.choices}) != len(self.choices):
            raise ValueError("choices must have distinct identifiers and complete finite support")
        for key, description in self.choices:
            if not key.startswith("o_") or len(key) != 10 or any(c not in "0123456789abcdef" for c in key[2:]) or not description:
                raise ValueError("choices need opaque ids and explicit descriptions")
        canonical(self.public())

    def public(self) -> dict:
        # Identity, exposure and grouping stay out of the content shown to the reader.
        return {
            "schema": "stage10.public.1", "evidence_view": self.evidence_view,
            "evidence": self.evidence, "question": self.question,
            "choices": [{"id": key, "description": value} for key, value in self.choices],
            "target_time": self.target_time, "contributor_role": self.contributor_role,
        }


def choices_for(descriptions: list[str], seed: str) -> tuple[tuple[str, str], ...]:
    if len(set(descriptions)) != len(descriptions):
        raise ValueError("duplicate choice descriptions")
    # Stable per task, independent of the correct answer and shared across arms.
    pairs = [("o_" + digest([seed, value])[:8], value) for value in descriptions]
    return tuple(sorted(pairs))


def response_schema(task: PublicTask) -> dict:
    ids = [key for key, _ in task.choices]
    return {
        "type": "object", "additionalProperties": False,
        "required": ["choice", "probabilities", "explanation", "insufficient_evidence"],
        "properties": {
            "choice": {"type": "string", "enum": ids},
            "probabilities": {"type": "object", "additionalProperties": False,
                              "required": ids, "properties": {key: {"type": "number", "minimum": 0, "maximum": 1} for key in ids}},
            "explanation": {"type": "string", "maxLength": 600},
            "insufficient_evidence": {"type": "boolean"},
        },
    }


def parse_forecast(content: str, task: PublicTask) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    obj = json.loads(content, object_pairs_hook=unique)
    if not isinstance(obj, dict) or set(obj) != {"choice", "probabilities", "explanation", "insufficient_evidence"}:
        raise ValueError("unexpected or missing forecast fields")
    ids = {key for key, _ in task.choices}
    if obj["choice"] not in ids or not isinstance(obj["probabilities"], dict) or set(obj["probabilities"]) != ids:
        raise ValueError("forecast does not cover declared choices")
    values = list(obj["probabilities"].values())
    if any(type(value) not in {int, float} or not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise ValueError("invalid probability")
    if abs(sum(values) - 1) > 1e-6:
        raise ValueError("probability vector must sum to one; no silent normalization")
    if not isinstance(obj["explanation"], str) or type(obj["insufficient_evidence"]) is not bool:
        raise ValueError("invalid explanation or uncertainty flag")
    return obj
