"""B04 manual synthesis contract and reproducible illustration selection.

DESIGN CHECK: B04/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: omitted sections, unknown dispositions, swapped evidence, duplicate cases,
missing denominators or post-review sample choice refuse. ALTERNATIVE: the exact
reviewed narrative and candidate rosters retain evidence, denominators and one
fixed-seed example per preselected type. Constructed omission/substitution tests
must fail; reordered complete rosters must select the same cases. Bands: complete
review or refusal. Scientific interpretation and roster eligibility/completeness
are explicit operator judgments, not results inferred by this formatter.
"""
from .common import digest
from .launch import CORPORA
from .queue import DISPOSITIONS

CASE_TYPES = {
    'local_repair': 'Useful local repair',
    'generation_failure': 'First sustained-generation failure',
    'maker_signature': 'Predictable maker signature',
    'unsupported_explanation': 'Unsupported confident explanation',
    'true_context': 'Helpful true context',
    'false_context': 'Harmful false context',
    'ambiguity': 'Persistent ambiguity',
    'cheap_baseline': 'Strongest cheap-baseline victory',
}
SECTIONS = {'world_model_changes': 'What changed in the account', 'competence': 'What the readers can do',
    'maker': 'What individual evidence adds', 'substrates': 'Where the evidence stops',
    'confirmations': 'Confirmations and failures', 'limitations': 'Limits that remain',
    'pursuit': 'Why pursue these branches', 'warrant': 'What the evidence establishes',
    'strongest_rival': 'Strongest remaining rival', 'next_decision': 'Recommended next decision and its objection'}
READINESS_LEVELS = {'checkout', 'data', 'loader', 'operation', 'reproduced_anchor', 'scientific_result'}


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('packet review needs nonempty explanatory text')
    return value


def references(value, evidence):
    if (not isinstance(value, list) or not value or any(not isinstance(k, str) for k in value)
            or len(value) != len(set(value)) or not set(value) <= set(evidence)):
        raise ValueError('packet prose must cite distinct checked evidence names')
    return value


def policy(plan):
    value = plan.get('packet_policy')
    if (not isinstance(value, dict) or set(value) != {'version', 'case_seed', 'case_types', 'inherited_checkouts'}
            or type(value['version']) is not int or value['version'] != 1
            or type(value['case_seed']) is not int or not 0 <= value['case_seed'] < 2**63
            or value['case_types'] != CASE_TYPES):
        raise ValueError('original plan must preselect the exact eight case types and sampling seed')
    names = value['inherited_checkouts']
    if (not isinstance(names, list) or len(names) != 17 or any(not isinstance(v, str) or not v.strip() for v in names)
            or len(set(names)) != 17):
        raise ValueError('original plan must retain all seventeen distinct checkout names')
    return value


def validate(review, plan, evidence, audit_sha):
    fixed = policy(plan)
    fields = {'manifest_sha256', 'audit_complete_sha256', 'scope', 'sections', 'evidence',
              'cases', 'case_roster_review', 'readiness', 'claims', 'next_stage_authorized'}
    if not isinstance(review, dict) or set(review) != fields:
        raise ValueError('complete exact manual packet review required')
    scope = 'scientific' if plan['kind'] == 'science' else 'pilot'
    if (review['manifest_sha256'] != digest(plan) or review['audit_complete_sha256'] != audit_sha
            or review['scope'] != scope or review['next_stage_authorized'] is not False):
        raise ValueError('packet review differs from its original audit/scope or authorizes a next stage')
    if not isinstance(review['evidence'], dict) or review['evidence'] != evidence or not evidence:
        raise ValueError('review evidence must equal the complete independently checked evidence map')
    if not isinstance(review['sections'], dict) or set(review['sections']) != set(SECTIONS):
        raise ValueError('world-model, competence, maker, substrate, confirmation, pursuit and warrant sections required')
    for row in review['sections'].values():
        if not isinstance(row, dict) or set(row) != {'text', 'evidence'}:
            raise ValueError('packet section must distinguish prose and evidence')
        text(row['text']); references(row['evidence'], evidence)
    roster_review = review['case_roster_review']
    if (not isinstance(roster_review, dict) or set(roster_review) != {'owner', 'complete', 'basis'}
            or roster_review['owner'] != 'coding_operator' or roster_review['complete'] is not True):
        raise ValueError('candidate eligibility and completeness require an explicit operator review')
    text(roster_review['basis'])
    if not isinstance(review['cases'], dict) or set(review['cases']) != set(CASE_TYPES):
        raise ValueError('all eight case types must retain their population or explicit absence')
    chosen = {}
    for kind, row in review['cases'].items():
        if not isinstance(row, dict) or set(row) != {'population', 'absent_reason', 'evidence'} or not isinstance(row['population'], list):
            raise ValueError('case type requires its reviewed eligible population and evidence')
        references(row['evidence'], evidence); population = row['population']; ids = set(); groups = set()
        for item in population:
            if not isinstance(item, dict) or set(item) != {'id', 'group', 'description', 'evidence'}:
                raise ValueError('case needs its original identity, source group, description and evidence')
            for key in ('id', 'group', 'description'): text(item[key])
            references(item['evidence'], evidence)
            if item['id'] in ids: raise ValueError('duplicate case in the reviewed population')
            ids.add(item['id']); groups.add(item['group'])
        if population and row['absent_reason'] is not None:
            raise ValueError('present case type cannot also claim absence')
        if not population: text(row['absent_reason'])
        selected = min(population, key=lambda r: (digest({'seed': fixed['case_seed'], 'type': kind, 'case': r['id']}), r['id'])) if population else None
        chosen[kind] = {'eligible_cases': len(population), 'independent_groups': len(groups),
            'population_sha256': digest(sorted(population, key=lambda r: r['id'])),
            'selected': selected, 'absent_reason': row['absent_reason'], 'evidence': row['evidence']}
    readiness = review['readiness']
    if not isinstance(readiness, dict) or set(readiness) != {'corpora', 'inherited_checkouts'}:
        raise ValueError('readiness must separate corpora and inherited checkouts')
    if (not isinstance(readiness['corpora'], dict) or set(readiness['corpora']) != CORPORA
            or not isinstance(readiness['inherited_checkouts'], dict)
            or set(readiness['inherited_checkouts']) != set(fixed['inherited_checkouts'])):
        raise ValueError('readiness must retain all twelve corpora and seventeen inherited checkouts')
    for rows in readiness.values():
        for name, row in rows.items():
            text(name)
            if not isinstance(row, dict) or set(row) != {'levels', 'basis', 'evidence'}:
                raise ValueError('readiness needs separate supported levels and scoped evidence')
            levels = row['levels']
            if (not isinstance(levels, list) or any(not isinstance(v, str) for v in levels)
                    or len(levels) != len(set(levels)) or not set(levels) <= READINESS_LEVELS):
                raise ValueError('unknown or repeated readiness level')
            text(row['basis']); references(row['evidence'], evidence)
    if not isinstance(review['claims'], list): raise ValueError('explicit reviewed claim roster required')
    claim_ids = set()
    for claim in review['claims']:
        if not isinstance(claim, dict) or set(claim) != {'id', 'statement', 'scope', 'disposition', 'evidence'}:
            raise ValueError('claim needs its scope, disposition and checked evidence')
        for key in ('id', 'statement', 'scope'): text(claim[key])
        if claim['id'] in claim_ids or claim['disposition'] not in DISPOSITIONS:
            raise ValueError('duplicate claim or incompatible disposition enum')
        claim_ids.add(claim['id']); references(claim['evidence'], evidence)
    if scope == 'pilot' and review['claims']:
        raise ValueError('discarded packet rehearsal cannot contain scientific claims')
    return {'review': review, 'case_selection': chosen, 'policy': fixed,
            'review_sha256': digest(review), 'scientific_interpretation_automated': False}


