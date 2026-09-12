"""Direct and fixed episodic readers, with explicit retrieval and token accounting.

DESIGN CHECK: LESSONS 2-5. Retrieval uses training evidence only; a changed or
hidden target answer cannot affect selected examples. All arms retain identical
target evidence and option order. Under either hypothesis, oversized evidence
is refused rather than silently truncated. Retrieval is a baseline, not a
procedure model or a claim of semantic-memory reproduction.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .contracts import PublicTask, canonical, digest
from .ollama import request_for


def from_record(record: dict) -> PublicTask:
    return PublicTask(**{**record, "choices": tuple(tuple(pair) for pair in record["choices"])})


def tokens(value: dict) -> Counter:
    return Counter(re.findall(r"\w+", canonical(value).casefold()))


def examples_for(task: PublicTask, training: list[dict], answers: list[dict], *, maximum: int = 2) -> tuple[list[dict], dict]:
    target = tokens(task.evidence)
    truth = {row["task_id"]: row["correct_choice"] for row in answers}
    if len(truth) != len(answers) or set(truth) != {row["task_id"] for row in training}:
        raise ValueError("training evidence and labels do not join uniquely")
    scored = []
    target_norm = math.sqrt(sum(value * value for value in target.values()))
    for row in training:
        source = from_record(row)
        if source.evidence_view != task.evidence_view or source.family != task.family:
            continue
        if source.task_id == task.task_id:
            raise ValueError("target appeared in the retrieval pool")
        counts = tokens(source.evidence)
        norm = math.sqrt(sum(value * value for value in counts.values())) * target_norm
        similarity = sum(value * counts.get(key, 0) for key, value in target.items()) / norm if norm else 0.0
        scored.append((-similarity, source.task_id, source))
    selected, ids, skipped = [], [], []
    for _, identifier, source in sorted(scored, key=lambda item: (item[0], item[1])):
        description = next((value for key, value in source.choices if key == truth[identifier]), None)
        if description is None:
            raise ValueError("training answer not in declared source support")
        example = {"evidence_view": source.evidence_view, "evidence": source.evidence,
                   "question": source.question, "observed_outcome": description}
        proposed = [*selected, example]
        try:
            request_for(task, instruction="Use these fixed retrieved episodes as concrete examples; predict the new case directly.",
                        examples=proposed, context_tokens=16384)
        except ValueError:
            skipped.append(identifier)
            continue
        selected.append(example); ids.append(identifier)
        if len(selected) == maximum:
            break
    if not selected:
        raise ValueError("no complete training episode fits the declared context budget")
    return selected, {"method": "casefolded word-count cosine, fixed identifier tie-break",
                      "training_pool_sha256": digest(training), "training_answers_sha256": digest(answers),
                      "selected_training_ids": ids, "context_skipped_ids": skipped, "maximum_examples": maximum}


def build(task: PublicTask, arm: str, training: list[dict], answers: list[dict]) -> tuple[dict, dict]:
    if arm == "R0":
        kwargs = {"instruction": "Predict directly from the permitted evidence.", "context_tokens": 16384}
        receipt = {"arm": arm, "retrieval": None}
    elif arm == "R1":
        examples, receipt = examples_for(task, training, answers)
        kwargs = {"instruction": "Use these fixed retrieved episodes as concrete examples; predict the new case directly.",
                  "examples": examples, "context_tokens": 16384}
        receipt = {"arm": arm, "retrieval": receipt}
    else:
        raise ValueError("reader arm has not been implemented; no direct-reader substitution")
    request_for(task, **kwargs)
    return kwargs, receipt
