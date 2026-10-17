"""V4 full grid with verified pilot reuse and immutable per-world checkpoints.

The scientific design and instrument bands are unchanged in menus_v4. This
route never rewrites a retained unit, retries a failed fit, or changes a seed.
At a requested yield it returns before any aggregate scientific summary exists.
"""
from __future__ import annotations

import time
from pathlib import Path
import numpy as np

from . import menus_v4 as pilot
from . import menus_v4_stats
from . import states
from .menus_io import assert_equal, input_hashes, read, sha256, write

SOURCES = ("sessions", "records", "vectors", "predictions")
WORLD_FILES = ("CONSTRUCTION.json", "READERS.json", "RESULT.json")
GEOMETRY_FILES = ("GEOMETRY.json", "GEOMETRY.npz")


def world_name(cell):
    return ("null-" if cell["permuted"] else "") + cell["plant"] + "-" + str(cell["delta"]) + "-" + str(cell["replicate"])


def copy_exclusive(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with Path(source).open("rb") as src, target.open("xb") as dest:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            dest.write(block)


def completed_world(folder, binding):
    checkpoint = read(folder / "CHECKPOINT.json")
    assert_equal(checkpoint["binding"], binding)
    for name in WORLD_FILES:
        if sha256(folder / name) != checkpoint["hashes"][name]:
            raise ValueError("V4 saved world checkpoint changed")
    return read(folder / "RESULT.json")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if not {"pilot_summary", "pilot_plan"} <= inputs.keys():
        raise ValueError("V4 full requires the measured pilot and its frozen plan")
    seed = int(config.get("seed", 20261017)); identity = input_hashes(inputs)
    pilot_root = Path(inputs["pilot_summary"]).parent; report = read(inputs["pilot_summary"]); plan = read(inputs["pilot_plan"])
    if not report.get("execution_only") or report.get("mode") != "pilot" or plan["module"] != "runners.drive.cards.menus_v4":
        raise ValueError("V4 full requires its three fixed pilot worlds")
    for key in SOURCES:
        if identity[key] != report["input_hashes"][key]:
            raise ValueError("V4 pilot/full sources differ")
    for key, default in (("seed", 20261017), ("optimizer_maxiter", 100)):
        if config.get(key, default) != plan["config"].get(key, default):
            raise ValueError("V4 pilot/full model configuration differs")
    code = {str(Path(module.__file__).resolve()): sha256(module.__file__) for module in (pilot, menus_v4_stats)}
    for path, digest in code.items():
        if plan["pins"].get(path) != digest:
            raise ValueError("V4 pilot implementation differs from full imported implementation")
    pilot.verify(pilot_root, plan["inputs"], plan["config"])
    binding = dict(inputs=identity, config=config, code_sha256=sha256(__file__), pilot_code=code)
    if (output / "BINDING.json").exists():
        assert_equal(read(output / "BINDING.json"), binding)
    else:
        write(output / "BINDING.json", binding)
    if (output / "GEOMETRY_MANIFEST.json").exists():
        for name, digest in read(output / "GEOMETRY_MANIFEST.json").items():
            if sha256(output / name) != digest:
                raise ValueError("V4 saved geometry changed")
    else:
        if any((output / name).exists() for name in GEOMETRY_FILES):
            raise ValueError("incomplete V4 geometry retained; owner review required")
        for name in GEOMETRY_FILES:
            copy_exclusive(pilot_root / name, output / name)
        write(output / "GEOMETRY_MANIFEST.json", {name: sha256(output / name) for name in GEOMETRY_FILES})
    geometry = read(output / "GEOMETRY.json")
    with np.load(output / "GEOMETRY.npz", allow_pickle=False) as arrays:
        geometry.update({key: arrays[key] for key in arrays.files})
    sessions = read(inputs["sessions"])
    base = {row["key"]: row["probabilities"]["B-pop"] for row in read(inputs["predictions"])}
    reusable = {world_name(world["cell"]): world for world in read(pilot_root / "WORLDS.json")}
    required = {world_name(dict(plant=plant, delta=.4, replicate=0, permuted=False)) for plant in pilot.PLANTS}
    if set(reusable) != required:
        raise ValueError("V4 pilot world set differs")
    timings = []; visited = 0

    def run_cell(plant, delta, replicate, permuted=False):
        nonlocal visited
        cell = dict(plant=plant, delta=delta, replicate=replicate, permuted=permuted)
        name = world_name(cell); folder = output / "worlds" / name
        unit_binding = dict(run=binding, cell=cell)
        if (folder / "CHECKPOINT.json").exists():
            result = completed_world(folder, unit_binding)
        else:
            if folder.exists() and any(folder.iterdir()):
                raise ValueError("incomplete V4 world retained; owner review required")
            if name in reusable:
                for filename in WORLD_FILES:
                    copy_exclusive(pilot_root / "worlds" / name / filename, folder / filename)
                result = read(folder / "RESULT.json")
                origin = dict(reused_pilot=True, pilot_summary_sha256=identity["pilot_summary"])
            else:
                started = time.perf_counter()
                generated, trace, oracle = pilot.construct(sessions, base, geometry, plant, delta,
                    pilot.cell_seed(plant, delta, replicate, seed) + (900000 if permuted else 0))
                if permuted:
                    names = np.random.default_rng(seed + 700000 + replicate).permutation([session["writer"] for session in generated])
                    for session, writer in zip(generated, names):
                        session["writer"] = str(writer)
                        for row in session["rows"]:
                            row["writer"] = str(writer)
                write(folder / "CONSTRUCTION.json", dict(cell=cell, rows=trace, oracle=oracle))
                saved = pilot.read_world(generated, trace, oracle, geometry, base, config)
                write(folder / "READERS.json", saved)
                result = dict(cell=cell, **pilot.score_world(saved, seed), wall_seconds=time.perf_counter() - started,
                    input_hashes=identity, construction_sha256=sha256(folder / "CONSTRUCTION.json"), readers_sha256=sha256(folder / "READERS.json"))
                write(folder / "RESULT.json", result); timings.append(result["wall_seconds"])
                origin = dict(reused_pilot=False)
            write(folder / "CHECKPOINT.json", dict(binding=unit_binding, hashes={filename: sha256(folder / filename) for filename in WORLD_FILES}, **origin))
        visited += 1
        if visited >= 14 and timings and not (output / "FIRST_TENTH.json").exists():
            write(output / "FIRST_TENTH.json", dict(completed_worlds=visited, maximum_worlds=140,
                  newly_measured_worlds=len(timings), projected_seconds=140 * float(np.mean(timings)),
                  method="mean newly computed world time times maximum fixed grid size; reused pilot worlds excluded from timing"))
        return result

    def yielding():
        return (output / "YIELD_REQUEST.json").exists()

    worlds, null_worlds = [], []
    for plant in pilot.PLANTS:
        for delta in pilot.SIZES:
            first = []
            for replicate in range(5):
                if yielding():
                    return dict(status="yielded", card="V4", completed_worlds=visited)
                first.append(run_cell(plant, delta, replicate))
            worlds.extend(first)
            detections = sum(world["readers"]["R-both"]["detected"] for world in first)
            if delta in (0., .4) or detections in (2, 3):
                for replicate in range(5, 10):
                    if yielding():
                        return dict(status="yielded", card="V4", completed_worlds=visited)
                    worlds.append(run_cell(plant, delta, replicate))
    for replicate in range(20):
        if yielding():
            return dict(status="yielded", card="V4", completed_worlds=visited)
        null_worlds.append(run_cell("taste_lexical", 0., replicate, True))
    if yielding():
        return dict(status="yielded", card="V4", completed_worlds=visited)
    write(output / "WORLDS.json", worlds); write(output / "NULL_WORLDS.json", null_worlds)
    result = pilot.summarize(worlds, null_worlds, "full")
    result.update(mode="full", input_hashes=identity, reused_pilot_worlds=3,
        checkpoint_count=visited, intermediate_hashes={name: sha256(output / name) for name in
        (*GEOMETRY_FILES, "WORLDS.json", "NULL_WORLDS.json", "BINDING.json", "GEOMETRY_MANIFEST.json")})
    write(output / "SUMMARY.json", result)
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    # Existing verifier independently recomputes every retained LR, held-out
    # writer-cluster score, recovery rate and mandatory 20-world size check.
    result = pilot.verify(output, inputs, config)
    binding = read(output / "BINDING.json")
    for world in read(output / "WORLDS.json") + read(output / "NULL_WORLDS.json"):
        folder = output / "worlds" / world_name(world["cell"])
        assert_equal(completed_world(folder, dict(run=binding, cell=world["cell"])), world)
    return result
