"""RF1 exact-source and explicit-election mapping gate. No boundary inference.

DESIGN CHECK: the current SNAP source supplies no election identifier and cannot
pass this gate alone. A separately reviewed native mapping must cover every
usable original comment, bind its original archive and qualify its provenance.
Constructed envelopes are accepted only in explicitly constructed fixtures.
"""
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import json
import re
from . import week5_rf_cp_source_v1 as source
from . import week5_rf_cp_markers_v1 as markers
from . import week5_rf_cp_instrument_v1 as instrument
from . import week5_rf_statistics_v2 as stats

IDENTITY_SCHEMA = 'RF1-EXPLICIT-ELECTION-IDENTITIES-1'
IDENTITY_METHOD = 'explicit_original_election_identifiers'


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def native(root, module, complete_pin, names, constructed):
    root = Path(root)
    complete, verified, plan = (read(root/name) for name in ('COMPLETE.json', 'VERIFIED.json', 'PLAN.json'))
    if source.sha(root/'COMPLETE.json') != complete_pin:
        raise ValueError('Native completion identity changed')
    if complete.get('status') != 'COMPLETE' or complete.get('fresh_process_verified') is not True or verified.get('verified') is not True:
        raise ValueError('A template or unfinished native receipt cannot qualify RF1')
    if plan.get('module') != module:
        raise ValueError('Wrong native producer')
    if not constructed and any(x.get('constructed_fixture') is True for x in (complete, verified, plan)):
        raise ValueError('Constructed receipt cannot qualify a human source')
    for name in ('PLAN.json', 'VERIFIED.json', *names):
        if complete.get('outputs', {}).get(name) != source.sha(root/name):
            raise ValueError('Native qualified output changed')
    return root/'output'


def load(inputs, config):
    if config.get('family') != 'RF1':
        raise ValueError('Wrong RF1 family')
    needed = {'identity_producer_module', 'identity_producer_sha256', 'identity_native_complete_sha256', 'identity_review_sha256'}
    if not needed <= set(config) or not {'identity_native_root', 'identity_review'} <= set(inputs):
        raise ValueError('Explicit qualified election_id table and native review are required')
    if type(config.get('constructed_fixture', False)) is not bool:
        raise ValueError('Constructed provenance must be a boolean')
    constructed = bool(config.get('constructed_fixture'))
    summary, sample, labels = instrument.load(inputs, config)
    gate_out = native(inputs['instrument_native_root'],
        'runners.drive.cards.week5_rf_cp_instrument_v1', config['instrument_native_complete_sha256'],
        ('output/INSTRUMENT.json',), constructed)
    gate = read(gate_out/'INSTRUMENT.json')
    expected = markers.instrument_gate(summary, sample, labels)
    if gate.get('admitted') is not True or expected.get('admitted') is not True or gate['details'] != expected['details']:
        raise ValueError('RF1 lexical instrument lacks complete qualified manual review')
    if gate.get('scientific_admission') is not False or gate['source_native_complete_sha256'] != config['source_native_complete_sha256'] or gate['annotations_sha256'] != config['annotations_sha256']:
        raise ValueError('Instrument/source/manual review identity mismatch')
    src = Path(inputs['source_native_root'])/'output'
    bind = read(src/'BINDING.json')
    complete = read(src/'SOURCE_COMPLETE.json')
    rows = {}
    refused = 0
    for name, pin in sorted(complete['blocks'].items()):
        if source.sha(src/name) != pin:
            raise ValueError('Qualified source block changed')
        for row in source.read_chunk(src/name)['rows']:
            if row.get('refused'):
                refused += 1
                continue
            if row['id'] in rows:
                raise ValueError('Duplicate original comment')
            rows[row['id']] = row
    module = config['identity_producer_module']
    module_path = Path(*module.split('.')).with_suffix('.py')
    module_pin = config['identity_producer_sha256']
    if not module.startswith('runners.drive.cards.') or source.sha(module_path) != module_pin:
        raise ValueError('Reviewed identity producer code changed')
    id_out = native(inputs['identity_native_root'], module, config['identity_native_complete_sha256'],
        ('output/ELECTION_IDENTITIES.json', 'output/IDENTITY_EVIDENCE.json', 'output/IDENTITY_VERIFIED.json'), constructed)
    table = read(id_out/'ELECTION_IDENTITIES.json')
    evidence = read(id_out/'IDENTITY_EVIDENCE.json')
    proof = read(id_out/'IDENTITY_VERIFIED.json')
    review_path = Path(inputs['identity_review'])
    if source.sha(review_path) != config['identity_review_sha256']:
        raise ValueError('Owner identity qualification review changed')
    review = read(review_path)
    expected_bind = {
        'constructed_fixture': constructed,
        'source_native_complete_sha256': config['source_native_complete_sha256'],
        'source_binding_sha256': source.sha(src/'BINDING.json'),
        'source_archive_sha256': bind['archive_sha256'],
        'producer_module_sha256': module_pin,
        'identity_method': IDENTITY_METHOD,
    }
    for key, value in expected_bind.items():
        if table.get(key) != value or evidence.get(key) != value:
            raise ValueError('Election mapping is not bound to the exact original source and producer')
    if table.get('schema') != IDENTITY_SCHEMA or table.get('election_identity_qualified') is not True:
        raise ValueError('Explicit qualified election_id table is absent')
    if evidence.get('heuristic_grouping') is not False or not evidence.get('original_identifier_evidence_sha256'):
        raise ValueError('Candidate/year/result/date-gap heuristics cannot create elections')
    if proof.get('verified') is not True or proof.get('table_sha256') != source.sha(id_out/'ELECTION_IDENTITIES.json') or proof.get('evidence_sha256') != source.sha(id_out/'IDENTITY_EVIDENCE.json'):
        raise ValueError('Complete election identity replay proof is missing')
    if review.get('decision') != 'qualified_explicit_original_identifiers' or not review.get('reviewer') or review.get('constructed_fixture') is not constructed:
        raise ValueError('Explicit owner source-identity qualification is missing')
    for key, value in {
        'identity_native_complete_sha256': config['identity_native_complete_sha256'],
        'table_sha256': source.sha(id_out/'ELECTION_IDENTITIES.json'),
        'evidence_sha256': source.sha(id_out/'IDENTITY_EVIDENCE.json'),
    }.items():
        if review.get(key) != value:
            raise ValueError('Owner identity review does not cover these exact native outputs')
    mapping = validate_assignments(rows, table['assignments'], constructed)
    return rows, mapping, {'source_refusals': refused, 'source_records': summary['records'],
        'identity_table_sha256': source.sha(id_out/'ELECTION_IDENTITIES.json')}


