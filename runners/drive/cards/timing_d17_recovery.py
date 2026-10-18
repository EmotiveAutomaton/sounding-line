"""D17's single engineering retry: accelerate the same fixed-mixture objective.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-17. Under NULL and ALTERNATIVE,
inputs, pooled components, seed, primary and original 1e-8 EM convergence
criterion are unchanged. Previously convergent fits retain exact values.
Only an original iteration-limit failure enters constrained optimization of
the identical concave log likelihood. Certify the original EM fixed-point
residual AND a convex duality gap below 1e-8; an optimizer success flag alone
never passes. Known boundary solutions and an uncertified candidate test the
failure direction. Original failure/checkpoints remain immutable; no refit of
pooled components or redraw is permitted. A failed retry ends this card.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from . import timing_d17 as original
from .timing_census import read, write, filehash
from .timing_p6 import write_equal, progress


def density_matrix(values, means, variances):
    values, means, variances = map(lambda x: np.asarray(x, float), (values, means, variances))
    if values.ndim != 1 or not len(values) or means.ndim != 1 or not len(means) or variances.shape != means.shape:
        raise ValueError("invalid mixture dimensions")
    if not all(np.isfinite(x).all() for x in (values, means, variances)) or np.any(variances <= 0):
        raise ValueError("invalid mixture input")
    logs = -.5 * (np.log(2 * np.pi * variances)[None, :] + (values[:, None] - means[None, :]) ** 2 / variances[None, :])
    return np.exp(logs - logs.max(axis=1)[:, None])


def certificate(density, weights):
    weights = np.asarray(weights, float)
    if not np.isfinite(weights).all() or np.any(weights < 0) or abs(weights.sum() - 1) > 1e-12:
        raise ValueError("mixture weights outside simplex")
    denominator = density @ weights
    if np.any(denominator <= 0):
        raise ValueError("zero mixture density")
    score = np.mean(density / denominator[:, None], axis=0)
    # On the simplex, w.dot(score)==1. Concavity therefore bounds the
    # per-observation objective gap by max(score)-1, including zero weights.
    return dict(fixed_point_residual=float(np.max(abs(weights * score - weights))),
                convex_duality_gap=max(0., float(score.max() - 1))), weights * score


def accelerated_weights(values, means, variances, initial):
    density = density_matrix(values, means, variances)
    initial = np.asarray(initial, float)
    if initial.shape != (density.shape[1],):
        raise ValueError("invalid initial weights")
    certificate(density, initial)
    def objective(weights):
        denominator = density @ weights
        return -float(np.mean(np.log(denominator))) if np.all(denominator > 0) else np.inf
    def gradient(weights):
        return -np.mean(density / (density @ weights)[:, None], axis=0)
    fit = minimize(objective, initial, jac=gradient, method="SLSQP",
                   bounds=[(0., 1.)] * len(initial),
                   constraints=[dict(type="eq", fun=lambda w: w.sum() - 1,
                                     jac=lambda w: np.ones_like(w))],
                   options=dict(maxiter=2000, ftol=1e-14))
    if not fit.success or not np.isfinite(fit.x).all() or np.any(fit.x < 0):
        raise ValueError("constrained mixture optimizer failed")
    weights = fit.x / fit.x.sum()
    # Bounded EM polish checks the same fixed point, without accepting a
    # zero-weight stationary point that is not a likelihood maximum.
    for _ in range(2000):
        checked, updated = certificate(density, weights)
        if checked["fixed_point_residual"] < 1e-8 and checked["convex_duality_gap"] < 1e-8:
            if objective(weights) > objective(initial) + 1e-12:
                raise ValueError("mixture objective worsened")
            return weights
        weights = updated / updated.sum()
    raise ValueError("accelerated mixture candidate failed convergence certificate")


def session_weights(values, means, variances, initial):
    try:
        return original.session_weights(values, means, variances, initial)
    except ValueError as exc:
        if str(exc) != "session mixture weights failed to converge":
            raise
        return accelerated_weights(values, means, variances, initial)


def implementation():
    # Isolated module namespace: the frozen original and other workers are
    # never patched. Execute and verify use this same declared replacement.
    spec = importlib.util.spec_from_file_location("_d17_recovery_implementation", original.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.session_weights = session_weights
    return module


def source_binding(inputs, config):
    if config or set(inputs) != {"original_plan", "original_failure", "inspection", "retained"}:
        raise ValueError("D17 recovery has fixed scope")
    path = Path(inputs["original_plan"]).resolve()
    root = path.parent
    plan, failure, inspection, retained = (read(inputs[k]) for k in
                                         ("original_plan", "original_failure", "inspection", "retained"))
    if Path(inputs["original_failure"]).resolve() != root / "FAILED.json":
        raise ValueError("D17 failure belongs to another attempt")
    if plan["module"] != "runners.drive.cards.timing_d17" or failure["status"] != "FAILED" or "execute child exited 1" not in failure["error"]:
        raise ValueError("unsupported D17 original attempt")
    if not inspection["native_exit_verified"] or not inspection["slot_released"] or inspection["primary_exists"]:
        raise ValueError("D17 original did not close before recovery")
    if inspection["failure_sha256"] != filehash(inputs["original_failure"]) or inspection["plan_sha256"] != filehash(path):
        raise ValueError("D17 inspection binding changed")
    if retained["failure_sha256"] != inspection["failure_sha256"] or retained["plan_sha256"] != inspection["plan_sha256"]:
        raise ValueError("D17 retained manifest changed")
    for name, expected in plan["pins"].items():
        if filehash(name) != expected:
            raise ValueError("D17 original source changed")
    output = root / "output"
    for name, expected in retained["files"].items():
        candidate = (output / name).resolve()
        candidate.relative_to(output.resolve())
        if filehash(candidate) != expected:
            raise ValueError("D17 retained checkpoint changed")
    return plan, output, dict(inputs={k:filehash(v) for k,v in inputs.items()}, files=retained["files"],
                              prior_wall_seconds=inspection["prior_wall_seconds"])


def execute(output, inputs, config):
    output = Path(output)
    plan, source, binding = source_binding(inputs, config)
    for name, expected in binding["files"].items():
        target = (output / name).resolve()
        target.relative_to(output.resolve())
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write((source / name).read_bytes())
        if filehash(target) != expected:
            raise ValueError("D17 copied checkpoint changed")
    write_equal(output / "RECOVERY_BINDING.json", binding)
    if not (output / "D17_PROGRESS.json").exists():
        progress(output / "D17_PROGRESS.json", dict(phase="retained", active_seconds=binding["prior_wall_seconds"]))
    return implementation().execute(output, plan["inputs"], plan["config"])


def verify(output, inputs, config):
    plan, _, binding = source_binding(inputs, config)
    if read(Path(output) / "RECOVERY_BINDING.json") != binding:
        raise ValueError("D17 recovery binding changed")
    for name, expected in binding["files"].items():
        if filehash(Path(output) / name) != expected:
            raise ValueError("D17 copied checkpoint changed")
    result = implementation().verify(Path(output), plan["inputs"], plan["config"])
    return dict(result, retained_files=len(binding["files"]), original_tolerance=1e-8,
                original_failure_preserved=True, prior_wall_seconds_charged=binding["prior_wall_seconds"])
