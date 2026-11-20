"""Manifest-bound joined-source probe with an unconditional metadata status.

DESIGN CHECK: LESSONS 2-5. Listing and readable people are distinct units.
Every completed diagnostic writes fixed metadata even when no table loads;
only verified distinct-person rows can enter structure.csv. Empty, invalid,
partial and fully loaded mappings remain separate. The installed gate does
not yet admit metadata-only CSV: this component must not be deployed until
that output channel and the actual joined-source mapping are reviewed.
"""
import csv
import io
import os
from pathlib import Path, PurePosixPath

from runners.drive.cards.week6_sealed_support_v1 import ReadBudget, SealedFailure, write_tables
from runners.drive.cards.week6_sm0_probe_v1 import inspect_table

ALIASES = ('midus-m2-joined', 'midus-m3-joined')
SUPPORTED = {'.csv', '.tsv', '.sav', '.dta'}
ARCHIVES = {'.zip', '.gz', '.bz2', '.xz', '.tar', '.7z'}
MAX_ENTRIES = 100_000
STATUS_FIELDS = ('record_kind', 'schema_version', 'disposition', 'listing_complete',
    'listed_files', 'listed_directories', 'supported_files', 'archive_files',
    'other_files', 'linked_entries', 'listing_errors', 'scan_limited',
    'mapping_valid', 'mapped_files', 'missing_files', 'loaded_tables',
    'failed_tables', 'unclassified_load_failures', 'suppressed_tables', 'exported_tables', 'reserved_read_bytes')
DISPOSITIONS = {'mapping_invalid', 'layout_incomplete', 'none_loaded', 'partial', 'mapped_tables_loaded'}


def validate_mapping(mapping):
    if not isinstance(mapping, dict) or set(mapping) != {'schema_version', 'source_alias', 'tables'}:
        raise ValueError('Exact mapping schema required')
    if type(mapping['schema_version']) is not int or mapping['schema_version'] != 1 or mapping['source_alias'] not in ALIASES:
        raise ValueError('Only the two approved joined aliases are eligible')
    tables = mapping['tables']
    if not isinstance(tables, list) or not 1 <= len(tables) <= 64:
        raise ValueError('A bounded nonempty table roster is required')
    paths = set()
    for table in tables:
        if not isinstance(table, dict) or set(table) != {'path', 'person_column', 'role'}:
            raise ValueError('Exact table declaration required')
        name = table['path']
        if not isinstance(name, str) or '\\' in name or ':' in name:
            raise ValueError('Portable relative table path required')
        path = PurePosixPath(name)
        if not name or path.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')) or path.suffix.lower() not in SUPPORTED:
            raise ValueError('Unsupported or escaping table path')
        if name.casefold() in paths: raise ValueError('Duplicate mapped path')
        paths.add(name.casefold())
        if table['person_column'] != 'M2ID' or table['role'] not in ('daily', 'survey'):
            raise ValueError('Mapping needs the reviewed person key and role')
    return tables


def inventory(root, maximum=MAX_ENTRIES):
    if type(maximum) is not int or not 1 <= maximum <= MAX_ENTRIES:
        raise ValueError('Bounded listing required')
    root = Path(root)
    counts = dict(listing_complete=1, listed_files=0, listed_directories=0,
        supported_files=0, archive_files=0, other_files=0, linked_entries=0,
        listing_errors=0, scan_limited=0)
    files = {}; pending = [root]; seen = 0
    if root.is_symlink() or not root.is_dir():
        counts.update(listing_complete=0, listing_errors=1)
        return files, counts
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    seen += 1
                    if seen > maximum:
                        counts.update(listing_complete=0, scan_limited=1)
                        return files, counts
                    try:
                        if entry.is_symlink(): counts['linked_entries'] += 1
                        elif entry.is_dir(follow_symlinks=False):
                            counts['listed_directories'] += 1; pending.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            path = Path(entry.path)
                            files[path.relative_to(root).as_posix()] = path
                            counts['listed_files'] += 1
                            key = 'supported_files' if path.suffix.lower() in SUPPORTED else 'archive_files' if path.suffix.lower() in ARCHIVES else 'other_files'
                            counts[key] += 1
                        else: counts.update(listing_complete=0, listing_errors=counts['listing_errors']+1)
                    except OSError:
                        counts.update(listing_complete=0, listing_errors=counts['listing_errors']+1)
        except OSError:
            counts.update(listing_complete=0, listing_errors=counts['listing_errors']+1)
    return files, counts


