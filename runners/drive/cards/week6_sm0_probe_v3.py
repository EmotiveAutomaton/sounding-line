"""Joined-source diagnostics through the unchanged person-counted sealed gate.

DESIGN CHECK: LESSONS 2-5. Under either scientific hypothesis, counts are exact
distinct people in each loaded table. No eligible population returns a fixed
exit code, never fabricated n or a metadata exception. Partial coverage stays
explicit. Invalid mappings and incomplete listings prevent participant reads.
This component neither admits a source nor changes the installed sealed gate.
"""
import csv
from pathlib import Path

from runners.drive.cards.week6_sealed_support_v1 import ReadBudget, SealedFailure, write_tables
from runners.drive.cards.week6_sm0_probe_v1 import inspect_table
from runners.drive.cards.week6_sm0_probe_v2 import MAX_ENTRIES, inventory, status_payload, validate_mapping


# Frozen one-to-one mapping; never include exception text or source names.
ERROR_CODES = dict(zip((
    'mapping_schema', 'joined_alias', 'table_roster', 'table_declaration',
    'nonportable_path', 'unsupported_or_escaping_path', 'duplicate_path',
    'unreviewed_key_or_role', 'source_unavailable', 'listing_error',
    'listing_limit', 'empty_source', 'archive_only', 'no_supported_table',
    'mapped_file_missing', 'read_limit', 'person_field_absent', 'empty_table',
    'ambiguous_columns', 'malformed_table', 'nonregular_source',
    'outside_source', 'source_io', 'source_encoding', 'reader_value',
    'reader_csv', 'unclassified_reader', 'other_reader_refusal',
    'all_loaded_populations_below_floor', 'output_unavailable',
    'output_not_fresh', 'output_inside_source', 'invalid_bounds',
    'internal_failure', 'output_refusal', 'status_schema',
), range(10, 46)))

MAPPING_ERRORS = dict(zip((
    'Exact mapping schema required',
    'Only the two approved joined aliases are eligible',
    'A bounded nonempty table roster is required',
    'Exact table declaration required',
    'Portable relative table path required',
    'Unsupported or escaping table path',
    'Duplicate mapped path',
    'Mapping needs the reviewed person key and role',
), tuple(ERROR_CODES)[:8]))
READER_ERRORS = {
    'Private-source read allowance exceeded': 'read_limit',
    'Declared person field absent': 'person_field_absent',
    'Empty table': 'empty_table',
    'Ambiguous case-folded source columns': 'ambiguous_columns',
    'Malformed delimited table': 'malformed_table',
    'Expected a regular source file': 'nonregular_source',
    'Source path outside the declared mount': 'outside_source',
}


def refuse(category):
    raise SealedFailure(ERROR_CODES[category], category)


def reader_category(exc):
    if isinstance(exc, SealedFailure):
        return READER_ERRORS.get(str(exc), 'other_reader_refusal')
    if isinstance(exc, OSError): return 'source_io'
    if isinstance(exc, UnicodeError): return 'source_encoding'
    if isinstance(exc, ValueError): return 'reader_value'
    if isinstance(exc, csv.Error): return 'reader_csv'
    return 'unclassified_reader'


def run(root, out, mapping, *, max_read_bytes=2_000_000_000, max_entries=MAX_ENTRIES):
    root, out = Path(root), Path(out)
    if (type(max_read_bytes) is not int or not 1 <= max_read_bytes <= 2_000_000_000
            or type(max_entries) is not int or not 1 <= max_entries <= MAX_ENTRIES):
        refuse('invalid_bounds')
    if not out.is_dir(): refuse('output_unavailable')
    if any(out.iterdir()): refuse('output_not_fresh')
    if out.resolve().is_relative_to(root.resolve()): refuse('output_inside_source')
    # Preserve the bounded listing component, including invalid-mapping cases.
    if root.is_symlink() or not root.is_dir(): refuse('source_unavailable')
    files, counts = inventory(root, max_entries)
    try: tables = validate_mapping(mapping)
    except ValueError as exc: refuse(MAPPING_ERRORS.get(str(exc), 'mapping_schema'))
    if counts['scan_limited']: refuse('listing_limit')
    if not counts['listing_complete']: refuse('listing_error')
    if not counts['listed_files']: refuse('empty_source')
    if counts['archive_files'] == counts['listed_files']: refuse('archive_only')
    if not counts['supported_files']: refuse('no_supported_table')

    status = dict(record_kind='source_layout', schema_version=1,
        disposition='none_loaded', **counts, mapping_valid=1, mapped_files=len(tables),
        missing_files=0, loaded_tables=0, failed_tables=0, unclassified_load_failures=0,
        suppressed_tables=0, exported_tables=0, reserved_read_bytes=0)
    rows, failures = [], set()
    budget = ReadBudget(root, max_read_bytes)
    for index, table in enumerate(tables, 1):
        path = files.get(table['path'])
        if path is None:
            status['missing_files'] += 1
            failures.add(ERROR_CODES['mapped_file_missing'])
            continue
        try: row = inspect_table(path, budget)
        except Exception as exc:
            category = reader_category(exc)
            failures.add(ERROR_CODES[category])
            status['failed_tables'] += 1
            status['unclassified_load_failures'] += int(category == 'unclassified_reader')
            continue
        status['loaded_tables'] += 1
        if row['n'] < 11: status['suppressed_tables'] += 1
        else: rows.append(dict(table=f'table_{index:03d}', **row))
    status['reserved_read_bytes'] = budget.charged
    status['exported_tables'] = len(rows)
    if not rows:
        if status['loaded_tables']:
            failures.add(ERROR_CODES['all_loaded_populations_below_floor'])
        if not failures: refuse('internal_failure')
        # Lowest fixed code wins when several categories occur. This reports
        # one observed category, not a claim that other failures were absent.
        code = min(failures)
        raise SealedFailure(code, next(k for k, v in ERROR_CODES.items() if v == code))
    status['disposition'] = 'partial' if failures else 'mapped_tables_loaded'
    try: status_payload(status)  # Fixed bounded schema; do not write this payload.
    except ValueError: refuse('status_schema')
    statuses = [dict(table=row['table'], n=row['n'], **status,
                     **{'error_'+name: int(code in failures) for name, code in ERROR_CODES.items()})
                for row in rows]
    try: result = write_tables(out, {'structure': rows, 'status': statuses})
    except SealedFailure: refuse('output_refusal')
    return dict(status=status, source_admitted=False, metadata_channel_required=False,
                writer=result)


def exit_code(root, out, mapping, **bounds):
    """The sealed entry point exits with this code; no failed payload is returned."""
    try: run(root, out, mapping, **bounds)
    except SealedFailure as exc: return exc.code
    except Exception: return ERROR_CODES['internal_failure']
    return 0
