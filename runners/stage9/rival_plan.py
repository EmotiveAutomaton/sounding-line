"""Bind a fixed rival menu or evaluation template to its actual training producer.

DESIGN CHECK: C01/C05/M01/X01/X02/X06/X12; LESSONS 3--5.
NULL: an unfinished, substituted or pilot fit cannot supply a scientific package;
changing the eligible menu or using discovery to select refuses. ALTERNATIVE:
the original declared producer commits a validated training-only package and the
unchanged complete rival menu or checksum-pinned evaluation template receives its
actual checksum. Evaluation cannot select rivals or change the declared contrasts.
Paired templates preserve both conditions' explicit model/baseline contrasts.
Bands: bound input
plan or explicit refusal. No predictions, model fitting or reserve access occurs.
"""
import argparse
from pathlib import Path
import time

from .artifact_comparisons import model_inputs
from .analysis_plan_contracts import validate as validate_consumer_template
from .common import REPO, ROOT, Units, digest, file_hash, freeze, read
from .confirmation_summary import arguments
from .live_status import read as read_status
from .queue import inside, validate_manifest, verify_committed, verify_sources, writer
from .revision_predictions import finish, reentry, sources
from .training_jobs import cell_identity

MODULE = 'runners.stage9.rival_plan'
ROUTES = ('population', 'brief', 'cheap-8.0', 'cheap-16.0', 'cheap-32.0')
# Exact existing consumer protocols. These names do not relabel transfer tasks
# as ordinary doses or introduce a candidate selected from observed performance.
QUERY_CONTRACTS = {
    'library-withdrawn-v1': (('process_record|withdrawn',), None),
    'goal-change-v1': (('process_record|goal',), 'population_changed'),
    'unchanged-goal-harder-v1': (('process_record|harder',), 'population_changed'),
    'context-report-v1': (('process_record|true', 'process_record|false', 'process_record|redundant'), 'population_cued'),
}


def evaluation_template(template, role, *, paired=False):
    """Validate a manual prospective template without reading any predictions."""
    fields = ({'role', 'contrasts', 'package_sha256'} if paired else
              {'operation', 'role', 'queries', 'contrasts', 'package_sha256'})
    if (not isinstance(template, dict)
            or set(template) != fields or template['role'] != role
            or (not paired and (template['operation'] != 'evaluate' or template['queries'] != {}))
            or template['package_sha256'] is not None
            or not isinstance(template['contrasts'], list) or not template['contrasts']):
        raise ValueError('explicit unbound evaluation-only template required')
    seen = set()
    for contrast in template['contrasts']:
        if (not isinstance(contrast, dict) or set(contrast) != {
                'id', 'card', 'left', 'right', 'threshold', 'strata', 'required_controls', 'meaning'}
                or any(not isinstance(contrast[k], str) or not contrast[k].strip()
                       for k in ('id', 'card', 'meaning'))
                or contrast['id'] in seen or contrast['threshold'] != .05):
            raise ValueError('unique explicit prospective contrast and fixed threshold required')
        seen.add(contrast['id'])
        for key in ('strata', 'required_controls'):
            values = contrast[key]
            if (not isinstance(values, list) or (paired and key == 'required_controls' and not values)
                    or any(not isinstance(v, str) or not v.strip() for v in values)
                    or len(values) != len(set(values))):
                raise ValueError('explicit unique strata and control names required')
        for side in (contrast['left'], contrast['right']):
            side_fields = ({'query', 'model', 'baseline'},) if paired else (
                {'query', 'model'}, {'query', 'selected_for'})
            if (not isinstance(side, dict) or set(side) not in side_fields
                    or any(not isinstance(v, str) or not v.strip() for v in side.values())):
                raise ValueError('explicit query and model or development selection required')
    return template