def status_payload(status):
    if set(status) != set(STATUS_FIELDS) or status['record_kind'] != 'source_layout' or type(status['schema_version']) is not int or status['schema_version'] != 1 or status['disposition'] not in DISPOSITIONS:
        raise ValueError('Fixed metadata status schema required')
    for key in STATUS_FIELDS[3:]:
        if type(status[key]) is not int or status[key] < 0:
            raise ValueError('Metadata counters must be nonnegative integers')
    if any(status[k] not in (0,1) for k in ('listing_complete','scan_limited','mapping_valid')):
        raise ValueError('Metadata flags must be binary')
    for key in STATUS_FIELDS[3:]:
        bound=2_000_000_000 if key=='reserved_read_bytes' else 64 if key in ('mapped_files','missing_files','loaded_tables','failed_tables','unclassified_load_failures','suppressed_tables','exported_tables') else MAX_ENTRIES
        if status[key]>bound:raise ValueError('Metadata counter exceeds its operational bound')
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=STATUS_FIELDS,lineterminator='\n')
    writer.writeheader();writer.writerow(status)
    payload=stream.getvalue().encode('utf8')
    if len(payload)>2048:raise ValueError('Metadata status exceeds its byte bound')
    return payload


def run(root, out, mapping, *, max_read_bytes=2_000_000_000, max_entries=MAX_ENTRIES):
    """Write diagnostic status; never claim that completion admits a source."""
    if type(max_read_bytes) is not int or not 1 <= max_read_bytes <= 2_000_000_000:
        raise ValueError('Original read ceiling required')
    root=Path(root);out=Path(out)
    if not out.is_dir() or any(out.iterdir()):raise ValueError('Fresh output directory required')
    if out.resolve().is_relative_to(root.resolve()):raise ValueError('Output must be outside the source')
    files,counts=inventory(root,max_entries)
    status=dict(record_kind='source_layout',schema_version=1,disposition='mapping_invalid',**counts,
        mapping_valid=0,mapped_files=0,missing_files=0,loaded_tables=0,failed_tables=0,unclassified_load_failures=0,
        suppressed_tables=0,exported_tables=0,reserved_read_bytes=0)
    try: tables=validate_mapping(mapping)
    except ValueError: tables=[]
    else:status.update(mapping_valid=1,mapped_files=len(tables))
    rows=[]
    # An incomplete listing cannot support an exact manifest or safe path census.
    if tables and counts['listing_complete']:
        budget=ReadBudget(root,max_read_bytes)
        for index,table in enumerate(tables,1):
            path=files.get(table['path'])
            if path is None:
                status['missing_files']+=1;continue
            try: row=inspect_table(path,budget)
            except (SealedFailure,OSError,UnicodeError,ValueError,csv.Error):
                status['failed_tables']+=1;continue
            except Exception:
                # Reader-library errors still produce diagnostics; do not hide
                # an unclassified failure among known unsupported layouts.
                status['failed_tables']+=1;status['unclassified_load_failures']+=1;continue
            status['loaded_tables']+=1
            if row['n']<11:status['suppressed_tables']+=1
            else:rows.append(dict(table=f'table_{index:03d}',**row))
        status['reserved_read_bytes']=budget.charged
    status['exported_tables']=len(rows)
    if status['mapping_valid']:
        if not status['listing_complete']:status['disposition']='layout_incomplete'
        elif not status['loaded_tables']:status['disposition']='none_loaded'
        elif status['loaded_tables']!=status['mapped_files']:status['disposition']='partial'
        else:status['disposition']='mapped_tables_loaded'
    payload=status_payload(status)
    if rows:write_tables(out,{'structure':rows})
    # Metadata has no population n. Do not invent one to pass the current gate.
    with (out/'status.csv').open('xb') as stream:stream.write(payload)
    if sum(p.stat().st_size for p in out.iterdir())>262144:raise ValueError('Combined output cap exceeded')
    return dict(status=status,source_admitted=False,metadata_channel_required=True)
