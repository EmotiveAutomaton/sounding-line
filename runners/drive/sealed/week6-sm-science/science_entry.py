"""Sealed MIDUS entry. The installed caller has no switches for study definitions."""
from pathlib import Path
from tempfile import TemporaryDirectory
import signal

import mi_source_contract_v1 as contract
import aggregate_register_v1 as register
from sealed_io_v1 import selected_columns

import daily_bank
import argument_bank
import argument_panel
from engine import study
from table_support import EXTRAS, required_columns, source_status, supported_columns
from family_draws import family_index
from joined_source import read_roles, resolve_wave, take_snapshot
from week6_sealed_support_v1 import SealedFailure, write_tables


MAX_PRIVATE_BYTES = 2_000_000_000
MAX_SECONDS = 6 * 60 * 60


def run_joined(roots, target, source_map, out):
    needed = {"M2"} if target == "M2" else {"M2", "M3"}
    if target not in ("M2", "M3") or set(roots) != needed:
        raise SealedFailure(11, "Required wave or source role unavailable")
    published_bytes = sum(entry["bytes"] for wave in needed for entry in source_map[wave].values())
    if published_bytes > MAX_PRIVATE_BYTES:
        raise SealedFailure(14, "Reviewed source exceeds its sealed read allowance")
    with TemporaryDirectory(prefix="sm-science-") as temporary:
        private = Path(temporary)
        snapshots, selections = {}, {}
        combined = target == "M3" and Path(roots["M2"]).resolve() == Path(roots["M3"]).resolve()
        for wave in sorted(needed):
            dest = private / wave
            dest.mkdir()
            got, snapshots[wave] = take_snapshot(Path(roots[wave]), dest, source_map,
                                                  sum(e["bytes"] for e in source_map[wave].values()),
                                                  combined_wave=wave if combined else None)
            if got != wave or set(snapshots[wave]) != {"diary", "survey"}:
                raise SealedFailure(11, "Required wave or source role unavailable")
            selections[wave] = {
                "diary": selected_columns(wave + "_P2", contract.fields),
                "survey": selected_columns(wave + "_P1", contract.fields),
            }
            if wave == "M2":
                for name in EXTRAS:
                    for role, columns in required_columns(wave, name).items():
                        selections[wave][role] = sorted(set(selections[wave][role]) | columns)
        statuses, measured, source_people = inspect_tables(snapshots, selections, target)
        status_groups = [group for roles in source_people.values() for group in roles.values()]
        if not statuses or not register.exact_counts_safe(status_groups):
            raise SealedFailure(12, "No supported source status")
        extras = supported_columns({"M2": measured["M2"]}, "M2")
        # BF structural support is fixed before the first outcome projection in this job.
        arguments = argument_panel.support_plan(snapshots["M2"]) if "D5.s" in extras else None
        daily_plan = None
        if "NT1.s" in extras:
            # This opens only predictor columns until the registered support check passes.
            daily_plan = daily_bank.plan(snapshots["M2"])
            status_groups.extend(daily_bank.released_sets(daily_plan))
            if not register.exact_counts_safe(status_groups):
                raise SealedFailure(12, "Unsafe complementary daily count")
        argument_data = None
        if arguments is not None:
            argument_data = argument_panel.outcome_plan(snapshots["M2"], arguments)
            argument_groups = argument_bank.released_sets(arguments, argument_data[0])
            if target == "M3":
                # Previously eligible wave-two disclosures must be protected in the repeat return.
                status_groups.extend(argument_groups)
        available = supported_columns(measured, target)
        branches = tuple(name for name in available if name in register.BRANCHES)
        family_column = "M2FAMNUM" in measured["M2"]["survey"]
        for row in statuses:
            row["family_field_present"] = int(family_column)
        tables = {"status": statuses, "table_status": source_status(measured, source_people, target)}
        if "M2ID" in measured["M2"]["survey"]:
            families = family_index(snapshots["M2"]["survey"])
            replay_families = family_index(snapshots["M2"]["survey"])
        else:
            families = {} if family_column else None
            replay_families = {} if family_column else None
        base_disclosures = list(status_groups)
        if branches:
            original = {wave: read_available(paths, selections[wave], measured[wave])
                        for wave, paths in snapshots.items()}
            separate = {wave: read_available(paths, selections[wave], measured[wave])
                        for wave, paths in snapshots.items()}
            tables.update(study(original, separate, target, families, replay_families,
                                branches, measured, status_groups, base_disclosures))
        if daily_plan is not None and target == "M2":
            tables.update(daily_bank.run(daily_plan, families, replay_families))
        if (arguments is not None and target == "M2" and
                register.exact_counts_safe([*base_disclosures, *argument_groups])):
            tables.update(argument_bank.run(arguments, *argument_data, families, replay_families))
        tables = {name: rows for name, rows in tables.items() if rows}
        write_tables(Path(out), tables)
        return tables