def validate_assignments(rows, assignments, constructed=False):
    mapping = {}
    for row in assignments:
        comment, election = row.get('comment_id'), row.get('election_id')
        if comment in mapping or comment not in rows or not isinstance(election, str) or not election:
            raise ValueError('Duplicate, missing or unknown explicit election assignment')
        if not constructed and not re.fullmatch('[0-9a-f]{64}', election):
            raise ValueError('Human election identifiers must be salted before consumption')
        mapping[comment] = election
    if set(mapping) != set(rows):
        raise ValueError('Explicit identities must cover every usable original comment')
    return mapping


def ordered_elections(rows, mapping):
    """Time orders already identified elections; it never establishes membership."""
    if set(mapping) != set(rows):
        raise ValueError('Unqualified election membership')
    groups = defaultdict(list)
    for key, row in rows.items():
        if not mapping[key]:
            raise ValueError('Missing explicit election identity')
        groups[mapping[key]].append(row)
    result, dispositions = [], []
    counts = Counter(original_comments=len(rows), original_elections=len(groups))
    for election in sorted(groups):
        comments = groups[election]
        candidates = {r['candidate'] for r in comments}
        years = {r['year'] for r in comments}
        if len(candidates) != 1 or len(years) != 1:
            raise ValueError('Explicit election has inconsistent candidate/year metadata')
        if len(comments) < 20:
            counts['below_20_comments'] += 1
            dispositions.append({'election': election, 'reason': 'below_20_comments', 'comments': len(comments)})
            continue
        ordered = sorted(comments, key=lambda r: (datetime.strptime(' '.join(r['source_timestamp'].split()), '%H:%M, %d %B %Y'), r['ordinal']))
        first = len(ordered)//3
        early, later = ordered[:first], ordered[first:]
        early_votes, late_votes = Counter(r['vote'] for r in early), Counter(r['vote'] for r in later)
        if any(v not in (-1, 0, 1) for v in (*early_votes, *late_votes)):
            raise ValueError('Unexpected vote domain')
        if early_votes[1]+early_votes[-1] == 0 or late_votes[1]+late_votes[-1] == 0:
            counts['no_nonneutral_early_or_later_votes'] += 1
            dispositions.append({'election': election, 'reason': 'no_nonneutral_early_or_later_votes', 'comments': len(comments)})
            continue
        cutoff_tie = datetime.strptime(' '.join(ordered[first-1]['source_timestamp'].split()), '%H:%M, %d %B %Y') == datetime.strptime(' '.join(ordered[first]['source_timestamp'].split()), '%H:%M, %d %B %Y')
        counts['cutoff_time_ties_source_ordinal_order'] += int(cutoff_tie)
        result.append({'election': election, 'candidate': next(iter(candidates)), 'year': next(iter(years)),
            'early_support': early_votes[1]/(early_votes[1]+early_votes[-1]),
            'later_support': late_votes[1], 'later_oppose': late_votes[-1],
            'early': stats.early_counts(early), 'total_comments': len(comments),
            'early_votes': {str(k): early_votes[k] for k in (-1, 0, 1)},
            'later_neutral': late_votes[0], 'cutoff_time_tie': cutoff_tie})
    counts['eligible_elections'] = len(result)
    counts['candidate_clusters'] = len({r['candidate'] for r in result})
    return result, {'counts': dict(sorted(counts.items())), 'dispositions': dispositions,
        'identity_inferred': False, 'early_rule': 'floor(total_comments/3), time then original ordinal',
        'neutral_rule': 'included in time split and lexical denominator; omitted from binomial votes'}
