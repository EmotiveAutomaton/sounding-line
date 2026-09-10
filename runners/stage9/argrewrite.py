"""ArgRewrite v2: preserved v4 units and documented whole-draft successors.

DESIGN CHECK: LESSONS sections 2, 3, 4, 5; corrections L79/L81/L85/L107/L109.
NULL: malformed columns, lost compound references or a changed v4 population fail
preparation. ALTERNATIVE: full released tables reproduce the historical 3236 units
and 1627 first-cycle units, keeping every excluded group. Multi-purpose groups are
discarded by the established rule, never assigned their first purpose. The v4
first revision-index grouping is explicit, with ALL compound references preserved.
All three drafts share one essay/student group. A later target is a whole-cycle
category distribution; its location cannot select an earlier evidence window.
Bands: exact historical reproduction or FAIL; source paper's 3238 remains distinct.
"""
from collections import Counter, defaultdict
import re
import time

from runners.stage9.common import REPO, ROOT, closure, digest, freeze, read
from runners.run_arg_replication import FINE9, SURFACE9, extract_v4

CLASSES = tuple(sorted(FINE9.values()))
SOURCE = REPO/'corpora/public/argrewrite'


def indices(value):
    if value is None or str(value).strip().lower() in ('', 'none', 'nan'):
        return []
    parts = str(value).split(',')
    values = []
    for part in parts:
        number = float(part.strip())
        if not number.is_integer():
            raise ValueError('nonintegral source reference')
        values.append(int(number))
    if len(set(values)) != len(values):
        raise ValueError('duplicate source reference')
    return values


def units_from_tables(tables):
    if set(tables) != {'old', 'new'}:
        raise ValueError('both source draft tables required')
    units = {}
    row_counts = Counter()
    documents = {}
    for side, rows in tables.items():
        sentences = {}
        for row in rows:
            if not {'Sentence Index', 'Sentence Content', 'Revision Index Level 0',
                    'Revision Purpose Level 0', 'Aligned Index'} <= set(row):
                raise ValueError('missing canonical revision columns')
            sid = indices(row['Sentence Index'])
            if len(sid) != 1 or sid[0] in sentences:
                raise ValueError('ambiguous sentence identity')
            text = str(row['Sentence Content'] or '').strip()
            sentences[sid[0]] = text
            refs = indices(row['Revision Index Level 0'])
            marker = str(row['Aligned Index']).strip().upper()
            if marker in ('ADD', 'DELETE'):
                if marker != ('DELETE' if side == 'old' else 'ADD'):
                    raise ValueError('alignment operation on wrong draft side')
                aligned = []
            else:
                aligned = indices(row['Aligned Index'])
            row_counts['source_rows'] += 1
            if len(refs) > 1: row_counts['compound_revision_rows'] += 1
            if len(aligned) > 1: row_counts['compound_alignment_rows'] += 1
            if not refs:
                row_counts['rows_without_revision_unit'] += 1
                continue
            # EXACT historical v4 grouping, not a new claim that compound indices
            # mean only their first member. Preserve the entire field on each row.
            unit = units.setdefault(refs[0], {'revision_index': refs[0], 'old': [], 'new': [],
                                             'oi': [], 'ni': [], 'purposes': set(), 'source_rows': []})
            if text: unit[side].append(text)
            unit['oi' if side == 'old' else 'ni'].append(sid[0])
            purposes = [p.strip().lower() for p in str(row['Revision Purpose Level 0'] or '').split(',')
                        if p.strip().lower() not in ('', 'none', 'nan')]
            unit['purposes'].update(purposes)
            unit['source_rows'].append({'side': side, 'sentence': sid[0], 'revision_indices': refs,
                                       'aligned_indices': aligned, 'alignment_source': row['Aligned Index'],
                                       'purposes': purposes})
        documents[side] = ' '.join(sentences[k] for k in sorted(sentences))
    output = []
    for unit in units.values():
        purposes = sorted(unit['purposes'])
        reason = ('no purpose' if not purposes else 'multi-purpose unit' if len(purposes) > 1
                  else 'unknown purpose' if purposes[0] not in FINE9 else None)
        output.append(unit | {'old': ' '.join(unit['old']), 'new': ' '.join(unit['new']),
                             'purposes': purposes, 'usable': reason is None, 'exclusion': reason,
                             'fine': FINE9[purposes[0]] if reason is None else None})
    return output, documents, dict(row_counts)


