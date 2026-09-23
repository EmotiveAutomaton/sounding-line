"""Offline reference-law sensitivity of bound, already completed readings.

DESIGN CHECK: LESSONS 3-5, CONTROLS 6-7. NULL: unchanged law reproduces
every original loss, including invalids. ALTERNATIVE: changed coefficients
can change reference probabilities without changing public evidence or support.
No network, model call, new fit or claim of fresh reader observations.
"""
from .common import read, freeze, digest, filehash, distribution
from .ghost_bridge import load_source
from .output_interface import rows_for_card
from .local_api import parse


def target_for(model, records, reference, direction):
    public = reference['public']
    matches = [r for r in records if model.project(r, public['tier']) == public]
    support = digest(sorted(digest({k:v for k,v in r.items() if k!='probability'}) for r in matches))
    if direction == 'forward-given-goal':
        goal = reference['actual']['steps'][0]['goal']
        matches = [r for r in matches if r['steps'][0]['goal']==goal]
    if not matches:
        raise ValueError('empty compatible support')
    field = 'goal' if direction=='reverse-local-goal' else 'operation'
    labels = model.GOALS if field=='goal' else model.OPERATIONS
    mass = sum(r['probability'] for r in matches)
    target = [sum(r['probability'] for r in matches if r['steps'][0][field]==v)/mass for v in labels]
    template = [sum(r['steps'][0][field]==v for r in matches)/len(matches) for v in labels]
    return target, template, support


def run(out, card, pulse, raw):
    source = raw/'jobs'/card['compile_card']
    references = {r['source']:r for r in read(source/'REFERENCES.json')}
    requests = read(source/'REQUESTS.json')
    original_targets = {r['id']:r for r in read(source/'EVALUATOR_ONLY.json')}
    forecasts, original_rows = {}, {}
    for job in card['source_jobs']:
        directory = raw/'jobs'/job
        terminal = read(directory/'COMPLETE.json')
        if terminal['status']!='complete':
            raise ValueError('source incomplete')
        for name, expected in terminal['output_files'].items():
            if filehash(directory/name) != expected:
                raise ValueError('source output changed')
        manifest = read(raw/'manifests'/(job+'.json'))
        selected = rows_for_card([r for r in requests if r['source'] in manifest['sources']], manifest)
        for row in read(directory/'ROWS.json'):
            if row['id'] in original_rows:
                raise ValueError('duplicate original reading')
            original_rows[row['id']] = row
        for r in selected:
            path = directory/'calls'/r['id']
            if read(path/'REQUEST.json') != r['request']:
                raise ValueError('saved request differs')
            try:
                p = parse(read(path/'RAW.json'), len(r['labels']), r['request']['format'])
            except (ValueError, KeyError, TypeError):
                p = None
            if distribution(p, original_targets[r['id']]['oracle_family_target']) != original_rows[r['id']]['oracle_family_score']:
                raise ValueError('original raw score does not reproduce')
            forecasts[r['id']] = p
    if len(forecasts)!=144 or set(forecasts)!={r['id'] for r in requests}:
        raise ValueError('incomplete original roster')
    model = load_source(card['generator_source'])
    rows, support_zero, laws = [], {}, []
    for lineage in [0]+card['lineages']:
        world = model.law(lineage)
        records = model.enumerate_world(world)
        if len(records)!=13824 or abs(sum(r['probability'] for r in records)-1)>1e-10:
            raise ValueError('source law normalization')
        cache = {}
        for r in requests:
            key = (r['source'], r['direction'])
            if key not in cache:
                cache[key] = target_for(model, records, references[r['source']], r['direction'])
            target, template, support = cache[key]
            if lineage == 0:
                support_zero[key] = support
                if any(abs(a-b)>1e-12 for a,b in zip(target, original_targets[r['id']]['oracle_family_target'])):
                    raise ValueError('lineage zero identity failed')
            elif support != support_zero[key]:
                raise ValueError('changed law altered compatible public support')
            rows.append(dict(lineage=lineage, id=r['id'], source=r['source'], method=r['method'],
                direction=r['direction'], forecast=forecasts[r['id']], target=target,
                reader=distribution(forecasts[r['id']], target), exact=distribution(target, target),
                template=distribution(template, target), uniform=distribution([1/len(target)]*len(target), target),
                support_sha256=support, original_correspondence=original_rows[r['id']]['correspondence']))
        laws.append(world)
        pulse(phase='frozen-reader-law-sensitivity', completed=len(laws), total=len(card['lineages'])+1)
    freeze(out/'ROWS.json', rows)
    freeze(out/'LAWS.json', laws)
    return dict(status='complete', kind='scientific', frozen_readings=len(forecasts), laws=len(laws),
        rows=len(rows), calls=0, scope='Reference-assumption sensitivity of fixed exposed readings; no new reader observations',
        controls=dict(raw_reparsed=True, original_law_identity=True, identical_public_support=True,
                      normalized_laws=True, invalids_retained=True, all_rivals=True),
        files={n:filehash(out/n) for n in ('ROWS.json','LAWS.json')})
