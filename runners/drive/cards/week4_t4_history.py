"""T4 past-only history prototypes and raw menu features; no fitted model.

DESIGN CHECK: LESSONS 3-5 reread November 2. Future/equal-time sessions and
the target writer must never enter their population comparison. Known vectors
test both selectors against brute-force answers; missing/zero histories remain
unsupported under both null and alternative. No outcome gate is applied here.
"""
from pathlib import Path
from collections import Counter, defaultdict
import time
import numpy as np
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .timing_pmap_source import completed
from runners.stage14.common import digest


def configuration(mode):
    if mode not in ('constructed', 'timing', 'full'):
        raise ValueError('Unknown history scope')
    return dict(card='T4-history', mode=mode, tolerance=1e-10, pilot_sessions=140)


def unit(vector):
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > 1e-12 else None


def prepare_histories(histories, vector):
    out = []
    for s in sorted(histories, key=lambda x: (x['end_at'], x['session'])):
        if not np.isfinite([s['timestamp'], s['end_at']]).all() or s['end_at'] < s['timestamp']:
            raise ValueError('Invalid source chronology')
        if s['sequences']:
            values = np.asarray([vector(r) for r in s['sequences']], dtype=np.float64)
            out.append(dict(session=s['session'], writer=s['writer'], end_at=s['end_at'],
                            count=len(values), total=values.sum(axis=0)))
    if len({s['session'] for s in out}) != len(out):
        raise ValueError('Duplicate history session')
    return out


class Sweep:
    def __init__(self, histories):
        self.histories = histories
        self.index = 0
        self.sums, self.counts, self.sessions = {}, Counter(), defaultdict(list)
        self.last = -float('inf')

    def at(self, clock):
        if clock < self.last:
            raise ValueError('Nonmonotone target clock')
        self.last = clock
        while self.index < len(self.histories) and self.histories[self.index]['end_at'] < clock:
            h = self.histories[self.index]; w = h['writer']
            self.sums[w] = self.sums.get(w, np.zeros_like(h['total'])) + h['total']
            self.counts[w] += h['count']; self.sessions[w].append(h['session'])
            self.index += 1
        return self.sums, self.counts, self.sessions


class Prefix:
    """Separate selector: no production sweep state or advancement logic."""
    def __init__(self, histories):
        groups = defaultdict(list)
        for h in histories: groups[h['writer']].append(h)
        self.groups = {}
        for w, hs in groups.items():
            hs = sorted(hs, key=lambda x: (x['end_at'], x['session']))
            self.groups[w] = (np.asarray([h['end_at'] for h in hs]),
                np.cumsum([h['total'] for h in hs], axis=0),
                np.cumsum([h['count'] for h in hs]), [h['session'] for h in hs])

    def at(self, clock):
        sums, counts, sessions = {}, {}, {}
        for w, (ends, totals, sizes, ids) in self.groups.items():
            n = int(np.searchsorted(ends, clock, side='left'))
            if n:
                sums[w] = totals[n-1]; counts[w] = int(sizes[n-1]); sessions[w] = ids[:n]
        return sums, counts, sessions


def prototypes(state, writer):
    sums, counts, sessions = state
    own = unit(sums[writer]) if writer in sums else None
    donors = [(w, unit(sums[w])) for w in sorted(sums) if w != writer]
    donors = [(w, v) for w, v in donors if v is not None]
    pop = unit(np.sum([v for w, v in donors], axis=0)) if donors else None
    ids = sorted(sid for w in sessions if w != writer for sid in sessions[w])
    witness = dict(own_sequences=int(counts.get(writer, 0)), other_writers=len(donors),
                   own_sessions=digest(sorted(sessions.get(writer, []))), population_sessions=digest(ids))
    return own, pop, witness


