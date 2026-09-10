"""Fixed complete plan formats for the remaining existing numerical consumers.

DESIGN CHECK: M05/M06/T02/S01--S04/X02/X06; LESSONS 3--5, CONTROLS 6.
NULL: incomplete questions/groups, changed rivals, cross-role selection or
untyped templates refuse. ALTERNATIVE: the original complete consumer protocol
receives only its actual training-package checksum. No prediction, selection,
inference or scientific claim is performed here. Bands: valid template or refusal.
"""
from .ambiguity_jobs import QUESTIONS as AMBIGUITY_QUESTIONS
from .familiarity_jobs import QUESTIONS as FAMILIARITY_QUESTIONS
from .familiarity_cases import CONDITIONS
from .familiarity_entry_analysis import QUERIES as ENTRY_QUERIES
from .selection_reader import STRATEGIES
from .selection_jobs import STOP_COSTS

CONTRACTS = ('ambiguity-v1', 'constraint-v1', 'selection-v1', 'familiarity-v1', 'familiarity-entry-v1')
VIEWS = ('artifact', 'process_record')
ROUTES = ('population', 'brief', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0')


def names(values):
    return (isinstance(values, list) and bool(values)
            and all(isinstance(v, str) and v.strip() for v in values)
            and len(set(values)) == len(values))


def ordinary(view, package):
    models = package['models'][view] if package is not None else (
        view + '-l2-0.01', view + '-l2-0.1')
    return {model + '|' + route for model in models for route in ROUTES}


def query_names(contract):
    if contract == 'ambiguity-v1':
        return set(AMBIGUITY_QUESTIONS)
    if contract == 'constraint-v1':
        return {v + '|' + freedom + '|' + deadline for v in VIEWS
                for freedom in ('expanded', 'restricted') for deadline in ('loose', 'tight')}
    if contract == 'selection-v1':
        return ({v + '|' + s + '|' + str(b) for v in VIEWS for s in STRATEGIES for b in (0, 1, 3, 7)}
                | {v + '|future-stop-' + str(c) + '|stopped' for v in VIEWS for c in STOP_COSTS})
    if contract == 'familiarity-v1':
        return set(FAMILIARITY_QUESTIONS)
    if contract == 'familiarity-entry-v1':
        return set(ENTRY_QUERIES)
    raise ValueError('unknown analysis plan contract')


def selection_menu(contract, package=None):
    queries = query_names(contract)
    if contract == 'familiarity-v1':
        return {view + '|' + kind: {
            'questions': ['q' + str(i) + '|' + kind for i in range(offset, offset + 4)],
            'eligible': ({'prior', 'surface-8.0', 'surface-16.0', 'surface-32.0'} if kind == 'recognition'
                         else ordinary(view, package) | {'program_prior', 'assume_different'})}
            for view, offset in (('artifact', 0), ('process_record', 4)) for kind in ('recognition', 'future')}
    if contract == 'familiarity-entry-v1':
        return {condition + '::' + query: {'conditions': [condition], 'query': query,
                'eligible': ordinary(query.split('|')[0], package)} for condition in CONDITIONS for query in queries}
    return {query: ({'inferred', 'committed', 'uniform' if query.startswith('history_') else 'population'} if contract == 'ambiguity-v1'
                   else ordinary(query.split('|')[0], package) | ({'program_prior'} if contract == 'constraint-v1' else set()))
            for query in queries}


def validate(template, contract, role, *, package=None):
    """Require the existing complete protocol; retain declaration order and bytes."""
    if contract not in CONTRACTS or not isinstance(template, dict):
        raise ValueError('explicit supported analysis contract and template required')
    grouped = contract in ('familiarity-v1', 'familiarity-entry-v1')
    menu_key = 'groups' if grouped else 'queries'
    if (set(template) != {'operation', 'role', menu_key, 'contrasts', 'package_sha256'}
            or template['operation'] not in ('select', 'evaluate') or template['role'] != role
            or role not in ('pilot', 'development', 'discovery') or template['package_sha256'] is not None
            or (template['operation'] == 'select' and role == 'discovery')
            or (template['operation'] == 'evaluate' and role == 'development')):
        raise ValueError('analysis template operation, role or unbound package differs')
    if template['operation'] == 'select':
        expected = selection_menu(contract, package); actual = template[menu_key]
        if template['contrasts'] != [] or not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError('complete fixed selection question/group menu required')
        for key, desired in expected.items():
            current = actual[key]
            if grouped:
                if not isinstance(current, dict) or set(current) != set(desired):
                    raise ValueError('selection group shape differs from the original consumer')
                for field in desired:
                    if field == 'eligible':
                        if not names(current[field]) or set(current[field]) != desired[field]:
                            raise ValueError('selection group omits or substitutes an eligible rival')
                    elif current[field] != desired[field]:
                        raise ValueError('selection group conditions or questions changed')
            elif not names(current) or set(current) != desired:
                raise ValueError('selection query omits or substitutes an eligible rival')
        return template
    contrasts = template['contrasts']
    if template[menu_key] != {} or not isinstance(contrasts, list) or not contrasts:
        raise ValueError('complete evaluation-only contrast grid required')
    queries = query_names(contract); seen = set(); covered = set()
    for c in contrasts:
        if (not isinstance(c, dict) or set(c) != {'id', 'card', 'left', 'right', 'threshold', 'strata', 'required_controls', 'meaning'}
                or any(not isinstance(c[k], str) or not c[k].strip() for k in ('id', 'card', 'meaning'))
                or c['id'] in seen or c['threshold'] != .05 or not names(c['required_controls'])
                or not isinstance(c['strata'], list) or (c['strata'] and not names(c['strata']))):
            raise ValueError('unique complete contrast, controls and fixed threshold required')
        seen.add(c['id'])
        if contract == 'ambiguity-v1' and c['card'] != 'M05' or contract == 'constraint-v1' and c['card'] != 'M06':
            raise ValueError('analysis contrast belongs to another card')
        if grouped and c['card'] != 'T02':
            raise ValueError('familiarity contrast belongs to another card')
        for side in (c['left'], c['right']):
            fields = ({'questions'} if contract == 'familiarity-v1' else
                      {'conditions', 'query'} if contract == 'familiarity-entry-v1' else {'query'})
            if (not isinstance(side, dict) or set(side) not in (fields | {'model'}, fields | {'selected_for'})
                    or not isinstance(side.get('model', side.get('selected_for')), str)
                    or not side.get('model', side.get('selected_for')).strip()):
                raise ValueError('explicit condition/query and model or development selection required')
            if contract == 'familiarity-v1':
                if not names(side['questions']) or not set(side['questions']) <= queries:
                    raise ValueError('unknown or repeated familiarity questions')
            else:
                if not isinstance(side['query'], str) or side['query'] not in queries:
                    raise ValueError('unknown consumer question')
                if contract == 'familiarity-entry-v1' and (not names(side['conditions']) or not set(side['conditions']) <= set(CONDITIONS)):
                    raise ValueError('unknown or repeated familiarity condition')
        left = c['left']
        if contract == 'familiarity-v1':
            covered.update(left['questions'])
        elif contract == 'familiarity-entry-v1':
            covered.update((condition, left['query']) for condition in left['conditions'])
        else:
            covered.add(left['query'])
            if contract == 'ambiguity-v1' and left['query'] != c['right']['query']:
                raise ValueError('ambiguity questions have distinct historical or future targets')
    expected = {(condition, query) for condition in CONDITIONS for query in queries} if contract == 'familiarity-entry-v1' else queries
    if covered != expected:
        raise ValueError('evaluation omits part of the complete original question/condition grid')
    return template
