import copy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import week3_frames_stats as stats
from runners.drive.cards import week3_frames_analysis as card
from runners.drive.cards import week3_frames_inputs as source
from runners.drive.cards.timing_census import write
from tests.test_week3_frames_inputs import fixture


def fixture_data():
    data=source.assemble([source.prepare_session(**s) for s in fixture()])
    # Constructed pipeline fixture explicitly exercises features/embedding paths;
    # it cannot authorize corpus support or scientific admission.
    data['summary']['support']=True
    return dict(data=data,dictionary=dict(words=['and','the','but'],punctuation=['.']))


def known_rows(effect=1):
    names=[str(i) for i in range(30)];rows=[]
    for i,name in enumerate(names):
        for j in range(4):
            delta=np.zeros(30);delta[i]=effect
            rows.append(dict(writer=name,kind='frustration',id=name+':'+str(j),delta_by_profile=delta.tolist(),
                             calibration20=.2,calibration40_increment=.2,pause_delta=0))
    return dict(profile_writers=names,rows=rows,source_summary=dict(support=True,constructed=True))


def test_fixed_style_rates_and_heldout_plants():
    value=fixture_data();features=stats.features(value['data'],value['dictionary'])
    for r in features['rows']:
        assert r['calibration20']>0 and r['calibration40_increment']>0
        assert r['delta_by_profile'][features['profile_writers'].index(r['writer'])]>0
    assert np.array_equal(stats.style(['and','the'],value['dictionary']),stats.style(['and','the']*10,value['dictionary']))
    with pytest.raises(ValueError,match='50neutral'):stats.plant(['and']*49,['the']*100,10)


def test_known_person_effect_null_and_reversal():
    positive=stats.analyze(known_rows(1),bootstraps=200,permutations=200)
    null=stats.analyze(known_rows(0),bootstraps=200,permutations=200)
    reverse=stats.analyze(known_rows(-1),bootstraps=200,permutations=200)
    assert positive['state']=='positive'
    assert positive['primary']['own_minus_fake']['ci95'][0]>0
    assert null['state']=='not_detected_sensitivity_unquantified'
    assert reverse['state']=='negative'


def test_common_arm_effect_has_no_person_advantage():
    value=known_rows(1)
    for r in value['rows']:r['delta_by_profile']=[1]*30
    result=stats.analyze(value,bootstraps=100,permutations=200)
    assert result['primary']['primary']['mean']==1
    assert result['primary']['own_minus_fake']['ci95']==[0,0]
    assert result['state']!='positive'


def test_failed_calibration_stops_primary_references():
    value=known_rows(1)
    for r in value['rows']:r['calibration40_increment']=0
    result=stats.analyze(value,bootstraps=100,permutations=200)
    assert result['state']=='invalid_calibration'
    assert result['primary']['state']=='not_run_gate_closed'


def test_complete_constructed_handler_fresh_process_and_changed_features(tmp_path):
    path=tmp_path/'fixture.json';write(path,fixture_data());inputs={'fixture':str(path)};out=tmp_path/'out'
    result=card.execute(out,inputs,card.CONSTRUCTED)
    assert result['constructed_only'] and not result['scientific_admission']
    assert result['secondary_embedding']['frustration']['writers']==2
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=card.CONSTRUCTED))
    code="import json,sys;from runners.drive.cards.week3_frames_analysis import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):card.verify(out,inputs,card.CONSTRUCTED)


def test_no_model_or_partial_admission_when_unsupported(tmp_path):
    value=fixture_data();value['data']['summary']['support']=False
    path=tmp_path/'fixture.json';write(path,value)
    result=card.execute(tmp_path/'out',{'fixture':str(path)},card.CONSTRUCTED)
    assert result['state']=='unsupported' and result['secondary_embedding']['state']=='unsupported_primary_source'
    with pytest.raises(ValueError,match='authenticated'):card.execute(tmp_path/'bad',{'fixture':str(path)},card.CONFIG)
