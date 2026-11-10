"""Native ICSI metadata variants: actual parser, preparation, complete refits."""
from pathlib import Path
import numpy as np
from . import week5_la_pipeline as pipeline
from . import week5_la as analysis
from .week5_la_fixture import fixture as parser_fixture
from .timing_p6 import gzip_equal,gzread,write_equal
from .timing_census import read


def constructed():
    parsed=next(r for r in parser_fixture()['sources'] if r['corpus']=='ICSI')
    info=next(iter(next(iter(parsed['metadata'].values()))['speakers'].values()))
    if info!=dict(english_variety='american',region='midwest'):raise ValueError('Actual ICSI parser metadata changed')
    rng=np.random.default_rng(20261107);metadata={};laughs=[];oracle={}
    for i in range(24):
        meeting=f'constructed-{i:02d}';people={};times={}
        for j in range(6):
            speaker=f'constructed-{j}'
            people[speaker]=dict(english_variety=['american','american','british','british','american','american'][j],
                                 region=['midwest','south','midwest','south','midwest','south'][j])
            if j==4:people[speaker]={}
            t=np.sort(rng.uniform(1,170,8+j+i%3)) if j!=5 else np.array([])
            if j==1:t=np.r_[t,np.asarray(times['constructed-0'][:3])+.25]
            if j==3:t=np.r_[t,np.asarray(times['constructed-2'][:3])+.25]
            times[speaker]=t.tolist()
            for at in t:laughs.append(dict(meeting=meeting,speaker=speaker,start=float(at),end=float(at+.1),label='vocal'))
        # A non-vocal annotation must not change the primary denominator.
        laughs.append(dict(meeting=meeting,speaker='constructed-0',start=190.,end=190.1,label='speech_comment'))
        metadata[meeting]=dict(duration=200.,corpus='ICSI',speakers=people)
        oracle[meeting]=(people,times)
    return metadata,laughs,oracle


def expected_rows(oracle,field):
    rows=[]
    for meeting,(people,times) in sorted(oracle.items()):
        ids=sorted(people)
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                if not people[a].get(field) or not people[b].get(field) or not times[a] or not times[b]:continue
                ja=sum(min(abs(v-t) for v in times[b])<=1. for t in times[a])/len(times[a])
                jb=sum(min(abs(v-t) for v in times[a])<=1. for t in times[b])/len(times[b])
                rows.append(dict(meeting=meeting,joined=(ja+jb)/2,same=int(people[a][field]==people[b][field]),rate_a=len(times[a])/200.,rate_b=len(times[b])/200.))
    return rows


def direct_point(rows):
    x=[];y=[]
    for m in sorted({r['meeting'] for r in rows}):
        rr=[r for r in rows if r['meeting']==m]
        a=np.array([[r['same'],r['rate_a'],r['rate_b']] for r in rr]);b=np.array([r['joined'] for r in rr])
        x.extend(a-a.mean(0));y.extend(b-b.mean())
    return float(np.linalg.lstsq(np.asarray(x),np.asarray(y),rcond=1e-10)[0][0])


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Metadata fixture accepts no human source')
    root=Path(output);source=root/'constructed-source';metadata,laughs,oracle=constructed()
    for name,value in [('ACTS.json.gz',[]),('LAUGHS.json.gz',laughs),('METADATA.json.gz',metadata)]:gzip_equal(source/'output'/name,value)
    old=pipeline.authenticate;pipeline.authenticate=lambda path:source
    try:
        for field in ('english_variety','region','native_language'):
            prepared=root/field/'prepared';fitted=root/field/'fitted'
            (pipeline.verify if verifying else pipeline.execute)(prepared,dict(source_root=str(source)),dict(card='LA2',corpus='ICSI',background=field))
            rows=gzread(prepared/'ROWS.json.gz');expected=expected_rows(oracle,field)
            if rows!=expected:raise ValueError('Metadata joining differs from independent symmetric-event oracle')
            (analysis.verify if verifying else analysis.execute)(fitted,dict(rows=str(prepared/'ROWS.json.gz')),dict(card='LA2',draws=2000))
            result=read(fitted/'RESULT.json');summary=read(prepared/'SUMMARY.json')
            if field=='native_language':
                if rows or result.get('state')!='unsupported':raise ValueError('Unrecorded native language was invented')
            else:
                if len(rows)!=144 or result['primary']['draws']!=2000 or abs(result['primary']['effect']-direct_point(rows))>1e-12:
                    raise ValueError('Complete metadata contrast does not match direct within-meeting fit')
                if summary['all_participant_pairs']!=360 or summary['unsupported_pairs']!=216:raise ValueError('Unknown/no-laugh exclusions lost')
    finally:pipeline.authenticate=old
    value=dict(fixture_only=True,actual_icsi_parser_metadata=True,actual_prepare_and_analysis_handlers=True,
               independent_symmetric_join_oracle=True,independent_within_meeting_point=True,
               variants=['english_variety','region'],meetings=24,draws_each=2000,unknown_and_zero_laugh_pairs_counted=True,
               native_language_absent_refused=True,no_fake_completion=True)
    if verifying:
        if read(root/'FIXTURE.json')!=value:raise ValueError('Metadata fixture receipt changed')
        return dict(verified=True,complete_icsi_metadata_variants=True)
    write_equal(root/'FIXTURE.json',value);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
