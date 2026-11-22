"""Timestamp-based Phase 0 pairs. The clock projection precedes the feelings.

DESIGN CHECK (LESSONS 3–5). Earlier NT1 clock checks prevent false ordering.
All and short-gap versions use the same draws. A sign or clarity disagreement
leaves the paired reading undecided. See week7/ANSWERED_PROMPTS.md.
"""
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

from . import week7_status_v1 as original
from .batch_runtime import atomic, filehash, freeze, now, read
from .es_clock_v1 import utc_seconds
from .week6_ld_draws_v1 import RequestedYield

CLOCKS = ('id', 'day', 'created_esm', 'ended_esm')
CARDS = ('PSD2', 'ISO1')
RULES = ('all', 'short')
old = original.old


def columns(card):
    return tuple(dict.fromkeys((*CLOCKS, *(k for k in original.columns(card) if k != 'beep'))))


def binding(card, member, root):
    if card not in CARDS:
        raise ValueError('No paired outcome registered for this card')
    path, sha = original.binding(card, member, root)
    schema = read(path.parent.parent/'SCHEMA.json')
    table, = [t for t in schema['files'] if t['file'] == path.name]
    if set(columns(card)) - {c['name'] for c in table['columns']}:
        raise ValueError('Declared clock or outcome column missing')
    return path, sha


def seconds(value):
    try:
        return utc_seconds(str(value))
    except (ValueError, TypeError, AssertionError):
        return np.nan


def chronology(clock):
    f = clock.loc[clock.id.notna() & clock.id.ne(''), list(CLOCKS)].copy()
    f['created'] = f.created_esm.map(seconds)
    f['answered'] = f.ended_esm.map(seconds)
    days = np.floor(f.created/86400)
    expected = days - days.groupby(f.id).transform('min') + 1
    missing = ~np.isfinite(f.created) | ~np.isfinite(f.answered)
    wrong = f.answered.lt(f.created) | f.duplicated(['id','answered'], keep=False)
    wrong |= pd.to_numeric(f.day, errors='coerce').ne(expected)
    invalid = (missing | wrong).groupby(f.id).transform('any')
    invalid_people = f.loc[invalid, 'id'].nunique()
    f['valid_clock'] = ~invalid
    f = f.sort_values(['id','answered'], kind='stable')
    previous = f.id.eq(f.id.shift()) & f.day.eq(f.day.shift()) & f.valid_clock
    f['gap'] = (f.answered.diff()/60).where(previous)
    f['block'] = np.floor((f.answered % 86400)/14400)
    gaps = f.gap.dropna().to_numpy()
    quantiles = (0, .25, .50, .75, .90, .95, 1)
    points = np.quantile(gaps, quantiles).tolist() if len(gaps) else [None]*len(quantiles)
    cap = 2*points[2] if len(gaps) else None
    edges = (0, 30, 60, 120, 240, 480, np.inf)
    summary = dict(people=f.id.nunique(), reports=len(f), clock_excluded_people=int(invalid_people),
                   all_pairs=len(gaps), paired_people=f.loc[previous,'id'].nunique(),
                   gap_minutes=dict(zip(('min','p25','median','p75','p90','p95','max'),points)),
                   bands_minutes_right_inclusive=['0-30','30-60','60-120','120-240','240-480','over 480'],
                   pairs_by_band=[int(((gaps>lo)&(gaps<=hi)).sum()) for lo,hi in zip(edges[:-1],edges[1:])],
                   cap_minutes=cap, short_pairs=int((gaps <= cap).sum()) if len(gaps) else 0)
    assert sum(summary['pairs_by_band']) == len(gaps)
    return f[['id','gap','block']], summary


def reading(main, short):
    def classify(metric):
        point, band = metric['estimate'], metric['interval']
        if point is None or band is None:
            return None
        return (int(np.sign(point)), bool(band[0] > 0 or band[1] < 0))
    a, b = classify(main), classify(short)
    return 'undecided' if a is None or a != b else 'consistent'


