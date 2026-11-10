"""Complete native WC2/FR1 handlers at their original full uncertainty counts."""
import copy
from pathlib import Path
from types import FunctionType
import numpy as np

from . import week5_bk_outcome_features as features
from . import week5_bk_outcome_analysis as analysis
from . import week3_failed_means as wc
from . import week3_frames_stats as fr
from . import week3_frames_analysis_cluster as cluster
from .timing_census import read
from .timing_p6 import write_equal,gzread
from tests.test_week3_failed_means import payload
from tests.test_week3_frames_analysis import fixture_data,known_rows


def wc_full(kind):
    original=payload(kind);events=[];vectors=original['vectors'];template=original['data']['events']
    for writer in range(30):
        for session in range(6):
            e=copy.deepcopy(template[(writer%8)*4+session%4]);e.update(id=f'{writer}-{session}',writer=str(writer),session=f'{writer}-{session}',timestamp=session)
            e['prompt']='p'+str(session);e['context'][0]['prompt']=e['prompt'];e['context'][0]['writer']='external'
            # The signed fixture has known varying persistence across whole
            # prompt halves so the complete reliability bank is exercised.
            if kind=='new_means' and session<writer%3:
                e['window']['text']=e['context'][0]['text']
            kept=copy.deepcopy(e);kept.update(id=e['id']+'-kept',kind='kept')
            e['kept_reference']=dict(id=kept['id']);events.extend([e,kept])
    return dict(data=dict(events=events),vectors=vectors)