def visible(unit, view):
    if not unit['usable']: raise ValueError('excluded revision')
    if view == 'artifact': return {'text': unit['new']}
    if view == 'pair': return {'before': unit['old'], 'after': unit['new']}
    raise ValueError('unknown revision view')


def future_visible(essay, view):
    # The target is ALL canonical draft2->3 purposes, not a target-selected span.
    if not essay['future_usable']: raise ValueError('unverified successive draft')
    if view == 'artifact': return {'text': essay['drafts']['2']}
    if view == 'record':
        return {'before': essay['drafts']['1'], 'after': essay['drafts']['2'],
                'earlier_labels': [r['fine'] for r in essay['units'] if r['cycle'] == '12' and r['usable']]}
    raise ValueError('unknown future view')


def normalized(text):
    return ''.join(text.split())


def padded_row(header, row):
    return {name: row[i] if i < len(row) else None for i, name in enumerate(header)}


def raw_inputs():
    """Original complete source inventory; no preparation output is written."""
    files = sorted(p for p in (SOURCE/'annotations').rglob('*.xlsx') if not p.name.startswith('~$'))
    draft_files = sorted((SOURCE/'essays').rglob('*.txt'))
    identity = {'sources': closure([REPO/'runners/stage9/argrewrite.py', REPO/'runners/stage9/common.py',
                                   REPO/'runners/run_arg_replication.py']),
                'inputs': closure(files + draft_files + [SOURCE/'readme.txt', SOURCE/'annotations/readme.txt']),
                'construction': 'historical v4 first revision-index groups; all raw compound references retained; multi-purpose groups discarded',
                'exposure': 'previously evaluated corpus; no untouched reserve',
                'rights_basis': 'in-hand curator-authorized research reuse; release readme requests Kashefi et al 2022 citation; no broad redistribution license asserted'}
    return files, draft_files, identity