def prepare(card, frame, timing, support, replay):
    f = frame.loc[timing.index].copy()
    f['beep'] = timing.block
    for col in columns(card):
        if col in CLOCKS:
            continue
        f[col] = pd.to_numeric(f[col], errors='raise')
        allowed = (1,2) if col=='interaction' else range(1,7)
        if not f.loc[f[col].notna(),col].isin(allowed).all():
            raise ValueError('Undocumented '+col)
    names = ('proud','ashamed') if card == 'PSD2' else ('ashamed','angry','sad')
    for name in names:
        f[name] = np.select([f.interaction.eq(1), f.interaction.eq(2)],
                            [f['int_'+name],f['occup_'+name]], default=np.nan)
    result = original.core.Prepared(f.id.nunique(),dict(clock=support))
    for rule in RULES:
        active = timing.gap.notna()
        if rule == 'short':
            active &= timing.gap.le(support['cap_minutes']) if support['cap_minutes'] is not None else False
        f['adjacent'] = active
        panel = original.core.Prepared(result.people,{})
        groups = f.groupby('id',sort=True)
        if card == 'ISO1':
            f['next_no'] = f.interaction.shift(-1).map({1:0.,2:1.}).where(active.shift(-1,fill_value=False))
            blocks = sorted(f.dropna(subset=['beep','next_no','interaction',*names]).beep.unique())
            panel.panels['iso'] = np.stack([original.iso_moments(g,blocks,replay) for _,g in groups])
            keys = (*names,'ashamed_minus_others')
            result.metadata[rule] = dict(observed_clock_blocks=[int(b) for b in blocks],
                model_pairs=len(f.dropna(subset=['beep','next_no','interaction',*names])))
        else:
            panel.panels['dial'] = np.array([original.dial_terms(g) for _,g in groups])
            keys = ('fall_proud','fall_ashamed','fall_share_proud','fall_share_ashamed')
        panel.specs = {k:{} for k in keys}
        result.panels[rule] = panel
        result.specs.update({rule+'/'+k:{} for k in keys})
    return result


def evaluate(data, weights, guard, *, verify=False):
    results = {}
    for rule, panel in data.panels.items():
        values = original.evaluate(panel, weights, guard, verify=verify)
        results.update({rule+'/'+k:values[k] for k in panel.specs})
    return results


def operate(output, inputs, config, replay):
    card, member = config['card'], config['member']
    path, pin = binding(card,member,inputs['data_root'])
    if pin != inputs['source_sha256'] or inputs['manifest_sha256'] != old.MANIFEST:
        raise ValueError('Different source')
    directory = Path(output)/('verify' if replay else 'execute')
    directory.mkdir(exist_ok=True,parents=True)
    def pinned(name, value):
        dest = directory/name
        if dest.exists():
            if read(dest) != value:
                raise ValueError('Different checkpoint '+name)
        else:
            freeze(dest,value)
    timing, support = chronology(pd.read_csv(path,sep='\t',usecols=list(CLOCKS),dtype={'id':str}))
    pinned('GAP_DISTRIBUTION.json',support)
    if replay and read(Path(output)/'execute/GAP_DISTRIBUTION.json') != support:
        raise ValueError('Timing projection differs on replay')
    frame = pd.read_csv(path,sep='\t',usecols=columns(card),dtype={'id':str})
    data = prepare(card,frame,timing,support,replay)
    start = time.monotonic()
    def guard():
        if time.monotonic()-start >= config['max_wall_seconds'] or any((Path(output)/n).exists() for n in ('STOP_REQUEST.json','YIELD_REQUEST.json')):
            raise RequestedYield('runtime limit')
    def progress(n, elapsed):
        atomic(directory/'DRAW_PROGRESS.json',dict(at=now(),committed_draws=n,elapsed=elapsed))
    try:
        result = original.bank.run(directory,sys.modules[__name__],data,member=member,source_digest=pin,
            seed=202611190000+int(member),guard=guard,verify=replay,execute_dir=Path(output)/'execute',
            limit=config['max_new_draws'],progress=progress)
    except RequestedYield as exc:
        return dict(status='yielded',verified=False,reason=str(exc))
    result['agreement'] = {key:reading(result['metrics']['all/'+key],result['metrics']['short/'+key])
                           for key in data.panels['all'].specs}
    pinned('ENGINE_RESULT.json',result)
    return dict(status='verified' if replay else 'computed',verified=replay,
                engine_sha256=filehash(directory/'ENGINE_RESULT.json'),draw_count=2000)


def execute(output,inputs,config):
    return operate(output,inputs,config,False)


def verify(output,inputs,config):
    return operate(output,inputs,config,True)
