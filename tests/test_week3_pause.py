import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import week3_pause_model as model
from runners.drive.cards import week3_pause_inputs as source
from runners.drive.cards import week3_pause_instrument as instrument
from runners.drive.cards import week3_pause_pilot as pilot
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzwrite,gzread


def synthetic_rows(seed=3,positive=True):
    rng=np.random.default_rng(seed);rows=[]
    for genre in ('creative','argumentative'):
        for w in range(9):
            for p in range(4):
                intervals=[]
                for li,loc in enumerate(source.LOCATIONS):
                    for k in range(12):
                        slow=[.08,.2,.7 if positive else .2,.75,.5][li]
                        component=rng.choice(3,p=[1-slow-.05,slow,.05])
                        mechanical=int(rng.random()<(.9 if loc=='before_sentence' else .25))
                        logtime=[-1.9,.5,3.2][component]+rng.normal(0,.18)+.08*w+.03*p+.4*mechanical
                        ordinal=li*12+k
                        intervals.append(dict(ordinal=ordinal,previous_ordinal=ordinal-1,seconds=ordinal+rng.uniform(0,.9),
                            interval_seconds=math.exp(logtime),location=loc,next_upper_or_punctuation=bool(mechanical),
                            mechanical_training=loc in {'within_word','before_word'},target='deletion' if loc=='before_revision' else 'single_character_insert'))
                rows.append(dict(session=f'{genre}-{w}-{p}',writer=f'w{w}',prompt=f'{genre}-p{p}',timestamp=1000+p*100+w,
                                 genre=genre,session_order=p,intervals=intervals,source_exclusions={},separator_intervals=0))
    return rows


def completed(base):
    write(base/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
          outputs={p.relative_to(base).as_posix():filehash(p) for p in (base/'output').rglob('*') if p.is_file()}))


def instrument_inputs(root,rows=None):
    rows=synthetic_rows() if rows is None else rows
    base=root/'inputs';out=base/'output'
    original=root/'constructed-original.json';write(original,rows)
    gzwrite(out/'PP1_INTERVALS.json.gz',rows)
    write(out/'PP1_INPUT_RESULT.json',dict(sessions=len(rows)))
    write(out/'PP1_INPUT_BINDING.json',dict(original_source_bindings={str(original.resolve()):filehash(original)}))
    completed(base)
    return dict(input_complete=str(base/'COMPLETE.json'),intervals=str(out/'PP1_INTERVALS.json.gz'),
                input_result=str(out/'PP1_INPUT_RESULT.json'),input_binding=str(out/'PP1_INPUT_BINDING.json'))


def source_inputs(root):
    rows=synthetic_rows();base=root/'preparation';out=base/'output';roster=[];index=[]
    for i,r in enumerate(rows):
        meta={k:r[k] for k in ('session','writer','prompt','timestamp')};meta['domain']=r['genre'];roster.append(meta)
        p=out/f'sessions/{i}.json.gz';gzwrite(p,dict(r,genre=None,interval_exclusions={}))
        index.append(dict(session=r['session'],writer=r['writer'],file=f'sessions/{i}.json.gz',sha256=filehash(p)))
    raw=root/'raw-roster.json';write(raw,roster)
    write(out/'WB1_INPUT_INDEX.json',index);write(out/'WB1_INPUT_RESULT.json',dict(source_bindings={str(raw.resolve()):filehash(raw)}))
    completed(base)
    return dict(preparation_complete=str(base/'COMPLETE.json'),preparation_index=str(out/'WB1_INPUT_INDEX.json'),
                preparation_result=str(out/'WB1_INPUT_RESULT.json'),raw_roster=str(raw))


def small_config():return dict(mode='constructed',seed=20261026,bootstrap_draws=3,permutations=4)


def test_source_genre_join_and_all_session_census(tmp_path):
    inputs=source_inputs(tmp_path)
    config=dict(mode='constructed',expected_sessions=72,seed=20261026)
    result=source.execute(tmp_path/'output',inputs,config)
    assert result['sessions']==72 and set(result['genres'])=={'creative','argumentative'}
    assert source.verify(tmp_path/'output',inputs,config)['verified']
    p=Path(inputs['raw_roster']);p.write_text(p.read_text()+' ')
    with pytest.raises(ValueError,match='authenticated source'):source.verify(tmp_path/'output',inputs,config)