def make_rows(sessions, histories, menu_refs, vector, verification=False, report=None):
    selector = Prefix(histories) if verification else Sweep(histories)
    pairs = [(s, m) for s in sessions for m in s['menus']]
    pairs.sort(key=lambda pair: (pair[1]['open_at'], pair[0]['session'], pair[1]['ordinal']))
    rows = []
    for index, (s, m) in enumerate(pairs):
        own, pop, witness = prototypes(selector.at(m['open_at']), s['writer'])
        if m['key'] not in menu_refs: raise ValueError('Missing menu representation')
        refs = menu_refs[m['key']]
        if refs['session'] != s['session'] or len(refs['options']) != len(m['options']):
            raise ValueError('Menu representation join differs')
        reasons = []
        if not m['source_supported']: reasons.append('canonical_state_context_or_split')
        if own is None: reasons.append('own_history_missing_or_zero')
        if pop is None: reasons.append('population_history_missing_or_zero')
        features = None
        if not reasons:
            ctx = vector(refs['context'])
            features = [[float(np.dot(vector(ref), own)), float(np.dot(vector(ref), pop)),
                         float(np.log1p(len(text.split()))), float(pos), float(np.dot(vector(ref), ctx))]
                        for pos, (text, ref) in enumerate(zip(m['options'], refs['options']))]
            features.append([0.0]*5)
            if not np.isfinite(features).all(): raise ValueError('Nonfinite features')
        rows.append(dict(key=m['key'], session=s['session'], writer=s['writer'], genre=s['genre'],
                         half=s['half'], open_at=m['open_at'], choice=m['choice'],
                         dismissal_index=m['dismissal_index'], witness=witness, reasons=reasons,
                         features=features, state=[m['previous_five_acceptance'],
                         float(np.log1p(m['seconds_since_last_acceptance'])) if m['seconds_since_last_acceptance'] is not None else None]))
        if report and index % 250 == 0: report(dict(phase='verify-features' if verification else 'features', done=index, total=len(pairs)))
    return rows


def load(inputs):
    if set(inputs) != {'encoding_completion'}: raise ValueError('Exact encoded source required')
    ec = Path(inputs['encoding_completion']); out = ec.parent/'output'
    completed(ec, ec.parent/'PLAN.json')
    for n in ('INVENTORY.json.gz', 'VISIBILITY.json', 'VECTORS.npy', 'SUMMARY.json'): completed(ec, out/n)
    summary = read(out/'SUMMARY.json')
    if summary['mode'] != 'full' or summary['new_texts'] != summary['encoded_texts']:
        raise ValueError('Complete encoding required')
    data = gzread(out/'INVENTORY.json.gz')['source']; ep = read(ec.parent/'PLAN.json')['inputs']
    mc = Path(ep['menus_completion']); completed(mc, mc.parent/'output/MENUS.json.gz')
    sessions = gzread(mc.parent/'output/MENUS.json.gz')
    cc = Path(ep['content_completion']); completed(cc, cc.parent/'VECTORS.npy', fresh=False)
    completed(cc, cc.parent/'VISIBILITY.json', fresh=False)
    old = np.load(cc.parent/'VECTORS.npy', allow_pickle=False)
    new = np.load(out/'VECTORS.npy', allow_pickle=False)
    ov, nv = read(cc.parent/'VISIBILITY.json'), read(out/'VISIBILITY.json')
    ni = {v['key']:i for i,v in enumerate(nv)}
    if len(ni) != len(nv) or len(nv) != len(new): raise ValueError('New vector key coverage differs')
    for a in (old, new):
        if a.ndim != 2 or a.shape[1] != 384 or not np.isfinite(a).all() or not np.allclose(np.linalg.norm(a,axis=1),1,atol=1e-5):
            raise ValueError('Invalid representation bank')
    def vector(ref):
        if 'cached' in ref:
            i = ref['cached']
            if i < 0 or i >= len(old) or ov[i]['key'] != ref['key']: raise ValueError('Cached reference differs')
            return old[i].astype(np.float64)
        return new[ni[ref['new']]].astype(np.float64)
    refs = {m['key']:m for m in data['menus']}
    if len(refs) != len(data['menus']) or set(refs) != {m['key'] for s in sessions for m in s['menus']}:
        raise ValueError('Complete menu coverage differs')
    return sessions, prepare_histories(data['histories'], vector), refs, vector


