"""Bounded exact matching/provenance parity; no scientific regression."""
from copy import deepcopy
import gc
from pathlib import Path
import random
import time

import pytest

from runners.drive.cards import timing_d33_match as scalar
from runners.drive.cards import timing_d33_supported_counts as fast
from runners.drive.cards import timing_d33_supported_prefix as prefix
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import progress

REPO=Path(__file__).resolve().parents[1]
PRIVATE=REPO/'.agent-state/drive-20261017/builder2'


def session(writer,sid,n,stamp=1,prompt='p'):
    return dict(writer=writer,session=sid,timestamp=stamp,end_at=stamp+1,prompt=prompt,
        training_sequences=[['word']*n,[]])


def same_answer_or_refusal(writers,target,exclude=False):
    unchanged=deepcopy(writers)
    try:answer=scalar.matched_other(writers,target,exclude)
    except Exception as error:
        with pytest.raises(type(error),match='^'+__import__('re').escape(str(error))+'$'):
            fast.matched_other(writers,target,exclude)
    else:assert fast.matched_other(writers,target,exclude)==answer
    assert writers==unchanged


def test_counts_reuse_only_plain_records_and_preserve_refusals():
    calls=[]
    def counting(value):calls.append(value);return scalar.token_count(value)
    count=fast.TokenCounts(counting);s=session('w','s',3)
    assert [count(s) for _ in range(20)]==[3]*20
    assert len(calls)==1 and count.memo[id(s)][0] is s
    unusual=dict(s,training_sequences=(['word'],))
    assert count(unusual)==count(unusual)==1
    assert len(calls)==3 # Non-native sequence protocol is never memoized.
    for malformed in ({},{'training_sequences':None},{'training_sequences':[None]}):
        try:scalar.token_count(malformed)
        except Exception as error:
            with pytest.raises(type(error)):count(malformed)
        else:raise AssertionError('malformed counter fixture accepted')


def test_known_capacity_ties_prompt_exclusion_and_zero_history():
    target=session('a','target',0,20)
    writers={'a':[session('a','a0',5,1),session('a','a1',2,4)],
        'b':[session('b','b0',1,1),session('b','b1',8,4),session('b','b2',3,8,'q')],
        'c':[session('c','c0',4,1),session('c','c1',4,4),session('c','future',99,30)]}
    for exclude in (False,True):same_answer_or_refusal(writers,target,exclude)
    same_answer_or_refusal(writers,dict(target,timestamp=0))
    same_answer_or_refusal({'a':writers['a'],'b':[]},target)


def test_random_complete_proofs_donors_and_allocations_match():
    rng=random.Random(20261018)
    for trial in range(48):
        writers={}
        for w in range(rng.randrange(2,7)):
            writer=str(w);writers[writer]=[]
            for s in range(rng.randrange(0,8)):
                row=session(writer,f'{w}-{s}',rng.randrange(0,12),rng.randrange(0,20),rng.choice(['p','q']))
                row['training_sequences'].append(['x']*rng.randrange(0,5));writers[writer].append(row)
        target=session('0','target',0,rng.randrange(0,25),rng.choice(['p','q']))
        for exclude in (False,True):same_answer_or_refusal(writers,target,exclude)


def test_new_matching_call_recounts_and_malformed_matching_still_refuses():
    target=session('a','target',0,20)
    writers={'a':[session('a','a0',3)],'b':[session('b','b0',4)]}
    before=fast.matched_other(writers,target)
    writers['b'][0]['training_sequences'][0].extend(['new']*8)
    after=fast.matched_other(writers,target)
    assert after==scalar.matched_other(writers,target) and after!=before
    for change in ('missing','bad_sequence','bad_clock','duplicate_id'):
        broken=deepcopy(writers)
        if change=='missing':del broken['b'][0]['training_sequences']
        elif change=='bad_sequence':broken['b'][0]['training_sequences']=[None]
        elif change=='bad_clock':broken['b'][0]['end_at']='invalid'
        else:
            broken['a'].append(session('a','a1',2))
            broken['b'].append(dict(broken['b'][0]))
        same_answer_or_refusal(broken,target)


def test_full_authenticated_source_matching_proofs_and_constructor_timing(tmp_path):
    started=time.perf_counter()
    ready=read(PRIVATE/'READY_D33_SUPPORTED_PREFIX_20261018.json')
    for path,sha in ready['source_closure'].items():assert filehash(REPO/path)==sha
    inputs=ready['inputs'];timings={};snapshots={}
    # Both complete source constructors independently re-read/authenticate P6,
    # reconstruct all original rows, and rebuild both variants' saved proofs.
    # No raw screen census, calibration change or scientific inference is run.
    for name,cls in [('scalar_matching',prefix.Sources),('memoized_matching',fast.Sources)]:
        progress(tmp_path/'PROGRESS.json',dict(phase=name,seconds=time.perf_counter()-started))
        t=time.perf_counter();obj=cls(inputs,tmp_path/name,False);timings[name]=time.perf_counter()-t
        snapshots[name]=dict(saved=obj.saved,roster=obj.roster,units=obj.units,
            supported_rosters={v:obj.roster_for(v) for v in ('pair','pair2')},
            raw_population=obj.raw.population)
        assert obj.raw.session.__func__ is prefix.raw_session
        del obj;gc.collect()
        progress(tmp_path/'PROGRESS.json',dict(phase=name+'-complete',seconds=time.perf_counter()-started,timings=timings))
    assert snapshots['scalar_matching']==snapshots['memoized_matching']
    proof_count=sum(len(v) for v in snapshots['memoized_matching']['units'].values())
    write(tmp_path/'MATCHING_SOURCE_PARITY.json',dict(seconds=time.perf_counter()-started,
        constructor_seconds=timings,memoized_to_scalar_ratio=timings['memoized_matching']/timings['scalar_matching'],
        exact_saved_proofs=proof_count,variants=['pair','pair2'],
        original_primary_rows=len(snapshots['memoized_matching']['saved']['rows']),
        parity='Exact full original rows/tuning/exclusions, chronological roster, both complete matching proof dictionaries and supported rosters; same raw population. Each constructor independently authenticates all input and saved proof files.',
        source_inputs_sha256=ready['input_pins'],scientific_fit=False,
        order='Full scalar source constructor then full memoized source constructor; no speed credit for unchanged source/covariate/inference phases; warm-cache order is a limitation.'))
