"""Authenticate the entire frozen CH1 roster before exposing analytical rows.

DESIGN CHECK: count completion is not population completion. Every input row,
node limit and score is joined exactly; missing, extra and duplicate rows refuse.
Temperature uses a different month from the outcome row, never its own choice.
"""
from collections import Counter,defaultdict
from pathlib import Path
import gzip,json
from .week5_ch_source import digest,write_json
from .week5_ch_engine import iter_positions,score_key,fit_temperature,policy_entropy


def verified_spec(spec):
    path=Path(spec['path'])
    if digest(path)!=spec['sha256']:raise ValueError('Input binding changed')
    return path


def collect(positions,batches,nodes=1000000):
    expected={}
    for row in iter_positions(positions):
        key=score_key(row,nodes)
        if key in expected:raise ValueError('Duplicate frozen position')
        expected[key]=row
    if not expected:raise ValueError('Empty frozen position roster')
    scored={};pins=[]
    for batch in batches:
        directory=Path(batch['path']);proof=json.loads(verified_spec(batch['verify']).read_text(encoding='utf8'))
        report=json.loads(verified_spec(batch['report']).read_text(encoding='utf8'))
        files=sorted(directory.glob('*.json'))
        if not proof.get('all_scores_equal') or proof['verified_positions']!=len(files):raise ValueError('Unverified batch')
        if report['node_limit']!=nodes or report['new_positions']+report['reused_positions']!=len(files):raise ValueError('Batch count mismatch')
        manifest=json.loads(verified_spec(batch['score_bindings']).read_text(encoding='utf8'))
        if set(manifest)!=set(f.name for f in files):raise ValueError('Incomplete score bindings')
        for file in files:
            if digest(file)!=manifest[file.name]:raise ValueError('Score changed after replay')
            value=json.loads(file.read_text(encoding='utf8'));key=score_key(value['position'],value['node_limit'])
            if key!=file.stem or key not in expected or value['position']!=expected[key]:raise ValueError('Score outside frozen roster')
            if key in scored:raise ValueError('Duplicate scored position')
            scored[key]=value
        pins.append(dict(verify_sha256=batch['verify']['sha256'],report_sha256=batch['report']['sha256'],bindings_sha256=batch['score_bindings']['sha256']))
    if set(scored)!=set(expected):raise ValueError(f'Incomplete frozen roster: {len(scored)}/{len(expected)}')
    rows=[dict(scored[key]['position'],**scored[key]['engine']) for key in sorted(expected)]
    return rows,dict(positions=len(rows),players=len({r['player'] for r in rows}),node_limit=nodes,batch_pins=pins)


def with_entropy(rows):
    groups=defaultdict(list)
    for r in rows:
        if not r['mate_sentinel_used']:groups[(r['month'],r['rating']//400)].append(r)
    months=sorted({r['month'] for r in rows});fits={};output=[];counts=Counter()
    for target in months:
        # The earliest other frozen month is the single predeclared calibration
        # month. This choice reads no performance measure or fitted temperature.
        donor=next((m for m in months if m!=target),None)
        for band in sorted({r['rating']//400 for r in rows if r['month']==target}):
            calibration=groups.get((donor,band),[]);scores=[];indices=[]
            for row in calibration:
                scores.append([r['cp'] for r in row['top']]);indices.append(next((i for i,r in enumerate(row['top']) if r['move']==row['uci']),None))
            fit=fit_temperature(scores,indices);fit.update(target_month=target,calibration_month=donor,rating_band=int(band),outside_top_five=sum(i is None for i in indices))
            fits[(target,band)]=fit
    for row in rows:
        fit=fits[(row['month'],row['rating']//400)];r=dict(row)
        if row['mate_sentinel_used']:r.update(entropy=None,entropy_fixed100=None);counts['mating_entropy_excluded']+=1
        else:
            scores=[v['cp'] for v in row['top']];fixed=policy_entropy(scores,100.)
            r.update(entropy=policy_entropy(scores,fit['temperature']) if fit['status']=='fitted' else None,entropy_fixed100=fixed)
            counts['fitted_entropy' if r['entropy'] is not None else 'uncalibrated_entropy']+=1
        output.append(r)
    return output,dict(fits=[fits[k] for k in sorted(fits)],counts=dict(counts))


def write_rows(path,rows):
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    # Stable gzip header permits complete source-based replay hashes.
    with path.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as f:
        for row in rows:f.write((json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode())


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    roster=verified_spec(inputs['positions']);plan=json.loads(verified_spec(inputs['batches']).read_text(encoding='utf8'))
    rows,receipt=collect(roster,plan['batches'],config.get('nodes',1000000));rows,temperatures=with_entropy(rows)
    write_rows(output/'PRIVATE_ANALYTICAL_ROWS.jsonl.gz',rows)
    receipt.update(population_complete=True,constructed_fixture=bool(config.get('constructed_fixture')),roster_sha256=inputs['positions']['sha256'],batches_manifest_sha256=inputs['batches']['sha256'],rows_sha256=digest(output/'PRIVATE_ANALYTICAL_ROWS.jsonl.gz'))
    write_json(output/'TEMPERATURES.json',temperatures);write_json(output/'COLLECTION.json',receipt)
    return dict(status='complete',positions=len(rows),population_complete=True)


def verify(output,inputs,config):
    output=Path(output);execute(output/'replay',inputs,config)
    for name in ('COLLECTION.json','TEMPERATURES.json','PRIVATE_ANALYTICAL_ROWS.jsonl.gz'):
        if digest(output/name)!=digest(output/'replay'/name):raise ValueError('Full CH collection replay differs')
    return dict(verified=True,complete_recalculation=True)


def load_complete(inputs):
    rows_path=verified_spec(inputs['scores']);receipt=json.loads(verified_spec(inputs['collection']).read_text(encoding='utf8'))
    if not receipt.get('population_complete') or receipt.get('constructed_fixture') or receipt['rows_sha256']!=inputs['scores']['sha256']:raise ValueError('Incomplete or constructed CH1 population')
    with gzip.open(rows_path,'rt',encoding='utf8') as f:rows=[json.loads(line) for line in f]
    if len(rows)!=receipt['positions'] or len({r['player'] for r in rows})!=receipt['players']:raise ValueError('Collection denominator changed')
    return rows
