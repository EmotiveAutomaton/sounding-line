import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_pieces_effects_pilot as pilot
from runners.drive.cards.timing_census import read, write
from tests.test_week3_pieces_effects import effect_inputs


def fixture(root):
    effect = effect_inputs(root)
    prep = read(Path(effect['coverage_complete']).parent/'PLAN.json')['inputs']
    return dict(prep, **{k: effect[k] for k in ['source_inputs', 'content_model', 'content_complete']})


def config():
    return dict(mode='constructed', seed=20261026, sample_denominator=1, minimum_occurrences=1,
                minimum_writers=1, permutation_draws=3, bootstrap_draws=20, safety_multiplier=3)


def test_full_probe_fresh_serialized_replay_and_result_mutation(tmp_path):
    inputs=fixture(tmp_path/'fixture'); output=tmp_path/'output'
    result=pilot.execute(output,inputs,config())
    assert not result['scientific_admission']
    assert result['work']['sessions']==result['work']['sample_sessions']==8
    assert result['work']['sample_occurrences']>0
    assert result['timing']['projected_missing_work_cpu_seconds']>0
    assert pilot.verify(output,inputs,config())['full_probe_replay']
    manifest=tmp_path/'verify.json';write(manifest,dict(output=str(output),inputs=inputs,config=config()))
    code="import json,sys;from runners.drive.cards.week3_pieces_effects_pilot import verify;x=json.load(open(sys.argv[1]));assert verify(**x)['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60,
        env=dict(os.environ,PYTHONHASHSEED='139',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
    result['work']['sample_occurrences']+=1
    (output/'EFFECTS_PILOT_RESULT.json').write_text(json.dumps(result),encoding='utf8')
    with pytest.raises(ValueError,match='full work replay differs'):
        pilot.verify(output,inputs,config())


def test_selection_ignores_order_and_outcomes():
    rows=[dict(session=str(i),symbols=['a']*i) for i in range(23)]
    chosen=pilot.selection(rows,10)
    assert len(chosen)==3 and chosen==pilot.selection(rows[::-1],10)
    for row in rows: row['symbols']=['changed']
    assert chosen==pilot.selection(rows,10)


def test_source_change_and_incomplete_work_refused(tmp_path):
    inputs=fixture(tmp_path/'fixture')
    source=Path(inputs['source_inputs'])
    values=read(source);values['raw_roster']=str(tmp_path/'wrong.json');write(tmp_path/'wrong.json',[])
    source.write_text(json.dumps(values),encoding='utf8')
    with pytest.raises(ValueError,match='source bundle differs'):
        pilot.execute(tmp_path/'output',inputs,config())


def test_corpus_counts_and_yield_are_not_scientific_admission(tmp_path):
    with pytest.raises(ValueError,match='corpus first tenth'):
        pilot.validate(dict(config(),mode='corpus'))
    inputs=fixture(tmp_path/'fixture');output=tmp_path/'output'
    write(output/'YIELD_REQUEST.json',dict(reason='constructed resource pause'))
    result=pilot.execute(output,inputs,config())
    assert result['status']=='yielded' and not result['scientific_admission']
    assert not (output/'EFFECTS_PILOT_RESULT.json').exists()