def inspect_tables(snapshots, selections, target):
    """Status counts derive from the authenticated ID column, including partial supports."""
    import math
    import pyreadstat

    status, measured, groups = [], {}, {}
    for wave, paths in snapshots.items():
        measured[wave], groups[wave] = {}, {}
        for index, role in enumerate(("survey", "diary"), start=1):
            required = set(selections[wave][role])
            allowed = required | ({"M2FAMNUM"} if wave == "M2" and role == "survey" else set())
            measured[wave][role], groups[wave][role] = set(), set()
            try:
                _, metadata = pyreadstat.read_sav(str(paths[role]), metadataonly=True)
                present = allowed.intersection(metadata.column_names)
                if "M2ID" not in present:
                    measured[wave][role] = present.intersection({"M2FAMNUM"})
                    continue
                frame, _ = pyreadstat.read_sav(str(paths[role]), usecols=["M2ID"],
                                               apply_value_formats=False, user_missing=False)
            except (OSError, ValueError, RuntimeError, pyreadstat.ReadstatError):
                continue
            keys = {int(v) for v in frame["M2ID"] if isinstance(v, (int, float))
                    and math.isfinite(v) and v > 0 and v == int(v)}
            groups[wave][role] = keys
            if keys:
                measured[wave][role] = present
            if wave == target and len(keys) >= 11:
                status.append({"table_role": index, "loaded": 1, "n": len(keys),
                               "fields_required": len(required), "fields_present": len(required & present)})
    return status, measured, groups


def read_available(paths, expected, measured):
    """Keep absent columns as missing for the original fixed-shape decoders.

    A branch is selected using measured columns before decoding. A missing
    value here can never stand in for an available scientific input.
    """
    result = {}
    for role, path in paths.items():
        if "M2ID" not in measured[role]:
            result[role] = []
            continue
        include = [name for name in expected[role] if name in measured[role]]
        records = read_roles({role: path}, {role: include})[role]
        missing = dict.fromkeys(set(expected[role]) - set(include))
        result[role] = [dict(missing, **record) for record in records] if missing else records
    return result


def main(source_map, target="M2"):
    """Each immutable job uses one declared mount. SM2 contains both original waves."""
    import os
    import warnings

    if os.name == "posix":
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_SECONDS, MAX_SECONDS))
        signal.alarm(MAX_SECONDS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            root = Path("/data")
            if target == "M2":
                if resolve_wave(root, source_map) != "M2":
                    return 11
                roots = {"M2": root}
            elif target == "M3":
                roots = {"M2": root, "M3": root}
            else:
                return 11
            run_joined(roots, target, source_map, Path("/out"))
            return 0
        except SealedFailure as exc:
            return exc.code
        # Source readers may raise backend-specific exceptions containing local
        # metadata. Preserve only the fixed failure class at the sealed boundary.
        except Exception:
            return 14