def fr_value(effect,common=False):
    value=known_rows(effect)
    if common:
        for row in value['rows']:row['delta_by_profile']=[float(effect)]*len(value['profile_writers'])
    value['source_summary'].update(support=True)
    rng=np.random.default_rng(20261026)
    calibration={key:fr.interval(list(fr.grouped(value['rows'],key).values()),rng,2000) for key in ('calibration20','calibration40_increment')}
    return dict(data=dict(summary=value['source_summary'],pairs=[]),vectors={},
                style=dict(features=value,calibration=calibration,calibration_pass=True))


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('No human input in outcome fixture')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);call=analysis.verify if verifying else analysis.execute
    expected={'new_means':'same end, new means','wording':'lingering taste','null':'no direction','topic':'no direction','reverse':'moves away'}
    for kind,route in expected.items():
        value=wc_full(kind);source=root/(kind+'.json');write_equal(source,value);dest=root/('WC2-'+kind)
        call(dest,dict(fixture=str(source)),dict(card='WC2',mode='constructed'))
        result=read(dest/'RESULT.json');original,_=wc.analyze(value['data'],value['vectors'],wc.CONFIG)
        if result['route']!=route or result['events']!=180 or result['writers']!=30 or any(result[k]!=v for k,v in original.items() if k!='scientific_admission'):
            raise ValueError('Frozen full WC2 handler/known route differs')
        if kind=='new_means' and len(result['reliability']['null'])!=1000:raise ValueError('Complete reliability bank absent')
    for name,effect,common,wanted in [('personal',1,False,'positive'),('reverse',-1,False,'negative'),('null',0,False,'not_detected_sensitivity_unquantified'),('common',1,True,None)]:
        value=fr_value(effect,common);source=root/('fr1-'+name+'.json');write_equal(source,value);dest=root/('FR1-'+name)
        call(dest,dict(fixture=str(source)),dict(card='FR1',mode='constructed'))
        result=read(dest/'RESULT.json')
        fn=FunctionType(fr.analyze.__code__,dict(fr.__dict__,contrast=cluster.contrast));original=fn(value['style']['features'],20261026,2000,200)
        if any(result[k]!=v for k,v in original.items() if k!='scientific_admission'):raise ValueError('Full corrected FR1 reference changed')
        if wanted is not None and result['state']!=wanted:raise ValueError('FR1 known signed route failed')
        if common and (result['primary']['own_minus_fake']['ci95']!=[0,0] or result['state']=='positive'):raise ValueError('Common effect became personal')
    # Exercise actual source-derived style features and all embedding consumers.
    value=fixture_data();value['data']['summary']['support']=False
    source=root/'raw-derived-style.json';write_equal(source,value);dest=root/'FR1-features';cfg=dict(card='FR1',mode='constructed',max_wall_seconds=1200)
    featurecall=features.verify if verifying else features.execute
    if not verifying:
        dest.mkdir(parents=True,exist_ok=True);write_equal(dest/'YIELD_REQUEST.json',dict(reason='before load'))
        if features.execute(dest,dict(fixture=str(source)),cfg)['status']!='yielded':raise ValueError('Feature preload yield missing')
        (dest/'YIELD_REQUEST.json').unlink()
        previous=features.ConstructedEncoder.vector;count=0
        def pause(encoder,text):
            nonlocal count
            value=previous(encoder,text);count+=1
            if count==1:write_equal(dest/'YIELD_REQUEST.json',dict(reason='sealed first embedding'))
            return value
        features.ConstructedEncoder.vector=pause
        try:
            if features.execute(dest,dict(fixture=str(source)),cfg)['status']!='yielded':raise ValueError('Feature sealed yield missing')
        finally:features.ConstructedEncoder.vector=previous
        (dest/'YIELD_REQUEST.json').unlink()
    featurecall(dest,dict(fixture=str(source)),cfg)
    if not verifying:
        seal=next((dest/'texts').glob('*.seal.json'));prior=seal.read_bytes();seal.write_text('{}',encoding='utf8')
        try:
            try:features.execute(dest,dict(fixture=str(source)),cfg)
            except ValueError as error:
                if 'seal differs' not in str(error):raise
            else:raise ValueError('Corrupt feature checkpoint was reused')
        finally:seal.write_bytes(prior)
    downstream=dict(data=gzread(dest/'EVENTS.json.gz'),vectors=gzread(dest/'VECTORS.json.gz'),style=gzread(dest/'STYLE.json.gz'))
    source=root/'thin-fr1.json';write_equal(source,downstream)
    call(root/'FR1-thin',dict(fixture=str(source)),dict(card='FR1',mode='constructed'))
    thin=read(root/'FR1-thin/RESULT.json')
    if thin['state']!='unsupported' or thin['fallback']['state']!='below floor, descriptive' or 'embedding' not in thin['fallback']:
        raise ValueError('Below-floor FR1 did not preserve primary and descriptive secondary')
    small=payload();source=root/'thin-wc2.json';write_equal(source,small)
    call(root/'WC2-thin',dict(fixture=str(source)),dict(card='WC2',mode='constructed'))
    thin=read(root/'WC2-thin/RESULT.json')
    if thin['state']!='unsupported' or thin['fallback']['pooled']['embedding']['mean']!=1:raise ValueError('Below-floor WC2 fallback failed')
    featurecall(root/'WC2-features',dict(fixture=str(source)),dict(card='WC2',mode='constructed',max_wall_seconds=1200))
    wc_small=gzread(root/'WC2-features/EVENTS.json.gz')
    if len(wc_small['events'])!=len(small['data']['events']):raise ValueError('WC2 feature event roster changed')
    one=analysis.pooled([dict(writer='one',x=1)],'x')
    if one['ci95'] is not None or one['mean']!=1:raise ValueError('Single writer received fake population uncertainty')
    # Independent unequal-cluster arithmetic: pooling differs from equal writers.
    if analysis.pooled([dict(writer='a',x=0),dict(writer='b',x=1),dict(writer='b',x=1)],'x')['mean']!=2/3:
        raise ValueError('Pooled fallback estimator changed')
    receipt=dict(fixture_only=True,full_original_primary_handlers=True,primary_writer_draws=2000,
                 wc2_reliability_draws=1000,wc2_reference_draws=200,fr1_profile_and_writer_arm_draws=200,
                 signed_and_exact_null_and_topic_worlds=True,source_derived_style_and_embeddings=True,
                 original_supported_statistics_exact=True,thin_primary_stays_unsupported=True,
                 pooled_fallback_cluster_draws=200,single_cluster_has_no_interval=True,preload_and_text_yield_resume=True,
                 both_feature_handlers=True,feature_seal_tamper_refused=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Outcome fixture receipt differs')
    else:write_equal(root/'FIXTURE.json',receipt)
    return dict(verified=True,full_native_primary_replay=True) if verifying else dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)

if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
