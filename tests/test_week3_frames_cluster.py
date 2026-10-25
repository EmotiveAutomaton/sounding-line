import copy
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import week3_frames_analysis_cluster as w
from runners.drive.cards import week3_frames_stats as original
from runners.drive.cards.timing_census import write
from tests.test_week3_frames_analysis import known_rows,fixture_data


def test_only_arm_reference_changes_all_primary_fake_banks_identical():
    value=known_rows(1)
    args=(value['rows'],value['profile_writers'])
    before=original.contrast(*args,np.random.default_rng(20261026),200,200)
    after=w.contrast(*args,np.random.default_rng(20261026),200,200)
    for key in ('primary','own_minus_fake','fake_primary_mean'):
        assert before[key]==after[key]
    assert after['arm_label_reference']['sd']>before['arm_label_reference']['sd']


def test_one_writer_repeated_controls_never_become_independent_labels():
    rows=[dict(writer='a',delta_by_profile=[1,0]) for _ in range(100)]
    result=w.contrast(rows,['a','b'],np.random.default_rng(20261026),100,200)
    assert result['arm_label_reference']['sd']>.9
    assert result['arm_label_reference']['one_sided_p']>.3


def test_context_restoration_and_complete_native_fixture(tmp_path):
    previous=original.contrast
    with pytest.raises(ValueError):w.execute(tmp_path/'invalid',{},w.CONFIG)
    assert original.contrast is previous
    source=tmp_path/'fixture.json';write(source,fixture_data());inputs={'fixture':str(source)};out=tmp_path/'out'
    result=w.execute(out,inputs,w.CONSTRUCTED)
    assert result['primary']['variant'].startswith('FR1.h1')
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=w.CONSTRUCTED))
    code="import json,sys;from runners.drive.cards.week3_frames_analysis_cluster import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
