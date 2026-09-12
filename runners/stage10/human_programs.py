"""Executable, explicitly approximate CoAuthor handling hypotheses.

DESIGN CHECK: LESSONS sections 2-5 reread. NULL: four constant hypotheses
yield the uniform mixture and no evidence of personal inference. ALTERNATIVE:
a declared predicate changes its action on the known feature boundary. Private
fields, unknown primitives and duplicate programs refuse, never become fallback
predictions. These are proposed behavior rules, not reconstructed human goals.
"""
from __future__ import annotations
import math
import re

from runners.stage9.program_inference import noisy_action, predictive_mixture
from .coauthor import DESCRIPTIONS
from .contracts import canonical, digest

ACTIONS = tuple(DESCRIPTIONS)
FEATURES = {
    "constant": "Always zero; a threshold of one expresses a constant action.",
    "draft_words": "Number of word tokens in the current draft.",
    "shortest_suggestion_words": "Fewest word tokens among displayed suggestions.",
    "longest_suggestion_words": "Most word tokens among displayed suggestions.",
    "maximum_word_overlap": "Largest fraction of distinct suggestion words also in the draft, zero to one.",
    "history_available": "One when actual earlier handling is present, otherwise zero.",
    **{"prior_" + a + "_rate": "Fraction of permitted earlier handling events classified as " + a + "; zero when none are supplied." for a in ACTIONS},
    **{"previous_" + a: "One when the latest permitted earlier handling was " + a + ", otherwise zero." for a in ACTIONS},
}


def features(task):
    expected = {"document", "suggestions"}
    if task.evidence_view == "process-record":
        expected.add("earlier_handling")
    elif task.evidence_view != "artifact":
        raise ValueError("human program evidence view not implemented")
    evidence = task.evidence
    if task.family != "coauthor-handling" or set(evidence) != expected:
        raise ValueError("undeclared human evidence fields or task")
    if {v for _, v in task.choices} != set(DESCRIPTIONS.values()):
        raise ValueError("handling choice semantics changed")
    if not isinstance(evidence["document"], str) or not isinstance(evidence["suggestions"], list) or not evidence["suggestions"] or any(not isinstance(s, str) for s in evidence["suggestions"]):
        raise ValueError("invalid current draft or displayed menu")
    history = evidence.get("earlier_handling", [])
    if not isinstance(history, list) or any(a not in ACTIONS for a in history):
        raise ValueError("invalid predecision handling history")
    words = lambda s: re.findall(r"\w+", s.casefold())
    document = words(evidence["document"])
    suggestions = [words(s) for s in evidence["suggestions"]]
    result = {"constant": 0, "draft_words": len(document),
              "shortest_suggestion_words": min(map(len, suggestions)),
              "longest_suggestion_words": max(map(len, suggestions)),
              "maximum_word_overlap": max(len(set(s) & set(document)) / max(1, len(set(s))) for s in suggestions),
              "history_available": int(bool(history))}
    for action in ACTIONS:
        result["prior_" + action + "_rate"] = history.count(action) / len(history) if history else 0
        result["previous_" + action] = int(bool(history) and history[-1] == action)
    return result


def validate(program):
    if not isinstance(program, dict) or set(program) != {"feature", "threshold", "below", "otherwise"}:
        raise ValueError("unexpected program fields")
    if program["feature"] not in FEATURES or type(program["threshold"]) not in {int, float} or not math.isfinite(program["threshold"]) or not 0 <= program["threshold"] <= 100000:
        raise ValueError("undeclared predicate or threshold")
    if program["below"] not in ACTIONS or program["otherwise"] not in ACTIONS:
        raise ValueError("undeclared handling action")
    return program


def execute(program, observed):
    validate(program)
    if set(observed) != set(FEATURES):
        raise ValueError("incomplete public feature record")
    action = program["below"] if observed[program["feature"]] < program["threshold"] else program["otherwise"]
    # Fixed lapse is an explicit approximate behavioral model, not measured noise.
    return {"action": action, "probabilities": noisy_action(action, ACTIONS, 0.15)}


def evaluate(task, candidates):
    observed = features(task)
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 8:
        raise ValueError("one to eight proposed programs required")
    programs = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != {"goal_hypothesis", "program"} or not isinstance(candidate["goal_hypothesis"], str):
            raise ValueError("goal conjecture must be separate from executable program")
        programs.append(validate(candidate["program"]))
    if len({canonical(p) for p in programs}) != len(programs):
        raise ValueError("duplicate program would multiply its mixture weight")
    executed = {str(i): execute(p, observed) for i, p in enumerate(programs)}
    weights = {key: 1 / len(executed) for key in executed}
    mixture = predictive_mixture(weights, {key: value["probabilities"] for key, value in executed.items()})
    by_description = {value: key for key, value in task.choices}
    return {"features": observed, "executed": executed, "weights": weights,
            "probabilities": {by_description[DESCRIPTIONS[a]]: p for a, p in mixture.items()},
            "executor_evaluations": len(programs), "programs_sha256": digest(programs),
            "readout": "equal mixture of proposed rule consequences with fixed total lapse 0.15",
            "meaning": "reader-proposed approximate behavior models; no historical intent, exact posterior or goal truth"}
