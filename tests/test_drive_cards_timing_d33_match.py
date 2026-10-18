import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from runners.drive.cards import timing_d33_match as match


def session(name,writer,prompt,tokens,start=0,end=1):
    return dict(session=name,writer=writer,prompt=prompt,timestamp=start,end_at=end,
        training_sequences=[['a']*tokens],words=[])


def test_exact_history_matching_future_exclusion_and_source_immutability():
    own=[session('o1','own','p',4),session('o2','own','q',6,2,3)]
    donors=[session('d1','other','p',6),session('d2','other','q',6,2,3),session('future','other','q',100,4,20)]
    target=session('target','own','q',9,10,11);source={'own':own+[target],'other':donors};before=copy.deepcopy(source)
    proof,selected=match.matched_other(source,target)
    assert proof['supported'] and proof['donor_tokens']==10 and len(selected)==2
    assert proof['prompt_matches']==2 and proof['donor_sessions']==['d1','d2']
    assert source==before


def test_pair2_excludes_target_prompt_from_both_caches():
    target=session('target','own','q',5,10,11)
    source={'own':[session('a','own','p',5),session('b','own','q',7)],
        'other':[session('c','other','p',7),session('d','other','q',500)]}
    proof,donor=match.matched_other(source,target,True)
    assert proof['own_sessions']==['a'] and proof['donor_sessions']==['c'] and proof['donor_tokens']==5


def test_insufficient_exact_capacity_retains_explicit_unsupported_target():
    target=session('target','own','p',5,10,11)
    proof,donor=match.matched_other({'own':[session('a','own','p',10)],'other':[session('b','other','p',9)]},target)
    assert not proof['supported'] and donor is None and proof['target_session']=='target'


def test_feasibility_guard_does_not_choose_too_small_close_match():
    own=[session('a','own','p',4),session('b','own','q',6)]
    available=[session('c','other','p',4),session('d','other','q',3),session('e','other','r',7)]
    selected=match.select_sessions(available,own)
    assert len(selected['sessions'])==2 and selected['capacity']>=10


@pytest.mark.parametrize('capacities,budget',[([7,3],5),([0,3,8],7),([1,1,1],2),([0,0],0)])
def test_prefix_budgets_preserve_boundaries(capacities,budget):
    allocated=match.allocated_budgets(capacities,budget)
    assert sum(allocated)==budget and all(a<=c for a,c in zip(allocated,capacities))
    assert match.truncate_sequences([['a','b'],['c','d']],3)==[['a','b'],['c']]


def test_matching_never_reads_target_outcomes_or_word_features():
    target=session('target','own','q',5,10,11)
    source={'own':[session('a','own','p',5)],'other':[session('b','other','p',7)]}
    first=match.matched_other(source,target)[0]
    target.update(words=[dict(log_pause=-999,accepted=False)],handling='dismiss',personal_surprise=1e9)
    assert match.matched_other(source,target)[0]==first


def test_primary_roster_rejects_negative_index_and_duplicate_tuning():
    records=[session(f's{i}','w','p',1,i*10,i*10+1) for i in range(5)]
    for r in records:r['words']=[dict(token='a')]
    row=dict(session='s4',writer='w',index=-1);tuning=[dict(writer='w',alpha=.1)]
    with pytest.raises(ValueError,match='identity'):match.primary_roster([row],records,tuning)
    row['index']=0
    with pytest.raises(ValueError,match='duplicate original tuning'):match.primary_roster([row],records,tuning+tuning)


