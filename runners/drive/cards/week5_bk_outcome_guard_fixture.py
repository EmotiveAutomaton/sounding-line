"""Actual v2 full fixture plus source-derived single-writer gate refusal."""
import copy
from pathlib import Path
from . import week5_bk_outcome_fixture as full
from . import week5_bk_outcome_features_v2 as features
from . import week5_bk_outcome_analysis_v2 as analysis
from .timing_census import read
from .timing_p6 import write_equal,gzread
from tests.test_week3_frames_analysis import fixture_data


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed-only interval guard fixture')
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    prior_analysis,prior_features=full.analysis,full.features
    # Existing complete fixture injects the synthetic class for its pause test;
    # the v2 runner resolves that class through the immutable v1 namespace.
    features.ConstructedEncoder=features.original.ConstructedEncoder
    analysis.pooled=analysis.original.pooled
    full.analysis,full.features=analysis,features
    try:(full.verify if verifying else full.execute)(root/'full',{}, {})
    finally:full.analysis,full.features=prior_analysis,prior_features
    value=fixture_data();value['data']['pairs']=[p for p in value['data']['pairs'] if p['event']['writer']=='a'];value['data']['summary']['support']=False
    source=root/'ONE_WRITER.json';write_equal(source,value);cfg=dict(card='FR1',mode='constructed',max_wall_seconds=1200)
    (features.verify if verifying else features.execute)(root/'features',dict(fixture=str(source)),cfg)
    style=gzread(root/'features/STYLE.json.gz')
    if style['calibration_pass'] or any(v['ci95'] is not None for v in style['calibration'].values()) or read(root/'features/SUMMARY.json')['encoded']:
        raise ValueError('One-writer calibration licensed embedding')
    payload=dict(data=gzread(root/'features/EVENTS.json.gz'),vectors=gzread(root/'features/VECTORS.json.gz'),style=style)
    source=root/'ONE_WRITER_ANALYSIS.json';write_equal(source,payload)
    (analysis.verify if verifying else analysis.execute)(root/'analysis',dict(fixture=str(source)),dict(card='FR1',mode='constructed'))
    result=read(root/'analysis/RESULT.json')
    if result['calibration_pass'] or result['fallback']['by_kind']['frustration']['style']['ci95'] is not None:raise ValueError('One writer received inference')
    receipt=dict(fixture_only=True,all_original_full_count_worlds_replayed=True,single_writer_calibration_unidentified=True,
                 single_writer_no_embedding_expense=True,single_writer_points_retained_without_intervals=True)
    if verifying:
        if read(root/'FIXTURE.json')!=receipt:raise ValueError('Guard fixture differs')
    else:write_equal(root/'FIXTURE.json',receipt)
    return dict(verified=True) if verifying else dict(status='complete',fixture_only=True)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
if __name__=='__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output,{},{})))
