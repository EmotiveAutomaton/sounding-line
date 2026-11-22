import csv
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pytest
from runners.drive.sealed import week7_sld3_build as builder

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.agent-state/drive-20261115'


@pytest.fixture(scope='module')
def study(tmp_path_factory):
    folder=tmp_path_factory.mktemp('sld3-code')
    for name,code in builder.modules().items():
        (folder/(name+'.py')).write_text(code,'utf8')
    reader=WORK/'lattice-20261119/fixture-reader-native'
    with patch.object(sys,'path',[str(folder),str(reader),*sys.path]):
        import week7_sld3 as study_module
        yield study_module


def test_mounted_constructed_and_gate(study,tmp_path):
    mount=WORK/'lattice-20261120/spark-family-constructed-v2'
    manifest=json.loads((mount/'MANIFEST.json').read_text('utf8'))
    assert manifest['constructed_only'] and manifest['private_source_reads']==0
    out=tmp_path/'out'
    out.mkdir()
    study.run(mount,out,manifest['sources'],draws=4)
    gate=WORK/'lattice-20261119/intake/unpacked/PREFLIGHT_2026-11-19/spark/sealed_gate.py'
    passed=subprocess.run([sys.executable,'-B',str(gate),str(out)],capture_output=True)
    assert passed.returncode==0
    with (out/'table_status.csv').open() as f:
        status=list(csv.DictReader(f))
    assert len(status)==109 and all(int(r['n'])==576 for r in status)
    with (out/'trait.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert rows and all(11<=int(r['n'])<=576 for r in rows)


def test_planted_daily_trait_and_duplicate_day(study):
    fields=study.contract.fields('M2')
    data={'survey':[],'diary':[]}
    for p in range(1,121):
        trait=1+(p%3)
        data['survey'].append({'M2ID':p,'M2FAMNUM':p,fields['traits']['neuroticism']:trait})
        for day in range(1,9):
            event=int(day in (1,5))
            row={'M2ID':p,fields['study_day']:day}
            row.update({s['occurrence']:1 if event else 2 for s in fields['stressors']})
            row.update({k:1+event*trait for k in fields['negative']})
            data['diary'].append(row)
    out=study.estimates(data,draws=8)
    rows=out['trait']
    assert rows[0]['n']==120
    assert abs(rows[0]['estimate']-np.sqrt(2/3)/2)<1e-8
    assert rows[-1]['estimate']==pytest.approx(0)
    data['diary'].append(data['diary'][0])
    with pytest.raises(ValueError,match='duplicate diary day'):
        study.estimates(data,draws=2)