def fixture(root):
    """Full original population size, constructed inputs only, no fit."""
    from runners.drive.cards.timing_census import write,filehash
    from runners.drive.cards.timing_p6 import gzwrite
    from runners.drive.cards.timing_d33 import make_rows
    root=Path(root).resolve();records=[];index=[]
    for wi in range(41):
        for si in range(5):
            r=session(f'w{wi:02}_s{si}',f'w{wi:02}',f'p{si%2}',5,si*100+wi,si*100+wi+10)
            n=1917+int(wi<5) if si==4 else 1
            r['words']=[dict(index=j,token='a',is_word=True,context=[],population_probability=.1,
                pause_seconds=.2,first_delta_characters=1,length=1,population_log_frequency=-2.,
                sentence_start=True,after_punctuation=False) for j in range(n)]
            path=root/'p6'/(r['session']+'.json.gz');gzwrite(path,r)
            index.append(dict(session=r['session'],writer=r['writer'],file=path.name,sha256=filehash(path)))
            records.append(r)
    def complete(folder,names):write(folder/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:filehash(folder/n) for n in names}))
    write(root/'p6/INDEX.json',index);complete(root/'p6',['INDEX.json'])
    write(root/'tc/PRIMARY.json',dict(timing_mode='per_character'));complete(root/'tc',['PRIMARY.json'])
    inputs=dict(p6_index=str(root/'p6/INDEX.json'),p6_completion=str(root/'p6/COMPLETE.json'),
        tc_primary=str(root/'tc/PRIMARY.json'),tc_completion=str(root/'tc/COMPLETE.json'))
    rows,tuning,exclusions=make_rows(records,'per_character');assert len(rows)==78602
    write(root/'d33/PLAN.json',dict(module='runners.drive.cards.timing_d33',config=dict(extension=False,bootstrap_draws=2000,seed=20261017),inputs=inputs))
    gzwrite(root/'d33/output/D33_INTERMEDIATES.json.gz',dict(rows=rows,tuning=tuning,exclusions=exclusions))
    write(root/'d33/output/D33_PRIMARY.json',dict(observations=78602,writers=41))
    complete(root/'d33',['PLAN.json','output/D33_INTERMEDIATES.json.gz','output/D33_PRIMARY.json'])
    inputs['d33_completion']=str(root/'d33/COMPLETE.json');write(root/'INPUTS.json',inputs)
    return inputs


def test_serialized_exact_population_intake_and_fresh_verify(tmp_path):
    from runners.drive.cards import timing_d33_pair_intake as card
    from runners.drive.cards.timing_census import read,write
    start=time.monotonic();inputs=fixture(tmp_path/'source');out=tmp_path/'output'
    write(out/'YIELD_REQUEST.json',dict(reason='constructed checkpoint'))
    yielded=card.execute(out,inputs,card.CONFIG)
    assert yielded['status']=='yielded' and yielded['completed']==1
    first=out/'sessions/pair/w00_s3.json';old=first.read_bytes();prior=read(out/'ACTIVE_TIME.json')['seconds']
    (out/'YIELD_REQUEST.json').unlink()
    result=card.execute(out,inputs,card.CONFIG)
    assert first.read_bytes()==old and read(out/'ACTIVE_TIME.json')['seconds']>=prior
    assert read(out/'FIRST_TENTH.json')['variants_sampled']==['pair','pair2']
    assert result['primary_rows']==78602 and result['primary_writers']==41
    assert all(v['exact_history_support_complete'] and not v['scientific_scoring_admitted'] and v['retained_primary_rows']==78602 for v in result['variants'].values())
    assert not result['scientific_result']
    code='import sys,json;from pathlib import Path;from runners.drive.cards.timing_d33_pair_intake import verify,CONFIG;assert verify(Path(sys.argv[1]),json.load(open(sys.argv[2])),CONFIG)["verified"];print("verified")'
    child=subprocess.run([sys.executable,'-c',code,str(out),str(tmp_path/'source/INPUTS.json')],capture_output=True,text=True,timeout=90,
        env={**os.environ,'OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','PYTHONHASHSEED':'917'})
    assert child.returncode==0,child.stdout+child.stderr
    write(tmp_path/'FIXTURE_RECEIPT.json',dict(seconds=time.monotonic()-start,fresh_exit=child.returncode,rows=78602,writers=41,
        output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())))
    # Rebinding a forged saved target cannot evade fresh source matching.
    from runners.drive.cards.timing_stats import bind
    binding=read(out/'TIMING_BINDINGS.json');path=out/'sessions/pair/w00_s4.json';value=read(path)
    value['proof']['donor_tokens']+=1;path.unlink();write(path,value)
    (out/'TIMING_BINDINGS.json').unlink();bind(out,inputs,card.CONFIG,list(binding['outputs']))
    with pytest.raises(ValueError,match='source-based'):card.verify(out,inputs,card.CONFIG)
