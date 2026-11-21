"""Sparse evaluation of the original LA9 weighted, L2-penalized fit.

The fixed fold coding, category reference, standardization, initialization,
regularization and optimizer come from the original producer. Removing rows
of weight zero preserves the objective and its derivatives. A full-source
speed trial must reproduce every saved coefficient within 1e-7.
"""
from pathlib import Path
import warnings

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from . import week6_la9_pooled_fit_v1 as original


def prepare(state):
    return {key: csr_matrix(matrix) for key, (_, matrix, _) in state["arms"].items()}


def draw(state, matrices, ordinal):
    n = state["meetings"]
    rng = np.random.default_rng(np.random.SeedSequence([original.model.SEED, ordinal, 6]))
    weights = np.bincount(rng.integers(n, size=n), minlength=n)[state["group"]]
    keep = weights > 0
    present = set(np.unique(state["term"][keep]))
    reference = state["categories"][0]
    result = {}
    for arm, (base, _, offset) in state["arms"].items():
        values = dict.fromkeys(state["eligible"])
        if reference in values and 0 in present:
            with threadpool_limits(limits=2), warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                fit = clone(base).fit(matrices[arm][keep], state["y"][keep], sample_weight=weights[keep])
            for label, index in state["eligible"].items():
                if index in present:
                    values[label] = 0. if index == 0 else float(fit.coef_[0][offset+index-1])
        result[arm] = values
    return result


def execute(output, inputs, config):
    """Compare the 100 already-preserved ordinals, stopping at the first mismatch."""
    if config != {"phase":"LA9-exact-timing","draws":100}:
        raise ValueError("Only the fixed first 100 ordinals qualify this implementation")
    from .batch_runtime import read, freeze, filehash
    from .week5_resume import output_manifest

    old = Path(inputs["pilot"])
    terminal = old/"PAUSED.json"
    if filehash(terminal) != inputs["pilot_sha256"]:
        raise ValueError("Original pilot receipt changed")
    plan = read(old/"PLAN.json")
    term = read(terminal)
    if (term["checkpoint_outputs"] != output_manifest(old/"output") or plan["module"] != original.MODULE
            or plan["inputs"] != inputs["original"] or read(old/"RESULT.json").get("completed") != 100):
        raise ValueError("Original 100-draw source binding differs")
    rows, support, _, _ = original.load(inputs["original"])
    state = original.state_for_fit(rows, support)
    matrices = prepare(state)
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    for ordinal in range(100):
        if (output/"YIELD_REQUEST.json").exists() or (output.parent/"YIELD_REQUEST.json").exists():
            return dict(status="yielded",completed=ordinal,total=100)
        expected = original.stored(old/"output/draws"/f"{ordinal:04d}.json")
        if expected["index"] != ordinal:
            raise ValueError("Mismatched preserved ordinal")
        actual = draw(state, matrices, ordinal)
        try:
            original.compare.compare_record(expected["value"], actual)
        except (ValueError, AssertionError):
            result = dict(status="computed",equivalent=False,first_mismatch=ordinal,
                          contrasted=ordinal+1,absolute_tolerance=1e-7)
            break
    else:
        result = dict(status="computed", equivalent=True, contrasted=100, absolute_tolerance=1e-7)
    proof = output/"EQUIVALENCE.json"
    if proof.exists():
        if read(proof)!=result:
            raise ValueError("Equivalence audit differs")
    else:
        freeze(proof,result)
    return result


def verify(output, inputs, config):
    from .batch_runtime import read
    output = Path(output)
    replay = execute(output/"independent-replay", inputs, config)
    if replay["status"]=="yielded":
        return replay
    if replay != read(output/"EQUIVALENCE.json"):
        raise ValueError("Independent sparse audit differs")
    return dict(verified=True, equivalent=replay["equivalent"], contrasted=replay["contrasted"])