def reconstruct(files, draft_files, input_closure):
    """Pure output reconstruction from the original already-exposed corpus."""
    from openpyxl import load_workbook
    essays = {}; ledger = []; totals = Counter(); historical = []
    for path in files:
        author_match = re.search(r'argrewrite_(\d+)', path.stem)
        cycles = [p for p in path.parts if p in ('12', '23')]
        if not author_match or len(cycles) != 1: raise ValueError('unknown source lineage')
        author = author_match.group(1); cycle = cycles[0]
        group = digest({'argrewrite_student_essay': author})
        essay = essays.setdefault(group, {'group': group, 'drafts': {}, 'units': [], 'tables': {}})
        if cycle in essay['tables']: raise ValueError('duplicate revision-cycle workbook')
        workbook = load_workbook(path, read_only=True, data_only=True)
        tables = {}
        for sheet in workbook:
            if sheet.title not in ('Old Draft', 'New Draft'): raise ValueError('unexpected source worksheet')
            sheet.reset_dimensions(); iterator = sheet.iter_rows(values_only=True)
            header = next(iterator)
            if len(set(header)) != len(header): raise ValueError('duplicate source header')
            tables['old' if sheet.title == 'Old Draft' else 'new'] = [padded_row(header, row) for row in iterator]
        workbook.close()
        units, documents, row_counts = units_from_tables(tables)
        totals.update(row_counts); essay['tables'][cycle] = documents
        for unit in units:
            key = digest({'group': group, 'cycle': cycle, 'revision': unit['revision_index']})
            unit.update({'key': key, 'group': group, 'cycle': cycle})
            essay['units'].append(unit)
            if unit['usable']:
                historical.append({'author': author, 'cycle': cycle, 'raw': unit['purposes'][0],
                    'fine': unit['fine'], 'binary': 'surface' if unit['fine'] in SURFACE9 else 'content',
                    'old': unit['old'], 'new': unit['new'],
                    'pos_idx': min(unit['ni']) if unit['ni'] else min(unit['oi']) if unit['oi'] else 0,
                    'pos_old': min(unit['oi']) if unit['oi'] else 0})
        ledger.append({'group': group, 'cycle': cycle, 'workbook_sha256': input_closure['files'][path.relative_to(REPO).as_posix()],
                       'attempts': len(units), 'usable': sum(u['usable'] for u in units), 'rows': row_counts})
    for path in draft_files:
        author = re.search(r'argrewrite_(\d+)', path.stem)
        draft = re.fullmatch(r'Draft([123])', path.parent.name)
        if not author or not draft: raise ValueError('unknown draft file identity')
        group = digest({'argrewrite_student_essay': author.group(1)})
        essay = essays[group]
        if draft.group(1) in essay['drafts']: raise ValueError('duplicate draft')
        essay['drafts'][draft.group(1)] = path.read_text(encoding='utf-8-sig')
    canonical = extract_v4()
    if sorted(map(digest, canonical)) != sorted(map(digest, historical)):
        raise ValueError('historical v4 construction mismatch')
    if len(historical) != 3236 or sum(r['cycle'] == '12' for r in historical) != 1627:
        raise ValueError('historical published-source count changed')
    counts = Counter(); exclusions = Counter(); agreement = Counter()
    for group, essay in essays.items():
        if set(essay['drafts']) != {'1', '2', '3'} or set(essay['tables']) != {'12', '23'}:
            raise ValueError('incomplete source draft lineage')
        checks = {cycle + ':' + side: normalized(essay['tables'][cycle][side]) == normalized(essay['drafts'][draft])
                  for cycle, side, draft in [('12', 'old', '1'), ('12', 'new', '2'), ('23', 'old', '2'), ('23', 'new', '3')]}
        checks['middle_table_continuity'] = normalized(essay['tables']['12']['new']) == normalized(essay['tables']['23']['old'])
        agreement.update({k: int(v) for k, v in checks.items()})
        essay['draft_checks'] = checks
        essay['future_usable'] = all(checks.values())
        essay['future_exclusion'] = None if essay['future_usable'] else 'raw/annotated draft correspondence mismatch'
        for unit in essay['units']:
            counts['attempted_units'] += 1
            if unit['usable']: counts['usable_units'] += 1
            else: exclusions[unit['exclusion']] += 1
    result = {'completed': True, 'workbooks': len(files), 'draft_files': len(draft_files),
              'essay_student_lineages': len(essays), 'rows': dict(totals), 'units': dict(counts), 'exclusions': dict(exclusions),
              'historical_v4_exact': True, 'paper_units': 3238, 'release_v4_units': 3236,
              'cycle_counts': dict(Counter(r['cycle'] for r in historical)),
              'class_counts': dict(Counter(r['fine'] for r in historical)), 'draft_agreement': dict(agreement),
              'genuine_future_lineages': sum(e['future_usable'] for e in essays.values()),
              'reserve_groups': 0,
              'limits': ['reader-assigned purpose agreement, not maker intention', 'previously exposed corpus',
                         'v4 compound-index grouping retained explicitly', 'paper and release unit counts differ']}
    if len(files) != 172 or len(draft_files) != 258 or len(essays) != 86: raise ValueError('released source totals fail')
    return essays, ledger, result


def prepare():
    started = time.time(); output = ROOT/'private/prepared/argrewrite-v3'
    files, draft_files, identity = raw_inputs()
    freeze(output/'IDENTITY.json', identity)
    if (output/'COMPLETE.json').exists():
        return read(output/'COMPLETE.json')
    essays, ledger, counts = reconstruct(files, draft_files, identity['inputs'])
    for group, essay in essays.items():
        freeze(output/'essays'/(group+'.json'), essay)
    freeze(output/'LEDGER.json', ledger)
    result = {'identity_sha256': digest(identity), **counts,
              'elapsed_seconds': time.time()-started, 'completed_at': time.time()}
    freeze(output/'COMPLETE.json', result)
    freeze(ROOT/'intake/ARGREWRITE_PREPARATION.json', result)
    return result


if __name__ == '__main__':
    print(prepare())