def render(packet):
    """Render the reviewed account once; identifiers and queue detail follow the prose."""
    review = packet['review']; lines = ['# Sounding Line Stage 9', '']
    if review['scope'] == 'pilot': lines += ['**Discarded infrastructure rehearsal. No scientific result or stage closure.**', '']
    def refs(keys): return 'Evidence: ' + ', '.join('[' + k + '](#evidence-' + str(list(review['evidence']).index(k)) + ')' for k in keys) + '.'
    for key in ('world_model_changes', 'competence', 'maker', 'substrates', 'confirmations'):
        row = review['sections'][key]; lines += ['## ' + SECTIONS[key], '', row['text'], '', refs(row['evidence']), '']
    lines += ['## External readiness', '', 'Supported levels are listed separately: a checkout is not a reproduced anchor or a scientific result.', '']
    for label, rows in review['readiness'].items():
        lines += ['### ' + ('Corpora' if label == 'corpora' else 'Inherited checkouts'), '']
        for name, row in rows.items():
            lines += ['- **' + name + '**: ' + (', '.join(row['levels']) or 'No executable level established') + '. ' + row['basis'] + ' ' + refs(row['evidence'])]
        lines.append('')
    lines += ['## Preselected case types', '', 'Counts below describe the operator-reviewed eligible case roster and its independent groups; examples do not replace full study denominators. Eligibility and roster completeness remain explicit review judgments.', '']
    for kind, label in CASE_TYPES.items():
        row = packet['case_selection'][kind]
        lines += ['### ' + label, '', str(row['eligible_cases']) + ' eligible cases from ' + str(row['independent_groups']) + ' independent groups.', '']
        item = row['selected']
        lines += [(item['description'] if item else 'Absent: ' + row['absent_reason']), '', refs(item['evidence'] if item else row['evidence']), '']
    for key in ('pursuit', 'warrant', 'strongest_rival', 'next_decision', 'limitations'):
        row = review['sections'][key]; lines += ['## ' + SECTIONS[key], '', row['text'], '', refs(row['evidence']), '']
    lines += ['## Scoped claim ledger', '']
    for claim in review['claims']:
        lines += ['- **' + claim['disposition'] + '**: ' + claim['statement'] + ' Scope: ' + claim['scope'] + ' ' + refs(claim['evidence'])]
    if not review['claims']: lines += ['No scientific claims in this packet.']
    lines += ['', '## Execution coverage', '', 'Original scheduled-cell counts and failure dispositions are retained in PACKET.json. The final packet and its delivery are separate from the completed audit.', '', '## Evidence', '']
    for number, (key, pointer) in enumerate(review['evidence'].items()):
        lines += ['<a id="evidence-' + str(number) + '"></a>', '', '**' + key + '**: `' + pointer['path'] + '` (SHA-256 `' + pointer['sha256'] + '`).', '']
    return '\n'.join(lines) + '\n'
