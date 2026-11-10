"""Read-only preflight and one-plan preparation; this module never launches work.

Only small native receipts are read here. Full source/model/bank authentication
remains in the existing counted producers. Their expected bytes are carried into
the plan; no source scan or numerical module import occurs during preparation.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import math

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / 'results/phase_2_4_stage_15/raw/drive-week5-20261107'
PREFIX = 'runners.drive.cards.'
FEATURE = PREFIX + 'week5_go3_features_publication'
ANALYSIS = PREFIX + 'week5_go3_bank_publication'
COLLECTION = PREFIX + 'week5_go3_collection'
FEATURE_FIXTURE = PREFIX + 'week5_go3_features_publication_fixture'
BANK_FIXTURE = PREFIX + 'week5_go3_bank_publication_fixture'
MATH_FIXTURE = PREFIX + 'week5_go3_math_publication_fixture'
PUBLICATION_FIXTURE = PREFIX + 'week5_go3_publication_io_fixture'
SITES = ('writers', 'philosophy', 'academia', 'worldbuilding', 'english')
CELLS = ('GO3', 'GO3.self', 'GO3.no-iterater', *(f'GO3.{site}' for site in SITES))
TRAIN_SHA = '0b1d1dbe74e2a68495cd0770746899c354cf6787450fc6b14b7ee1f95914eb4c'
FEATURE_FLAGS = ('all_feature_rows_replayed', 'all_external_training_rows_and_model_replayed',
                 'all_source_rows_retained', 'no_stack_scientific_fit', 'publication_identity_replayed')
BANK_FLAGS = ('complete_replay', 'complete_models_predictions_and_reference_banks_replayed',
              'complete_feature_bank_authenticated', 'all_row_habit_scope_preserved', 'publication_identity_replayed')
REQUIRED_SCOPE = {
    'runners/drive/cards/' + name + '.py' for name in (
        'week5_go', 'week5_go_revisions', 'week5_go3_source_integrity', 'week5_go3_source_checkpointed',
        'week5_go3_collection', 'week5_go3_collection_counted_fixture_v2', 'week5_go3_analysis',
        'week5_go3_features_collected', 'week5_go3_features_collected_fixture',
        'week5_go3_bank_analysis', 'week5_go3_bank_analysis_fixture', 'week5_go3_bank_math_fixture',
        'week5_runtime_v7', 'week5_output_size', 'week5_resume_v2', 'week5_policy_v2')
} | {'docs/design/stage-15/week5/' + name for name in (
    'GO3-source.md', 'GO3-analysis.md', 'GO3_COLLECTION.md', 'GO3_COLLECTED_FEATURES.md', 'GO3_BANK_ANALYSIS.md')}


REQUIRED_SCOPE |= {'runners/drive/cards/' + name + '.py' for name in (
    'week5_qualification_io', 'week5_go3_publication', 'week5_go3_features_publication',
    'week5_go3_features_publication_fixture', 'week5_go3_bank_publication',
    'week5_go3_bank_publication_fixture', 'week5_go3_math_publication_fixture',
    'week5_go3_publication_io_fixture')}
REQUIRED_SCOPE.add('docs/design/stage-15/week5/GO3_PUBLICATION.md')


def source_closure():
    """Match the launcher's repository-import closure without importing producers."""
    pending = [FEATURE, ANALYSIS, FEATURE_FIXTURE, BANK_FIXTURE, MATH_FIXTURE, PUBLICATION_FIXTURE,
               PREFIX + 'week5_runtime_v7', PREFIX + 'week5_policy_v2', PREFIX + 'week5_child_v3',
               'runners.drive.week5_launch_v7']
    seen, sources = set(), set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        parts = module.split('.')
        path = REPO.joinpath(*parts).with_suffix('.py')
        if not path.exists():
            path = REPO.joinpath(*parts) / '__init__.py'
        if not path.exists():
            continue
        sources.add(path.relative_to(REPO).as_posix())
        package = module if path.name == '__init__.py' else module.rpartition('.')[0]
        for index in range(1, len(parts)):
            init = REPO.joinpath(*parts[:index]) / '__init__.py'
            if init.exists():
                sources.add(init.relative_to(REPO).as_posix())
        for node in ast.walk(ast.parse(path.read_text(encoding='utf8'))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                name = importlib.util.resolve_name('.' * node.level + (node.module or ''), package) if node.level else node.module
                names = [name] + [name + '.' + alias.name for alias in node.names] if name else []
            else:
                continue
            pending.extend(name for name in names if name and name.split('.')[0] in {'runners', 'soundingline', 'corpora', 'tools'})
    return sources


def read(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 4 * 1024 ** 2:
        raise ValueError('Only bounded regular metadata may be read in preflight')
    return json.loads(path.read_text(encoding='utf8'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def child(root, name):
    path = Path(root) / name
    if path.is_symlink():
        raise ValueError('Linked evidence refused')
    path.resolve().relative_to(Path(root).resolve())
    return path


def merge(pins, additions):
    for path, value in additions.items():
        key = str(Path(path).resolve())
        if key in pins and pins[key] != value:
            raise ValueError('Conflicting original source or branch pin')
        pins[key] = value


def file_proof(reference, pins):
    if not isinstance(reference, dict) or set(reference) != {'path', 'sha256'}:
        raise ValueError('Exact path/hash proof absent')
    path = Path(reference['path']).resolve()
    value = read(path)
    if sha(path) != reference['sha256']:
        raise ValueError('Proof changed')
    merge(pins, {str(path): reference['sha256']})
    return value


def completed(reference, module, flags, pins):
    if not isinstance(reference, dict) or set(reference) != {'root', 'complete_sha256'}:
        raise ValueError('Exact native completion reference absent')
    root = Path(reference['root']).resolve()
    root.relative_to(ROOT.resolve())
    done = read(root / 'COMPLETE.json')
    if sha(root / 'COMPLETE.json') != reference['complete_sha256']:
        raise ValueError('Native completion changed')
    if done.get('status') != 'COMPLETE' or done.get('fresh_process_verified') is not True:
        raise ValueError('Complete independent native replay required')
    if any((root / name).exists() for name in ('FAILED.json', 'PAUSED.json')):
        raise ValueError('Ambiguous native terminal')
    required = ('PLAN.json', 'VERIFIED.json', 'OWNER.json', 'EXECUTE_NATIVE.json', 'VERIFY_NATIVE.json')
    if any(name not in done['outputs'] for name in required):
        raise ValueError('Native execution/verification identity evidence absent')
    for name in required:
        if sha(root / name) != done['outputs'][name]:
            raise ValueError('Native metadata binding changed')
    plan, verified = read(root / 'PLAN.json'), read(root / 'VERIFIED.json')
    if plan['module'] != module or any(verified.get(flag) is not True for flag in ('verified', *flags)):
        raise ValueError('Wrong native producer or incomplete qualification')
    if module in (FEATURE, ANALYSIS, FEATURE_FIXTURE, BANK_FIXTURE, MATH_FIXTURE):
        if verified.get('publication_spec') != 'GO3-UUID-1' or verified.get('publication_identity_replayed') is not True:
            raise ValueError('Exact UUID publication identity did not independently replay')
        identities = []
        for directory in ('output', 'output/independent-replay'):
            ident = sealed_json(root, done, directory + '/PUBLICATION_IDENTITY.json')
            seal = sealed_json(root, done, directory + '/PUBLICATION_IDENTITY.seal.json')
            if seal.get('sha256') != sha(root / directory / 'PUBLICATION_IDENTITY.json'):
                raise ValueError('Publication identity seal changed')
            if ident.get('module') != module or ident.get('inputs') != plan['inputs'] or ident.get('semantic_config') != {k: v for k, v in plan['config'].items() if k != 'max_wall_seconds'}:
                raise ValueError('Publication source/branch identity differs')
            for name, value in ident['sources'].items():
                if sha(name) != value:
                    raise ValueError('Publication identity source changed')
                merge(pins, {name: value})
            identities.append(ident)
        if identities[0] != identities[1]:
            raise ValueError('Independent publication identity differs')
    merge(pins, plan['pins'])
    merge(pins, {str(root / 'COMPLETE.json'): reference['complete_sha256']})
    merge(pins, {str(child(root, name)): value for name, value in done['outputs'].items()})
    return root, done, plan


def sealed_json(root, done, name):
    path = child(root, name)
    if done['outputs'].get(name) != sha(path):
        raise ValueError('Required sealed metadata changed or absent')
    return read(path)


def collection_gate(reference, pins):
    root, done, plan = completed(reference, COLLECTION, ('complete_source_collection_replayed', 'source_only'), pins)
    data = sealed_json(root, done, 'output/COLLECTION.json')
    support = sealed_json(root, done, 'output/SUPPORT.json')
    if support.get('sites') != list(SITES) or any(support.get(k) is not True for k in ('complete_collection', 'source_only', 'no_fitting_performed')):
        raise ValueError('Exact complete source-only five-site collection required')
    if support.get('scientific_admission') is not False or [s['site'] for s in data['sources']] != list(SITES):
        raise ValueError('Collection scope differs')
    if sum(s['rows'] for s in data['sources']) != support['rows'] or len({s['salt_sha256'] for s in data['sources']}) != 1:
        raise ValueError('Complete source count or shared salt differs')
    for source in data['sources']:
        src = Path(source['root']).resolve()
        if sha(src / 'COMPLETE.json') != source['complete_sha256']:
            raise ValueError('Collected source terminal changed')
        producer = read(src / 'PLAN.json')
        terminal = read(src / 'COMPLETE.json')
        if terminal.get('fresh_process_verified') is not True or terminal['outputs'].get('output/edits.parquet') != source['projection_sha256']:
            raise ValueError('Collected source projection binding differs')
        merge(pins, producer['pins'])
        merge(pins, {str(src / 'COMPLETE.json'): source['complete_sha256'], source['projection']: source['projection_sha256']})
    return root, support, data


def feature_fixture(reference, case, pins):
    root, done, plan = completed(reference, FEATURE_FIXTURE,
        (*FEATURE_FLAGS, 'original_external_model_and_complete_feature_parity', 'constructed_only'), pins)
    source = Path(plan['inputs']['collection_run'])
    source_plan = read(source / 'PLAN.json')
    if source_plan['module'] != PREFIX + 'week5_go3_collection_counted_fixture_v2' or source_plan['config'].get('case') != case:
        raise ValueError('Wrong constructed feature source branch')
    for directory in ('output', 'output/independent-replay'):
        parity = sealed_json(root, done, directory + '/FIXTURE_PARITY.json')
        if any(parity.get(k) is not True for k in ('verified', 'constructed_only', 'all_rows_retained',
                'original_external_model_parameters_exact', 'original_feature_and_probability_rows_exact', 'fixed_literal_known_answers')):
            raise ValueError('Complete original feature parity absent')
    return root


def math_gate(reference, pins):
    root, done, _ = completed(reference, MATH_FIXTURE,
        ('complete_constructed_grid_replayed', 'every_model_prediction_and_reference_draw_replayed', 'constructed_only', 'publication_identity_replayed'), pins)
    value = sealed_json(root, done, 'output/FIXTURE.json')
    expected = dict(total_cases=16, primary_draws=2000, texture_draws=200,
                    conditional_references=1000, paired_habit_draws=2000, internal_complete_unit_pilots=18)
    if any(value.get(k) != v for k, v in expected.items()) or any(value.get(k) is not True for k in (
        'fixed_signal_and_uninformative_worlds', 'exact_context_only_habit_null', 'original_complete_estimator_and_reference_parity')):
        raise ValueError('Full original mathematical grid qualification absent')


def cost_census(root=ROOT):
    """Metadata-only conservative reservation, not a fresh-budget allocation."""
    rows = []
    for directory in sorted(Path(root).iterdir()):
        if not directory.is_dir() or not (directory / 'PLAN.json').is_file():
            continue
        plan = read(directory / 'PLAN.json')
        if plan.get('campaign') != 'S15-WEEK5' or plan.get('family') != 'GO':
            continue
        terminals = [n for n in ('COMPLETE.json', 'FAILED.json', 'PAUSED.json') if (directory / n).is_file()]
        if len(terminals) > 1:
            raise ValueError('Ambiguous cost terminal')
        claimed = (directory / 'ATTEMPT.claim').exists()
        terminal = terminals[0] if terminals else None
        amount = read(directory / terminal)['cpu_seconds'] if terminal else plan['max_cpu_seconds'] if claimed else 0
        if not math.isfinite(float(amount)) or float(amount) < 0:
            raise ValueError('Invalid measured or reserved cost')
        rows.append(dict(root=str(directory.resolve()), plan_sha256=sha(directory / 'PLAN.json'), terminal=terminal,
                         terminal_sha256=sha(directory / terminal) if terminal else None,
                         measured_cpu_seconds=float(amount) if terminal else None,
                         charged_or_reserved_cpu_seconds=float(amount) + (30 if claimed else 0),
                         go3=directory.name.startswith('GO3-')))
    return dict(attempts=rows, known_GO3_cpu_seconds=sum(r['charged_or_reserved_cpu_seconds'] for r in rows if r['go3']),
                known_GO_cpu_seconds=sum(r['charged_or_reserved_cpu_seconds'] for r in rows),
                accounting='includes failed/paused/complete attempts and 30 claimed-attempt overhead; live GO workers reserve their full cap; additional prior charges require owner reconciliation')


def check_budget(request, pins):
    value = file_proof(request['accounting'], pins)
    current = cost_census()
    if value.get('owner_reviewed') is not True or value.get('cost_census') != current:
        raise ValueError('Fresh owner-reconciled GO3/family accounting absent')
    card, family = value.get('GO3_charged_cpu_seconds'), value.get('GO_charged_cpu_seconds')
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in (card, family)):
        raise ValueError('Finite owner-reconciled charges required')
    if card < current['known_GO3_cpu_seconds'] or family < current['known_GO_cpu_seconds']:
        raise ValueError('Known upstream/failure/reservation charges omitted')
    cap = request['limits']['cpu_seconds']
    if not 0 < cap + 30 <= min(250000 - card, 600000 - family):
        raise ValueError('Attempt exceeds original remaining GO3/GO ceiling')
    return value


def resume_gate(request, module, inputs, pins):
    reference = request['resume']
    if reference is None:
        return None
    if set(reference) != {'root', 'plan_sha256', 'paused_sha256'}:
        raise ValueError('Exact immutable predecessor reference required')
    root = Path(reference['root']).resolve()
    root.relative_to(ROOT.resolve())
    if any((root / n).exists() for n in ('COMPLETE.json', 'FAILED.json')):
        raise ValueError('Only an unambiguous paused predecessor may resume')
    if sha(root / 'PLAN.json') != reference['plan_sha256'] or sha(root / 'PAUSED.json') != reference['paused_sha256']:
        raise ValueError('Paused predecessor changed')
    plan, stopped = read(root / 'PLAN.json'), read(root / 'PAUSED.json')
    semantic = lambda cfg: {k: v for k, v in cfg.items() if k != 'max_wall_seconds'}
    if plan['module'] != module or plan['inputs'] != inputs or semantic(plan['config']) != semantic(request['config']):
        raise ValueError('Resume changes source, branch, memory scope or model')
    if stopped.get('status') != 'PAUSED' or not stopped.get('checkpoint_outputs'):
        raise ValueError('Complete paused output manifest absent')
    merge(pins, plan['pins'])
    merge(pins, {str(root / 'PLAN.json'): reference['plan_sha256'], str(root / 'PAUSED.json'): reference['paused_sha256']})
    # Actual output hashing/copy and pinned-file checks remain in runtime v7.
    return root, stopped


def observed_pilot(prior, stage, cell):
    root, stopped = prior
    prefix = '' if stopped['paused_operation'] == 'execute' else 'independent-replay/'
    relative = prefix + ('STATE.json' if stage == 'features' else 'classifier/bootstrap.json')
    path = root / 'output' / relative
    if not path.exists():
        return False
    if sha(path) != stopped['checkpoint_outputs'].get(relative):
        raise ValueError('Stopped complete-unit pilot binding changed')
    state = read(path)
    if stage == 'features':
        return state.get('pilot_done') is True and state.get('completed_units', 0) > 0
    draws = 2000 if cell == 'GO3' else 200
    return state.get('pilot_done') is True and len(state.get('draws', [])) >= math.ceil(.05 * draws)


def measured_native(reference, pins):
    value = file_proof(reference, pins)
    if value.get('measured') is not True or value.get('constructed_or_counted_native') is not True:
        raise ValueError('Actual counted unit/memory measurement required')
    native = value.get('native_attempt')
    if not isinstance(native, dict) or set(native) != {'root', 'terminal', 'terminal_sha256', 'plan_sha256'}:
        raise ValueError('Measurement lacks an exact counted native attempt')
    root = Path(native['root']).resolve()
    root.relative_to(ROOT.resolve())
    if native['terminal'] not in ('COMPLETE.json', 'PAUSED.json'):
        raise ValueError('Failed qualification cannot establish usable unit envelope')
    if sha(root / native['terminal']) != native['terminal_sha256'] or sha(root / 'PLAN.json') != native['plan_sha256']:
        raise ValueError('Measured native attempt changed')
    if any((root / name).exists() for name in ('COMPLETE.json', 'PAUSED.json', 'FAILED.json') if name != native['terminal']):
        raise ValueError('Ambiguous measured native attempt')
    plan, terminal = read(root / 'PLAN.json'), read(root / native['terminal'])
    if plan.get('campaign') != 'S15-WEEK5' or plan.get('family') != 'GO' or plan.get('module') not in (FEATURE, ANALYSIS, FEATURE_FIXTURE, BANK_FIXTURE, MATH_FIXTURE):
        raise ValueError('Unrelated work cannot qualify GO3 atomic cost or memory')
    if terminal.get('cpu_seconds') != value.get('attempt_cpu_seconds') or not (root / 'EXECUTE_NATIVE.json').exists():
        raise ValueError('Measurement differs from native cost or identity')
    merge(pins, {str(root / native['terminal']): native['terminal_sha256'], str(root / 'PLAN.json'): native['plan_sha256']})
    merge(pins, plan['pins'])
    return value


def build_plan(request):
    required = {'owner_reviewed', 'attempt', 'stage', 'config', 'collection', 'feature_bank', 'training',
                'scope', 'proofs', 'accounting', 'forecast', 'publication', 'limits', 'resume',
                'design_commit', 'expected_boundary'}
    if set(request) != required or request['owner_reviewed'] is not True:
        raise ValueError('Exact owner-reviewed single-attempt request required')
    if request['stage'] not in ('features', 'analysis'):
        raise ValueError('Only declared GO3 feature or analysis stages allowed')
    if not request['attempt'].startswith('GO3-') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._' for c in request['attempt']):
        raise ValueError('Exact GO3 attempt name required for shared card accounting')
    if (ROOT / request['attempt']).exists() or not request['design_commit']:
        raise ValueError('New attempt and reviewed committed admission design required')
    pins = {}
    scope = file_proof(request['scope'], pins)
    if not (REQUIRED_SCOPE | source_closure()).issubset(scope.get('files', {})):
        raise ValueError('Original source/fold/feature/runtime closure is incomplete')
    for name, value in scope['files'].items():
        path = (REPO / name).resolve()
        path.relative_to(REPO)
        if sha(path) != value:
            raise ValueError('Delivered scientific/source/fold/runtime definition changed')
        merge(pins, {str(path): value})
    if scope.get('complete_original_definitions') is not True:
        raise ValueError('Complete frozen source/fold/feature definition set absent')
    collection_root, support, _ = collection_gate(request['collection'], pins)
    proofs = request['proofs']
    expected_roles = {'feature_supported', 'feature_missing-category'}
    if request['stage'] == 'analysis':
        expected_roles |= {'math_grid', 'bank_supported', 'bank_missing-category'}
    if set(proofs) != expected_roles:
        raise ValueError('Exact counted qualification roster required')
    feature_roots = {case: feature_fixture(proofs['feature_' + case], case, pins) for case in ('supported', 'missing-category')}
    module = FEATURE if request['stage'] == 'features' else ANALYSIS
    config = request['config']
    if request['stage'] == 'features':
        if set(config) != {'phase', 'max_wall_seconds'} or config['phase'] != 'features' or request['feature_bank'] is not None:
            raise ValueError('Exact full-source feature configuration required')
        if not isinstance(request['training'], dict) or set(request['training']) != {'path', 'sha256'} or request['training']['sha256'] != TRAIN_SHA:
            raise ValueError('Original complete external training partition required')
        training = Path(request['training']['path']).resolve()
        # The counted producer authenticates these bytes before reading text.
        merge(pins, {str(training): TRAIN_SHA})
        inputs = dict(collection_run=str(collection_root), iterater_train=str(training))
    else:
        if set(config) != {'phase', 'cell', 'max_wall_seconds', 'max_frame_GiB'} or config['phase'] != 'GO3' or config['cell'] not in CELLS or config['max_frame_GiB'] != 3:
            raise ValueError('Exact original complete grid cell and frozen 3-GiB frame envelope required')
        if request['training'] is not None:
            raise ValueError('Analysis consumes only its complete feature bank')
        math_gate(proofs['math_grid'], pins)
        for case in ('supported', 'missing-category'):
            _, _, proof_plan = completed(proofs['bank_' + case], BANK_FIXTURE,
                (*BANK_FLAGS, 'constructed_only', 'original_complete_bank_analysis_exact'), pins)
            if proof_plan['config'].get('cell') != 'GO3' or Path(proof_plan['inputs']['feature_run']).resolve() != feature_roots[case]:
                raise ValueError('Actual primary bank/branch qualification differs')
        bank_root, bank_done, bank_plan = completed(request['feature_bank'], FEATURE, FEATURE_FLAGS, pins)
        if Path(bank_plan['inputs']['collection_run']).resolve() != collection_root:
            raise ValueError('Feature bank uses another source collection')
        bank = sealed_json(bank_root, bank_done, 'output/FEATURES.json')
        if any(bank.get(k) is not True for k in ('complete_features', 'all_source_rows_retained', 'feature_only')) or bank['rows_projected'] != support['rows']:
            raise ValueError('Incomplete or mis-scoped feature bank')
        inputs = dict(feature_run=str(bank_root))
    limits = request['limits']
    if set(limits) != {'cpu_seconds', 'wall_seconds', 'ram_GiB'} or any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in limits.values()):
        raise ValueError('Finite bounded attempt resources required')
    if limits['cpu_seconds'] > 7200 or limits['wall_seconds'] > 14400 or limits['ram_GiB'] > 4:
        raise ValueError('Attempt envelope exceeds reviewed scaffold')
    if not 0 < config['max_wall_seconds'] <= min(900, limits['wall_seconds'] - 60):
        raise ValueError('Whole-unit cooperative quantum must leave supervisor grace')
    if limits['ram_GiB'] < 3:
        raise ValueError('Existing feature/frame planning envelope is 3 GiB')
    check_budget(request, pins)
    forecast = file_proof(request['forecast'], pins)
    if forecast.get('owner_reviewed') is not True or forecast.get('module') != module or forecast.get('config') != config or forecast.get('inputs') != inputs:
        raise ValueError('Exact source/cell cost and memory review required')
    for key in ('forecast_cpu_seconds', 'longest_atomic_wall_seconds', 'projected_peak_ram_GiB'):
        if not isinstance(forecast.get(key), (int, float)) or not math.isfinite(forecast[key]) or forecast[key] <= 0:
            raise ValueError('Measured unit envelope and explicit forecast required')
    if forecast['longest_atomic_wall_seconds'] >= limits['wall_seconds'] - config['max_wall_seconds'] or forecast['projected_peak_ram_GiB'] > limits['ram_GiB']:
        raise ValueError('Measured indivisible unit or memory cannot fit this attempt')
    if not forecast.get('native_measurement_receipts'):
        raise ValueError('Unmeasured qualification forecast cannot admit corpus work')
    for ref in forecast['native_measurement_receipts']:
        measured_native(ref, pins)
    io_root, io_done, _ = completed(request['publication'], PUBLICATION_FIXTURE,
        ('deterministic_publication_cases_replayed', 'constructed_only', 'no_model_or_source_execution'), pins)
    io_proof = sealed_json(io_root, io_done, 'output/PROOF.json')
    if io_proof.get('publication_spec') != 'GO3-UUID-1' or io_proof.get('deterministic_atomic_publication_cases_passed') is not True:
        raise ValueError('Exact counted UUID publication contract remains unqualified')
    for name, value in io_proof['sources'].items():
        if sha(name) != value:
            raise ValueError('Qualified publication helper/monitor source changed')
        merge(pins, {name: value})
    prior = resume_gate(request, module, inputs, pins)
    boundary = request['expected_boundary']
    if boundary not in ('execute-pilot', 'verify-pilot', 'resource-pause', 'complete'):
        raise ValueError('Explicit next boundary required')
    if prior is None and boundary not in ('execute-pilot', 'resource-pause'):
        raise ValueError('Fresh complete-bank work must cross its first counted pilot')
    if prior and forecast['forecast_cpu_seconds'] > 7200:
        actual_pilot = observed_pilot(prior, request['stage'], config.get('cell'))
        if actual_pilot:
            if forecast.get('pilot_reviewed') is not True or forecast.get('pilot_plan_sha256') != request['resume']['plan_sha256']:
                raise ValueError('Long continuation lacks exact stopped-pilot cost review')
        elif forecast.get('route') != 'continue-to-first-pilot' or boundary not in ('execute-pilot', 'verify-pilot', 'resource-pause'):
            raise ValueError('Early resource pause cannot be relabelled as a complete five-percent pilot')
    design = REPO / 'docs/design/stage-15/week5/GO3_PUBLICATION.md'
    merge(pins, {str(design): sha(design), str(Path(__file__)): sha(__file__)})
    return dict(campaign='S15-WEEK5', family='GO', card=request['attempt'], module=module, inputs=inputs, config=config,
                pins=pins, design=str(design), reviewed_design_commit=request['design_commit'],
                fixture_passed=True, owner_reviewed=True, validation_receipts=[str(io_root / 'VERIFIED.json')],
                paid=False, gpu=False, ollama=False, numerical_threads=2, max_cpu_seconds=limits['cpu_seconds'],
                max_wall_seconds=limits['wall_seconds'], projected_peak_ram_GiB=limits['ram_GiB'],
                forecast_cpu_seconds=forecast['forecast_cpu_seconds'], pilot_fraction=.05,
                expected_owner_boundary=boundary,
                premortem=dict(case_and_check='Complete source/fold/feature identities; actual counted qualification and fresh replay before separate science admission.',
                               smaller_route='Preserve complete checkpoint and all charges. No implicit clipping, site omission, reduced draws or editor sampling.'),
                **({'resume': request['resume']} if prior else {}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('request', type=Path)
    parser.add_argument('--emit-plan', type=Path, required=True)
    args = parser.parse_args()
    plan = build_plan(read(args.request))
    merge(plan['pins'], {str(args.request.resolve()): sha(args.request)})
    with args.emit_plan.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(plan, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(prepared_plan=str(args.emit_plan.resolve()), admitted=False, launched=False,
                          required_next='Owner independently reviews and invokes existing launcher for this one attempt only.')))


if __name__ == '__main__':
    main()
