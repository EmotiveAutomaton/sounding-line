"""Finite hypothesis execution through the unchanged exported Ghost APIs.

DESIGN CHECK: LESSONS sections 2-5; Stage10 sections4-6. Known laws, unknown
maker candidates. Under NULL, impossible evidence must remain a mismatch;
under ALTERNATIVE, candidate consequences must match actual public APIs.
Unknown fields and private reads fail. No inferred hypothesis is historical truth.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def evaluate(frame, consumer, opportunity, reconstruction, world):
    if set(frame) != {"envelope", "candidates"}:
        raise ValueError("unexpected executor fields")
    context = consumer.validate(frame["envelope"])
    obs = context["observation"]
    candidates = frame["candidates"]
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 8:
        raise ValueError("one to eight hypotheses required")
    if len({json.dumps(c, sort_keys=True) for c in candidates}) != len(candidates):
        raise ValueError("duplicate hypotheses")
    op = context["operation"]
    rows = []
    calls = 0
    if op == "opportunity":
        # Validate the same public schema without consulting any private state.
        allowed = {"schema_version", "task_id", "access_tier", "final_artifact", "observations",
                   "allowed_causes", "target_probe", "query_cost", "reader_search_budget"}
        if set(obs) != allowed or obs["schema_version"] != "v16.opportunity.1":
            raise ValueError("unexpected opportunity observation")
        if obs["target_probe"] not in opportunity.PROBES:
            raise ValueError("unknown probe")
        required_calls = len(candidates) * (len(obs["observations"]) + 1)
        if required_calls > obs["reader_search_budget"]:
            raise ValueError("executor exceeds public search budget")
        for c in candidates:
            if set(c) != {"cause", "cost", "lapse"} or c["cause"] not in obs["allowed_causes"] or c["cause"] not in opportunity.CAUSES:
                raise ValueError("candidate cause outside declared public support")
            if type(c["cost"]) not in (int, float) or c["cost"] not in opportunity.COSTS or type(c["lapse"]) not in (int, float) or c["lapse"] not in opportunity.LAPSES:
                raise ValueError("candidate nuisance parameters outside support")
            likelihood = 1.0
            checks = []
            for item in obs["observations"]:
                if set(item) != {"probe", "artifact"} or item["probe"] not in opportunity.PROBES or type(item["artifact"]) is not int or item["artifact"] not in (0, 1):
                    raise ValueError("invalid observed probe")
                p = opportunity.response_probability(c["cause"], c["cost"], c["lapse"], item["probe"])
                mass = p if item["artifact"] else 1-p
                likelihood *= mass
                calls += 1
                checks.append({"observation": item, "probability_of_observation": mass})
            p = opportunity.response_probability(c["cause"], c["cost"], c["lapse"], obs["target_probe"])
            calls += 1
            rows.append({"candidate": c, "evidence_likelihood": likelihood,
                         "future_probabilities": [1-p, p], "observation_checks": checks})
        full_support = len(obs["allowed_causes"]) * len(opportunity.COSTS) * len(opportunity.LAPSES)
    elif op == "reading":
        if set(obs) != reconstruction.PUBLIC_KEYS or obs["schema_version"] != "v16.public.2":
            raise ValueError("unexpected reading observation")
        evidence = [obs["declared_context"]["current_observation"], *obs["permitted_prior_artifacts"]]
        for item in evidence:
            if set(item) != {"artifact", "target", "feasible", "prefix"}:
                raise ValueError("unexpected reading evidence")
        future = obs["target_request"]
        if len({c.get("library_index") for c in candidates}) != len(candidates):
            raise ValueError("duplicate library hypotheses would multiply mixture weight")
        for c in candidates:
            if set(c) != {"library_index", "reconstruction"} or type(c["library_index"]) is not int or c["library_index"] not in range(4):
                raise ValueError("candidate library outside public support")
            program = c["reconstruction"]
            if not isinstance(program, list) or len(program) > 3 or any(type(a) is not int or a not in world.ACTIONS for a in program):
                raise ValueError("candidate program is not a legal bounded primitive sequence")
            likelihood = 1.0
            checks = []
            for item in evidence:
                mass = reconstruction.observation_mass(c["library_index"], item["target"], item["artifact"], tuple(item["prefix"]), tuple(item["feasible"]))
                likelihood *= mass
                calls += 1
                checks.append({"observation": item, "probability_of_observation": mass})
            probs = [reconstruction.observation_mass(c["library_index"], future["future_target"], a, (), tuple(future.get("feasible", range(8)))) for a in range(16)]
            calls += 16
            actual = world.execute(program, feasible=tuple(evidence[0]["feasible"]), budget=min(3, obs["reader_action_budget"]))
            calls += 1
            rows.append({"candidate": c, "evidence_likelihood": likelihood,
                         "future_probabilities": probs, "observation_checks": checks,
                         "reconstruction_execution": {"artifact": actual.artifact, "legal": actual.legal,
                             "primitive_cost": actual.primitive_cost, "matches_visible_artifact": actual.legal and actual.artifact == obs["final_artifact"],
                             "historical_trace_match": "not inspected; execution success is separate"}})
        full_support = 4
    else:
        raise ValueError("unsupported structured operation")
    total = sum(r["evidence_likelihood"] for r in rows)
    mixture = None if total == 0 else [sum(r["evidence_likelihood"] * r["future_probabilities"][i] for r in rows)/total for i in range(len(rows[0]["future_probabilities"]))]
    return {"candidates": rows, "model_mismatch": total == 0,
            "conditional_candidate_mixture": mixture,
            "mixture_rule": "uniform over distinct proposed candidates, weighted by likelihood of allowed observations; conditional on proposed support only",
            "support_warning": "unproposed hypotheses may explain the evidence; this is not a full-support posterior or historical truth",
            "public_state_support_size": full_support, "executor_api_evaluations": calls,
            "assistance": "unchanged public Ghost known-law APIs; maker state not supplied"}


def main():
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root / "public/consumer"))
    import consumer
    from v16_reference import opportunity, reconstruction, world
    directory = root / "public/consumer"
    sources = {str(p.relative_to(directory)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in [directory / "consumer.py", *sorted((directory / "v16_reference").glob("*.py"))]}
    wrapper_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if any(n == "ghostscale" or n.startswith("ghostscale.") for n in sys.modules):
        raise RuntimeError("private repository imported")
    sys.addaudithook(consumer.guard)
    print(json.dumps({"ready": True, "sources": sources, "wrapper_sha256": wrapper_sha, "pid": os.getpid()}), flush=True)
    for line in sys.stdin.buffer:
        try:
            if len(line) > 4_000_000:
                raise ValueError("frame too large")
            frame = json.loads(line)
            if frame == {"operation": "shutdown"}:
                break
            if frame.get("operation") == "probe-private":
                Path(frame["path"]).read_bytes()
                raise AssertionError("private read permitted")
            started = time.perf_counter()
            cpu = time.process_time()
            result = evaluate(frame, consumer, opportunity, reconstruction, world)
            response = {"ok": True, "result": result, "wall_seconds": time.perf_counter()-started, "cpu_seconds": time.process_time()-cpu}
        except Exception as exc:
            response = {"ok": False, "error": type(exc).__name__ + ": " + str(exc)}
        print(json.dumps(response, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
