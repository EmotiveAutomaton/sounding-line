"""CA5.s: all fixed Unsure-coding, split and published-quality specifications.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7. Coding cannot drop unsure ratings.
Metadata alone freezes both splits and topic support. Group/item-only worlds
must stay null and planted topic patterns recur. Twelve fixed cells are all
reported; no best-cell selection. A robust pass requires every cell's positive
interval and Holm-adjusted p below .05; unsupported cells cannot pass.
"""
from pathlib import Path
import numpy as np
from . import week3_dices as base
from . import week3_dices_followup as shared
from .batch_runtime import atomic
from .menus_io import assert_equal, input_hashes, read, write


def calculate(output, inputs, config, verify_only=False):
    data, count, draws = shared.admit(inputs, config)
    cells = []
    for population, original, groups, items, topics in shared.populations(data):
        for coding in shared.UNSURE:
            values = shared.recode(original, coding)
            for split in shared.SPLITS:
                profiles, _, census = shared.features(values, groups, items, topics, split)
                cell = {"population": population, "unsure_score": coding, "split": split, **census}
                if profiles is None:
                    cell.update(state="unsupported", reason="full fixed population lacks peer or topic support")
                else:
                    real, zero = base.profile_correlations(profiles)
                    null = []
                    for j in range(count):
                        fake = base.permutation(values, groups, shared.SEED + j)
                        features, _, changed = shared.features(fake, groups, items, topics, split)
                        if changed != census or features is None:
                            raise ValueError("permutation changed frozen support")
                        null.append(base.profile_correlations(features)[0])
                    cell.update(shared.topic_report(real, np.asarray(null), draws), zero_profile_raters=int(zero.sum()))
                cells.append(cell)
                if not verify_only:
                    atomic(Path(output) / "PROGRESS.json", {"phase": "fixed_specifications", "completed": len(cells), "total": 12})
    adjusted = shared.holm([c.get("permutation_p_one_sided", 1.) for c in cells])
    for cell, p in zip(cells, adjusted):
        cell["holm_adjusted_p_12_cells"] = p
    robust = all(c["state"] == "positive" and c["holm_adjusted_p_12_cells"] < .05 for c in cells)
    return {**shared.contract("CA5.s"), "input_hashes": input_hashes(inputs), "cells": cells,
            "all_fixed_specifications_pass": robust,
            "curve_status": "all_fixed_specifications_pass" if robust else "not_all_fixed_specifications_pass",
            "interval_scope": "per-cell unadjusted 95% intervals; twelve permutation p-values additionally Holm adjusted",
            "split_definition": "odd/even numeric item IDs; first floor(n/2) versus remaining sorted numeric item IDs, not a temporal claim",
            "coding_definition": "No=0, Yes=1; every Unsure retained and coded 0, 0.5 or 1; twelve cells exhaustive"}


def execute(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    result = calculate(output, inputs, config)
    write(output / "SUMMARY.json", result)
    return result


def verify(output, inputs, config):
    assert_equal(calculate(output, inputs, config, True), read(Path(output) / "SUMMARY.json"))
    return {"verified": True, "fresh_all_12_cells_and_all_references": True}