def resolve(declaration, plan, state, queue_path, own_cell, scope):
    """Validate original producer identity before reading its training package."""
    if (scope not in ('pilot', 'scientific') or plan['kind'] !=
            ('prelaunch_rehearsal' if scope == 'pilot' else 'science')
            or state['manifest_sha256'] != digest(plan)):
        raise ValueError('rival-plan queue or scope differs')
    paired = isinstance(declaration, dict) and 'paired_template' in declaration
    consumer = isinstance(declaration, dict) and 'analysis_template' in declaration
    consumer_template = declaration.get('analysis_template') if consumer else None
    if consumer and (not isinstance(consumer_template, dict) or consumer_template.get('operation') not in ('select', 'evaluate')):
        raise ValueError('explicit consumer selection or evaluation template required')
    evaluation = (consumer_template['operation'] == 'evaluate') if consumer else (
        paired or (isinstance(declaration, dict) and 'template' in declaration))
    contracted = isinstance(declaration, dict) and 'query_contract' in declaration
    role = 'pilot' if scope == 'pilot' else ('discovery' if evaluation else 'development')
    template_key = 'analysis_template' if consumer else 'paired_template' if paired else 'template'
    fields = {'model_job', 'model_path', 'role', template_key if evaluation or consumer else 'queries'}
    if consumer:
        fields.add('analysis_contract')
    if contracted:
        fields.add('query_contract')
    if (not isinstance(declaration, dict)
            or set(declaration) != fields
            or declaration['role'] != role):
        raise ValueError('fixed development-only selection or discovery-only evaluation declaration required')
    if contracted:
        contract = declaration['query_contract']
        if evaluation or consumer or not isinstance(contract, str) or contract not in QUERY_CONTRACTS:
            raise ValueError('unknown or misplaced fixed rival query contract')
    if consumer:
        validate_consumer_template(consumer_template, declaration['analysis_contract'], role)
    elif evaluation:
        evaluation_template(declaration[template_key], role, paired=paired)
    matches = [i for i, job in enumerate(plan['jobs'])
               if digest({'manifest_sha256': digest(plan), 'job': job}) == own_cell]
    if len(matches) != 1:
        raise ValueError('rival plan lacks its exact queue cell')
    index = matches[0]; own = plan['jobs'][index]
    prior = {job['id']: job for job in plan['jobs'][:index]}
    key = declaration['model_job']
    if (own['module'] != MODULE or own['resource'] != 'cpu' or own['role'] != 'work'
            or key not in prior or key not in own['after']):
        raise ValueError('rival plan requires its declared prior training dependency')
    job = prior[key]
    completion = inside(REPO / job['produces'])
    if (job['module'] != 'runners.stage9.artifact_models' or job['role'] != 'work'
            or job['resource'] != 'cpu' or state['jobs'][key]['status'] != 'COMPLETE'
            or inside(REPO / declaration['model_path']) != completion
            or inside(Path(arguments(job, '--root'))) != completion.parent
            or arguments(job, '--role') != ('pilot' if scope == 'pilot' else 'training')):
        raise ValueError('rival model producer is unfinished, substituted or wrong scope')
    verify_committed(queue_path, job, plan, digest(plan))
    done = read(completion); identity = read(completion.parent / 'IDENTITY.json')
    model_cell = digest({'manifest_sha256': digest(plan), 'job': job})
    if (identity['operation'] != 'artifact-model-training-v1'
            or identity['cell_identity'] != model_cell
            or done['cell_identity'] != model_cell
            or done['identity_sha256'] != digest(identity)
            or done['role'] != arguments(job, '--role')
            or done.get('accepted') is not True or done.get('training_only') is not True):
        raise ValueError('original completed training identity or acceptance differs')
    package = model_inputs(completion.parent, declaration['role'])
    package_sha = file_hash(completion)
    if package['completion_sha256'] != package_sha:
        raise ValueError('model completion changed while binding the rival plan')
    binding = {'model_job': key, 'model_path': declaration['model_path'],
               'model_cell_identity': model_cell, 'model_complete_sha256': package_sha}
    if consumer:
        validate_consumer_template(consumer_template, declaration['analysis_contract'], role, package=package)
        return {**consumer_template, 'package_sha256': package_sha}, binding
    if evaluation:
        return {**declaration[template_key], 'package_sha256': package_sha}, binding
    queries = declaration['queries']
    if not isinstance(queries, dict) or not queries:
        raise ValueError('explicit nonempty rival query menu required')
    if contracted and set(queries) != set(QUERY_CONTRACTS[contract][0]):
        raise ValueError('rival queries differ from the complete declared task contract')
    for query, names in queries.items():
        if not isinstance(query, str) or query.count('|') != 1:
            raise ValueError('rival query must name its exact view and dose')
        view, dose = query.split('|')
        if not contracted and (view not in ('artifact', 'process_record') or dose not in ('dose0', 'dose1', 'dose3', 'dose7', 'repeat7')):
            raise ValueError('unsupported rival evidence view or dose')
        population = QUERY_CONTRACTS[contract][1] if contracted else None
        expected = ({population, 'cheap-8.0', 'cheap-16.0', 'cheap-32.0'} if population else
                    {key + '|' + route for key in package['models'][view] for route in ROUTES})
        if (not isinstance(names, list) or any(not isinstance(n, str) for n in names)
                or len(names) != len(set(names)) or set(names) != expected):
            raise ValueError('rival menu omits, duplicates or substitutes a fitted candidate')
    return ({'operation': 'select', 'role': declaration['role'], 'queries': queries,
             'contrasts': [], 'package_sha256': package_sha},
            binding)


