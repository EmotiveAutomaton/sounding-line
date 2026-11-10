"""Full WC4 raw-source, actual POS and statistical known-answer replay."""
from pathlib import Path
import copy,hashlib,json,time
import numpy as np
from . import week5_bk_wc4_source as source
from . import week5_bk_wc4_analysis as analysis
from . import week3_stability_inputs as old_source
from . import week3_stability_stats as old_stats
from . import week3_stability_tagger_smoke as smoke
from . import week4_shared_spans_h1 as r1
from .week3_insertion_provenance_h1 import fixture as insertion
from runners.stage9.coauthor import replay
from .timing_census import read
from .timing_p6 import gzread,write_equal
from tests.test_week3_stability import source_fixture,statistical_fixture


def run(output,inputs,config,verifying=False):
    if set(inputs)!={'model_manifest'} or config:raise ValueError('Only pinned tagger and constructed fixture inputs')
    root=Path(output);raw=[source_fixture()];first=copy.deepcopy(raw[0]);cases=[]
    for i,kind in enumerate(('plain','newline','rewrite','repeated','unmatched','edited','deleted')):
        events,timeline=insertion(kind);canonical=replay(events);timeline.setdefault('decisions',[])
        meta=dict(session='constructed-'+kind,writer='constructed-'+str(i),prompt='constructed-prompt',timestamp=i)
        wb1=dict(**meta,raw_events=len(events),final_document_sha256=hashlib.sha256(timeline['final_document'].encode()).hexdigest(),actions=[],intervals=[])
        row=dict(meta=meta,events=events,timeline=timeline,canonical=canonical,p6=dict(words=[]),wb1=wb1,annotation=dict(sentence_length=1.,lexical_density=1.,punctuation_rate=0.,artifact_words=1,artifact_sentences=1))
        raw.append(row);cases.append(kind)
    missing=copy.deepcopy(first);missing['meta']=dict(missing['meta'],session='constructed-missing');missing['wb1'].update(missing['meta']);missing['wb1']['actions']=[];missing['wb1']['intervals']=[];raw.append(missing)
    path=root/'SOURCE.json';write_equal(path,raw);cfg=dict(card='WC4-inputs',mode='constructed',max_wall_seconds=1200);out=root/'source'
    if not verifying:
        write_equal(out/'YIELD_REQUEST.json',dict(reason='constructed preload request'))
        if source.execute(out,dict(fixture=str(path)),cfg).get('status')!='yielded':raise ValueError('WC4 preload yield missing')
        (out/'YIELD_REQUEST.json').unlink()
    (source.verify if verifying else source.execute)(out,dict(fixture=str(path)),cfg)
    result=gzread(out/'EVENTS.json.gz');expected=old_source.prepare_session(**first)
    if any(result['sessions'][0][k]!=expected[k] for k in expected):raise ValueError('Original WC4 property arithmetic changed')
    if not {'words_per_burst','pause_before_sentence'}<=set(result['sessions'][-1]['missing']):raise ValueError('Missing opportunities became zero')
    for i,row in enumerate(raw[1:8],1):
        proof=r1.spans(row['events'],row['timeline'],row['canonical']);actual=result['sessions'][i]
        if actual['r1_audit']['physical_insertions']!=len(proof):raise ValueError('Physical insertions vanished')
        canonical=[s for s in proof if s['canonical']];total=sum(s['original_codepoints'] for s in canonical)
        expected_share=sum(s['retained_codepoints'] for s in canonical)/total if total else None
        if actual['properties']['retained_share']!=expected_share:raise ValueError('Canonical retained-share arithmetic differs')
    seal=out/'sessions/session-0000.json.seal.json';saved=seal.read_bytes();seal.write_text('{}\n')
    try:
        try:source.verify(out,dict(fixture=str(path)),cfg)
        except ValueError as error:
            if 'seal differs' not in str(error):raise
        else:raise ValueError('Changed source seal accepted')
    finally:seal.write_bytes(saved)
    (smoke.verify if verifying else smoke.execute)(root/'actual-tagger',inputs,smoke.CONFIG)
    for mode in ('positive','null','reversed','constant'):
        rows=statistical_fixture(mode);p=root/(mode+'.json');write_equal(p,rows)
        (analysis.verify if verifying else analysis.execute)(root/mode,dict(fixture=str(p)),dict(mode='constructed'))
        got=read(root/mode/'RESULT.json');old=old_stats.analyze(rows,analysis.CONFIG);old.update(constructed_only=True,scientific_admission=False)
        if any(got[k]!=v for k,v in old.items()):raise ValueError('Complete original WC4 statistic changed')
    rows=[r for r in statistical_fixture() if r['writer']=='w00'];p=root/'single.json';write_equal(p,rows)
    (analysis.verify if verifying else analysis.execute)(root/'single',dict(fixture=str(p)),dict(mode='constructed'))
    single=read(root/'single/RESULT.json')
    if single['state']!='unsupported_writers' or any(v['ci95'] is not None or v['variance'] is None for v in single['fallback']['properties'].values()):raise ValueError('Single-writer pooled variability guard failed')
    bank=np.random.default_rng(11).uniform(.1,2,(5,6,2,8));draws=np.array([[0,0,1,3,4,5],[5,4,3,2,1,0],[0,0,0,0,0,0]])
    actual,delta,invalid=old_stats.paired_bootstrap(bank,draws)
    if invalid!=1:raise ValueError('Undefined paired correlation was retained')
    for i,draw in enumerate(draws[:2]):
        values=[old_stats.agreement(arm[draw]).mean() for arm in bank]
        if not np.allclose([actual[i],delta[i]],[values[0],values[0]-np.mean(values[1:])],rtol=0,atol=1e-12):raise ValueError('Literal correlation rebuild differs')
    receipt=dict(fixture_only=True,actual_raw_source=True,all_original_properties_unchanged=True,r1_encodings=cases,
                 missing_opportunities_explicit=True,source_yield_and_tamper_refusal=True,actual_pinned_cpu_tagger=True,
                 full_references=1000,full_paired_bootstraps=2000,positive_null_reversed_flat=True,
                 literal_paired_correlation=True,single_writer_pooled_without_intervals=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Complete WC4 fixture changed')
        return dict(verified=True,full_source_tagger_statistic_replay=True)
    write_equal(root/'FIXTURE.json',receipt);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse
    from threadpoolctl import threadpool_limits
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('model_manifest');p.add_argument('--verify',action='store_true');a=p.parse_args();began=time.process_time()
    with threadpool_limits(limits=2):value=(verify if a.verify else execute)(a.output,dict(model_manifest=a.model_manifest),{})
    write_equal(Path(a.output)/('NATIVE_VERIFY_CPU.json' if a.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