def known_answers():
    hs = [dict(session='a0',writer='a',end_at=1,count=1,total=np.array([1.,0.])),
          dict(session='b0',writer='b',end_at=2,count=2,total=np.array([0.,2.])),
          dict(session='a_equal',writer='a',end_at=3,count=1,total=np.array([-1.,0.])),
          dict(session='b_future',writer='b',end_at=4,count=1,total=np.array([0.,-1.]))]
    for selector in (Sweep(hs),Prefix(hs)):
        for clock in (1,2,3,4,5):
            sums, counts, ids = {}, Counter(), defaultdict(list)
            for h in hs:
                if h['end_at'] < clock:
                    w=h['writer'];sums[w]=sums.get(w,np.zeros(2))+h['total'];counts[w]+=h['count'];ids[w].append(h['session'])
            expected = prototypes((sums,counts,ids),'a');actual = prototypes(selector.at(clock),'a')
            assert actual[2] == expected[2]
            for a,b in zip(actual[:2],expected[:2]):
                assert (a is None and b is None) or (a is not None and b is not None and np.array_equal(a,b))
    own,pop,w=prototypes(Prefix(hs).at(3),'a')
    assert np.array_equal(own,[1,0]) and np.array_equal(pop,[0,1]) and w['own_sequences']==1
    menu=dict(key='m',ordinal=1,open_at=3,source_supported=True,options=['own word','other'],
              choice=2,dismissal_index=2,previous_five_acceptance=.4,seconds_since_last_acceptance=2)
    sessions=[dict(session='target',writer='a',genre='constructed',half='test',menus=[menu])]
    refs={'m':dict(session='target',options=['own','pop'],context='pop')}
    vectors={'own':np.array([1.,0.]),'pop':np.array([0.,1.])}
    first=make_rows(sessions,hs,refs,vectors.__getitem__)
    assert first==make_rows(sessions,hs,refs,vectors.__getitem__,True)
    assert first[0]['features']==[[1.,0.,float(np.log1p(2)),0.,0.],[0.,1.,float(np.log1p(1)),1.,1.],[0.]*5]
    assert first[0]['choice']==2 and not first[0]['reasons']
    menu['source_supported']=False
    assert make_rows(sessions,hs,refs,vectors.__getitem__)[0]['features'] is None
    return dict(strict_past=True,own_excluded_from_population=True,equal_time_excluded=True,zero_norm_unsupported=True,brute_force_agrees=True,known_features_and_dismissal=True,source_exclusion=True)


def run(output, inputs, config, verification=False):
    if config != configuration(config['mode']): raise ValueError('Frozen configuration required')
    output=Path(output);start=time.process_time();checks=known_answers()
    if config['mode']=='constructed':
        if inputs: raise ValueError('Constructed only')
        values={'SUMMARY.json':dict(checks=checks,scientific_effect_computed=False)};rows=None
    else:
        sessions, histories, refs, vector=load(inputs);total_sessions=len(sessions)
        if config['mode']=='timing': sessions=sorted(sessions,key=lambda s:s['session'])[:140]
        rows=make_rows(sessions,histories,refs,vector,verification,lambda x:progress(output/'PROGRESS.json',x))
        counts=defaultdict(Counter);reasons=Counter()
        for r in rows:
            if not r['reasons']:counts[r['writer']][r['half']]+=1
            for reason in r['reasons']:reasons[reason]+=1
        supported=sorted(w for w,c in counts.items() if c['train']>=20 and c['test']>=20)
        values={'SUMMARY.json':dict(mode=config['mode'],sessions=len(sessions),history_sessions=len(histories),menus=len(rows),eligible_menus=sum(not r['reasons'] for r in rows),supported_writers=len(supported) if config['mode']=='full' else None,required_writers=25,exclusions=dict(reasons),scientific_effect_computed=False,checks=checks),
                'PRIVATE_SUPPORT.json':dict(counts={w:dict(c) for w,c in counts.items()},supported_writers=supported)}
        if verification:
            old=gzread(output/'FEATURES.json.gz')
            if len(old)!=len(rows):raise ValueError('Feature row count differs')
            for a,b in zip(old,rows):
                af,bf=a.pop('features'),b.pop('features')
                if a!=b or (af is None)!=(bf is None):raise ValueError('History identity/state replay differs')
                if af is not None and not np.allclose(af,bf,atol=config['tolerance'],rtol=0):raise ValueError('Feature replay differs')
        else:
            gzip_equal(output/'FEATURES.json.gz',rows)
            write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-start,full_forecast_cpu_seconds=3*(time.process_time()-start)*total_sessions/len(sessions)))
    for name,value in values.items():
        if verification:
            if read(output/name)!=value:raise ValueError('History summary replay differs')
        else:write_equal(output/name,value)
    return dict(verified=True,complete_history_replay=True) if verification else dict(status='complete',scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
