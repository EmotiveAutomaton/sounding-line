"""Literal R5 readers under the frozen 256 + 512 output reservation.

DESIGN CHECK: LESSONS3-5. R0 uses256 tokens, R1 uses512, R3 two256-token
proposals. NULL/ALTERNATIVE share public evidence and support. A failed proposal
or impossible executor result stays invalid; all incurred cost remains charged.
Only opportunity is admitted to this adapter. Prior full-budget R3 is intact.
"""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path

from . import effort, effort_proposal, ollama
from .contracts import canonical, digest, parse_forecast
from .executor import execute, source_identity as executor_identity
from .ghost import task_from
from .reader import build
from .structured import identity as structured_identity


def identity(root):
    sources = structured_identity()
    for name in ("effort.py", "effort_proposal.py", "effort_readers.py"):
        sources["runners/stage10/" + name] = hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    sources["exported-executor-source-closure"] = digest(executor_identity(root))
    return sources


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def cached(output, binding, task, allowance):
    path = output / "BUDGET_ATTEMPT.json"
    if not path.exists():
        return None
    saved = read(path)
    if saved["binding"] != binding:
        raise ValueError("reserved-budget adapter input changed")
    for relative, expected in saved["files"].items():
        file = output / relative
        if not file.resolve().is_relative_to(output.resolve()) or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError("reserved-budget adapter raw evidence changed")
    effort.check_attempt(task, saved["result"], allowance)
    return saved["result"]


def finish(task, output, binding, allowance, state, forecast, calls, executions, started):
    result = {"status": state, "forecast": forecast, "evidence_sha256": digest(task.public()),
              "maximum_generated_tokens": allowance,
              "cost": {"wall_seconds": time.perf_counter() - started, "model_calls": len(calls),
                       "input_tokens": sum(c["cost"]["prompt_eval_count"] for c in calls),
                       "output_tokens": sum(c["cost"]["eval_count"] for c in calls),
                       "executor_evaluations": sum(e["response"].get("result", {}).get("executor_api_evaluations", 0) for e in executions),
                       "reasoning_tokens": None, "reasoning_tokens_status": "not separately exposed"}}
    effort.check_attempt(task, result, allowance)
    files = {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()}
    ollama.write_new(output / "BUDGET_ATTEMPT.json", {"at": ollama.now(), "binding": binding, "result": result, "files": files,
                                                   "wall_scope": "entire reader callback including model service, executor startup and local overhead"})
    return result


class Readers:
    def __init__(self, root, envelope, training, answers):
        if envelope["declared_context"]["operation"] != "opportunity":
            raise ValueError("adaptive executable adapter currently admits opportunity only")
        self.root, self.envelope, self.training, self.answers = root, envelope, training, answers
        self.sources = self.current_sources()

    def current_sources(self):
        return {**identity(self.root), "training-public": digest(self.training),
                "training-answers": digest(self.answers), "public-envelope": digest(self.envelope)}

    def binding(self, task, arm, allowance):
        if task_from(self.envelope) != task or self.current_sources() != self.sources:
            raise ValueError("adaptive public task or frozen sources changed")
        return digest({"task": task.public(), "arm": arm, "allowance": allowance, "sources": self.sources,
                       "training": self.training, "answers": self.answers, "envelope": self.envelope})

    def direct(self, task, output, allowance, arm):
        if allowance != (256 if arm == "R0" else 512) or arm not in {"R0", "R1"}:
            raise ValueError("reserved direct budget changed")
        binding = self.binding(task, arm, allowance)
        saved = cached(output, binding, task, allowance)
        if saved is not None:
            return saved
        started = time.perf_counter()
        kwargs, retrieval = build(task, arm, self.training, self.answers)
        output.mkdir(parents=True, exist_ok=False)
        ollama.write_new(output / "RETRIEVAL.json", retrieval)
        result = ollama.call(task, output / "call", generated_tokens=allowance, **kwargs)
        # Reproduce the parser and exposed cost counters from literal raw bytes.
        raw = read(output / "call/RAW.json")
        forecast, state = None, "INVALID"
        try:
            if raw.get("done") is not True or raw.get("done_reason") != "stop":
                raise ValueError("incomplete response")
            forecast = parse_forecast(raw["message"]["content"], task); state = "VALID"
        except (ValueError, KeyError, TypeError):
            pass
        if result["status"] != state or result["forecast"] != forecast or result["cost"] != {k: raw.get(k) for k in result["cost"]}:
            raise ValueError("raw direct parse or cost disagrees")
        return finish(task, output, binding, allowance, state, forecast, [result], [], started)

    def initial(self, task, output, allowance):
        return self.direct(task, output, allowance, "R0")

    def retrieval(self, task, output, allowance):
        return self.direct(task, output, allowance, "R1")

    def structured(self, task, output, allowance):
        if allowance != 512:
            raise ValueError("reserved structured budget changed")
        binding = self.binding(task, "R3", allowance)
        saved = cached(output, binding, task, allowance)
        if saved is not None:
            return saved
        output.mkdir(parents=True, exist_ok=False)
        started = time.perf_counter()
        calls, executions, feedback = [], [], None
        state, forecast = "INVALID", None
        for index in range(2):
            folder = output / ("round-" + str(index+1))
            call = effort_proposal.call(task, self.envelope, folder / "proposal", feedback, generated_tokens=256)
            calls.append(call)
            raw = read(folder / "proposal/RAW.json")
            if call["cost"] != {k: raw.get(k) for k in call["cost"]}:
                raise ValueError("proposal cost does not reproduce raw")
            state = call["status"]
            if state != "VALID":
                break
            executed = execute(self.root, self.envelope, call["proposal"]["candidates"], folder / "execution")
            executions.append(executed)
            if not executed["response"]["ok"]:
                state = "EXECUTOR_INVALID"; break
            feedback = executed["response"]["result"]
        if len(calls) == 2 and state == "VALID":
            if feedback["model_mismatch"]:
                state = "MISMATCH"
            else:
                probabilities = feedback["conditional_candidate_mixture"]
                forecast = {"choice": call["proposal"]["choice"],
                            "probabilities": {key: probabilities[int(description)] for key, description in task.choices},
                            "insufficient_evidence": call["proposal"]["insufficient_support"],
                            "explanation": "Executed likelihood-weighted mixture conditional on proposed states; generated choice retained separately."}
        return finish(task, output, binding, allowance, state, forecast, calls, executions, started)

    @property
    def additional(self):
        return {"R1": self.retrieval, "R3": self.structured}
