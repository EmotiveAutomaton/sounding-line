"""D30.r metadata/source preflight; no fabricated section or person mappings.

DESIGN CHECK: the held release has project-scoped author IDs and no section
type. Fine labels such as Section Planning are edit-purpose labels, never paper
section types. Publisher filtering and partial editor views cannot support a
raw keypress claim. This intake reports missing dependencies as infrastructure,
not a scientific null, and never runs TC or D30 on unsupported identities.
"""
from __future__ import annotations

import time
from pathlib import Path

from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_stats import bind, check_binding
from runners.stage14.common import atomic, freeze

CONFIG = dict(card="D30.r-intake", version=1)
INPUTS = {"repo_root", "source_identity", "source_schema", "source_review", "prepared_summary"}
EXPECTED_FIELDS = {"project", "timestamp", "author", "before text", "after text", "label", "high-level"}
FORECAST_SECONDS = 60


def inspect(inputs, config, output=None, elapsed=None):
    if config != CONFIG or set(config) != set(CONFIG) or any(type(config[k]) is not type(v) for k, v in CONFIG.items()) or set(inputs) != INPUTS:
        raise ValueError("exact ScholaWrite intake configuration and inputs required")
    root = Path(inputs["repo_root"]).resolve()
    identity = read(inputs["source_identity"])
    pins = identity["source_files"]["files"]
    schema_path = Path(inputs["source_schema"]).resolve()
    relative = schema_path.relative_to(root).as_posix()
    if pins.get(relative) != filehash(schema_path):
        raise ValueError("source identity does not authenticate schema")
    for index, (name, expected) in enumerate(sorted(pins.items()), 1):
        path = (root / name).resolve()
        path.relative_to(root)
        if filehash(path) != expected:
            raise ValueError("held ScholaWrite source changed")
        if output is not None:
            atomic(output / "INTAKE_PROGRESS.json", dict(verified_source_files=index, total_source_files=len(pins), active_seconds=elapsed()))
            if index == 1 and not (output / "FIRST_TENTH.json").exists():
                projection = 2 * elapsed() * len(pins)
                freeze(output / "FIRST_TENTH.json", dict(verified_source_files=1, total_source_files=len(pins),
                       elapsed_seconds=elapsed(), projected_cpu_seconds=projection, forecast_cpu_seconds=FORECAST_SECONDS,
                       boundary="first complete source-file hash; earliest safe unit"))
                if projection > 2 * FORECAST_SECONDS:
                    atomic(output / "YIELD_REQUEST.json", dict(reason="first_tenth_projection_exceeds_twice_forecast"))
            if elapsed() > 3 * FORECAST_SECONDS:
                raise RuntimeError("ScholaWrite intake threefold time ceiling")
            if (output / "YIELD_REQUEST.json").exists():
                return dict(status="yielded", card="D30.r-intake", reason="saved source-file hash boundary; source hashes rechecked on resume")
    schema, review, prepared = read(schema_path), read(inputs["source_review"]), read(inputs["prepared_summary"])
    if set(schema["features"]) != EXPECTED_FIELDS:
        raise ValueError("held release schema changed; re-review before further intake")
    if prepared["source_rows"] != schema["splits"]["all_sorted"]["num_examples"]:
        raise ValueError("prepared/source row census differs")
    if "project scoped" not in review["author_ids"] or "not" not in review["author_ids"]:
        raise ValueError("source author-identity contract requires review")
    return dict(state="invalid", instrument_only=True, scientific_result=False, dependency_state="held",
                card="D30.r-intake", source_rows=prepared["source_rows"], projects=prepared["projects"],
                project_scoped_author_ids=prepared["project_scoped_author_ids"], fields=sorted(schema["features"]),
                source_files_authenticated=len(pins),
                missing_dependencies=["authenticated paper-section type mapping, not edit-purpose labels",
                                      "authenticated anonymous cross-project writer mapping, not reused project-local numbers",
                                      "own TC census on actual released edit timing with filtering and editor-view coverage explicit",
                                      "project-separated language-model fitting and same-section donor population"],
                unlicensed_substitutions=["Section Planning is not an introduction/methods/results label",
                                         "equal numeric author IDs across projects do not establish one person",
                                         "filtered released snapshots do not establish physical keypress timing",
                                         "partial editor windows do not establish full manuscript context"],
                next="Obtain authentic scoped metadata and review timing feasibility before scientific replication; no source contact or inference commissioned by this preflight",
                privacy="aggregate counts and source hashes only; no raw text, participant identifiers or inferred identities")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    if (output / "TIMING_BINDINGS.json").exists():
        return verify(output, inputs, config)["primary"]
    freeze(output / "INTAKE_RUN_BINDINGS.json", dict(config=config, source_sha256=filehash(__file__),
           inputs={k: str(Path(v).resolve()) if Path(v).is_dir() else filehash(v) for k, v in inputs.items()}))
    prior = read(output / "INTAKE_PROGRESS.json")["active_seconds"] if (output / "INTAKE_PROGRESS.json").exists() else 0.
    started = time.monotonic()
    result = inspect(inputs, config, output, lambda: prior + time.monotonic()-started)
    if result.get("status") == "yielded":
        return result
    freeze(output / "INTAKE_PRIMARY.json", result)
    freeze(output / "INTAKE_TIMING.json", dict(wall_seconds=prior+time.monotonic()-started, forecast_cpu_seconds=FORECAST_SECONDS))
    bind(output, inputs, config, ["INTAKE_PRIMARY.json"])
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    check_binding(output, inputs, config)
    result = inspect(inputs, config)
    if result != read(Path(output) / "INTAKE_PRIMARY.json"):
        raise ValueError("ScholaWrite intake does not reconstruct")
    return dict(verified=True, primary=result)