def run(directory, declaration_path, manifest_path, queue_path, scope, *, declaration_sha256=None):
    started, cpu = time.monotonic(), time.process_time(); cell = cell_identity()
    directory, declaration_path, manifest_path, queue_path = map(
        inside, (directory, declaration_path, manifest_path, queue_path))
    declaration = read(declaration_path)
    paired = isinstance(declaration, dict) and 'paired_template' in declaration
    consumer = isinstance(declaration, dict) and 'analysis_template' in declaration
    evaluation = (isinstance(declaration['analysis_template'], dict) and declaration['analysis_template'].get('operation') == 'evaluate') if consumer else (
        paired or (isinstance(declaration, dict) and 'template' in declaration))
    pinned = consumer or evaluation or (isinstance(declaration, dict) and 'query_contract' in declaration)
    if pinned and declaration_sha256 != file_hash(declaration_path):
        raise ValueError('evaluation or task declaration differs from its frozen checksum')
    if consumer:
        prefix = 'consumer-plan-pilots' if scope == 'pilot' else 'scientific-consumer-plans'
    elif paired:
        prefix = 'paired-plan-pilots' if scope == 'pilot' else 'scientific-paired-plans'
    elif evaluation:
        prefix = 'evaluation-plan-pilots' if scope == 'pilot' else 'scientific-evaluation-plans'
    else:
        prefix = 'rival-plan-pilots' if scope == 'pilot' else 'scientific-rival-plans'
    if scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / prefix):
        raise ValueError('rival-plan output scope differs')
    plan = read(manifest_path); validate_manifest(plan); verify_sources(plan['sources'])
    if read(queue_path / 'MANIFEST.json') != plan:
        raise ValueError('rival-plan manifest differs from the operating queue')
    matches = [job for job in plan['jobs'] if digest({'manifest_sha256': digest(plan), 'job': job}) == cell]
    if len(matches) != 1:
        raise ValueError('rival plan lacks its exact queue cell')
    own = matches[0]
    for flag, path in (('--output', directory), ('--declaration', declaration_path),
                       ('--manifest', manifest_path), ('--queue', queue_path)):
        if inside(Path(arguments(own, flag))) != path:
            raise ValueError('rival-plan invocation differs from its original queue arguments')
    if arguments(own, '--scope') != scope or inside(REPO / own['produces']) != directory / 'COMPLETE.json':
        raise ValueError('rival-plan invocation scope or produce differs')
    if pinned and arguments(own, '--declaration-sha256') != declaration_sha256:
        raise ValueError('declaration checksum differs from its original queue argument')
    selected, binding = resolve(declaration, plan, read_status(queue_path / 'STATUS.json'), queue_path, cell, scope)
    identity = {'operation': 'rival-plan-binding-v1', 'scope': scope, 'cell_identity': cell,
                'source': sources(), 'manifest_sha256': digest(plan),
                'declaration_path': str(declaration_path), 'declaration_sha256': file_hash(declaration_path),
                'declaration': declaration, 'binding': binding}
    with writer(directory):
        Units(directory, identity); prior = reentry(directory, identity)
        filename = 'PAIRED_PLAN.json' if paired else 'EVALUATION_PLAN.json' if evaluation else 'SELECTION_PLAN.json'
        if prior is not None:
            if read(directory / filename) != selected:
                raise ValueError('bound rival plan does not reconstruct')
            return prior
        freeze(directory / filename, selected)
        return finish(directory, identity, started, cpu, [filename],
                      role=declaration['role'], model_complete_sha256=binding['model_complete_sha256'],
                      queries=len(selected.get('queries', {})), predictions_or_scores_computed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'declaration', 'manifest', 'queue'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    parser.add_argument('--declaration-sha256', help='Required original-queue checksum for evaluation templates and task-specific rival contracts')
    args = parser.parse_args()
    run(args.output, args.declaration, args.manifest, args.queue, args.scope,
        declaration_sha256=args.declaration_sha256)