def test_known_boundary_signal_and_speed_invariance():
    rows=[r for r in synthetic_rows() if r['genre']=='creative']
    observed=model.model(rows)
    assert observed['contrasts']['sentence_minus_word']>.2
    assert all(x['slow_component_mean_seconds']>0 for x in observed['location_summary'].values())
    assert observed['mixture']['log_means']==sorted(observed['mixture']['log_means'])
    changed=copy.deepcopy(rows)
    for r in changed:
        multiplier=math.exp(int(r['writer'][1:])*.3)
        for x in r['intervals']:x['interval_seconds']*=multiplier
    assert np.allclose(model.arrays(rows)['log_interval'],model.arrays(changed)['log_interval'],atol=1e-12)
    a=model.profile_rows(rows,.4);b=model.profile_rows(changed,.4)
    assert np.allclose([r['features']['PP1.duration_hierarchy'] for r in a],[r['features']['PP1.duration_hierarchy'] for r in b],atol=1e-12)


def test_profiles_do_not_use_other_half_and_mechanical_known_answer():
    rows=[r for r in synthetic_rows() if r['genre']=='creative']
    before=model.profile_rows(rows,.4)
    changed=copy.deepcopy(rows)
    for r in changed:
        if r['session_order']%2:
            for x in r['intervals']:x['interval_seconds']*=50
    after=model.profile_rows(changed,.4)
    for a,b in zip(before,after):
        assert np.allclose(a['features']['PP1.duration_hierarchy'],b['features']['PP1.duration_hierarchy'],atol=1e-12)
    a=model.arrays(rows)
    rng=np.random.default_rng(87)
    a['log_interval']=.4*a['mechanical']+.15*(a['location']=='before_word')+.02*a['time']-.03*a['order']+rng.normal(0,.01,len(a['time']))
    estimate,_=model.mechanics(a)
    assert abs(estimate-.4)<.005


def test_no_boundary_signal_does_not_create_positive_gradient():
    rows=[r for r in synthetic_rows(seed=19,positive=False) if r['genre']=='creative']
    value=model.model(rows)
    assert abs(value['contrasts']['sentence_minus_word'])<.08


def test_mixture_and_mechanical_failure_are_not_null_results():
    with pytest.raises(ValueError,match='mixture lacks support'):model.mixture(np.ones(40))
    rows=[r for r in synthetic_rows() if r['genre']=='creative']
    for r in rows:
        for x in r['intervals']:x['next_upper_or_punctuation']=False
    with pytest.raises(ValueError,match='lacks both levels'):model.model(rows)
    with pytest.raises(ValueError,match='separately'):model.arrays(synthetic_rows())


def test_complete_instrument_fresh_native_replay_and_mutation(tmp_path):
    inputs=instrument_inputs(tmp_path);out=tmp_path/'main';config=small_config()
    result=instrument.execute(out,inputs,config)
    assert result['full_card_complete'] and not result['scientific_admission']
    assert set(result['genres'])=={'creative','argumentative'}
    assert all(r['gradient_pass'] for r in result['genres'].values())
    assert instrument.verify(out,inputs,config)['verified']
    p=tmp_path/'replay.json';write(p,dict(output=str(out),inputs=inputs,config=config))
    script="import json,sys;from pathlib import Path;from runners.drive.cards.week3_pause_instrument import verify;x=json.load(open(sys.argv[1]));assert verify(Path(x['output']),x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',script,str(p)],check=True,timeout=120,env=dict(os.environ,PYTHONHASHSEED='83'))
    saved=read(out/'PP1_RESULT.json');saved['genres']['creative']['gradient_pass']=False
    (out/'PP1_RESULT.json').write_text(json.dumps(saved),encoding='utf-8')
    with pytest.raises(ValueError,match='reconstruction differs'):instrument.verify(out,inputs,config)


def test_cost_pilot_counts_complete_work_without_scores(tmp_path):
    inputs=instrument_inputs(tmp_path);config=small_config()
    result=pilot.execute(tmp_path/'pilot',inputs,config)
    assert result['status']=='cost_probe_complete' and 'genres' not in result and not result['scientific_admission']
    assert result['timing']['projected_main_and_fresh_replay_cpu_seconds']>result['timing']['work_cpu_seconds']
    assert pilot.verify(tmp_path/'pilot',inputs,config)['verified']
    with pytest.raises(ValueError,match='full PP1 timing'):pilot.measure(tmp_path,inputs,dict(config,mode='corpus'))


def test_main_draw_counts_cannot_be_reduced_for_corpus():
    with pytest.raises(ValueError,match='full PP1 bootstrap'):instrument.configuration(dict(small_config(),mode='corpus'))


def test_fixture_cannot_masquerade_as_corpus(tmp_path):
    inputs=instrument_inputs(tmp_path)
    with pytest.raises(ValueError,match='full authenticated canonical'):instrument.execute(tmp_path/'bad',inputs,instrument.CONFIG)
    with pytest.raises(ValueError,match='full authenticated canonical'):pilot.execute(tmp_path/'bad-pilot',inputs,pilot.CONFIG)
