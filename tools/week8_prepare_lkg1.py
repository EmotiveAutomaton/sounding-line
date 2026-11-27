"""Validate provider documentation, prior sealed supports and a synthetic CANDOR survey."""
import csv
import os
from pathlib import Path
from runpy import run_path
import subprocess
import sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.week8_sealed import GATE,HOST,OLD,STATE
from runners.drive.cards import week7_gear,week8_gear as gear
from runners.drive.sealed import week8_package as bundle
from runners.drive.sealed.week6_sc1_counts_v1 import PINS
from runners.stage14.common import filehash,freeze,read

UNIT='LKG1-liking-gap'
STUDY=bundle.LIB/'week8_lkg1.py'
MODULES=[STUDY,bundle.LIB/'week6_sc1_counts_v1.py']
TEST=ROOT/'tests/test_week8_lkg1.py'
CAP=3600


def previous():
    base=OLD/'lattice-20261120'
    rowfiles={}
    pins=[]
    for key,d,name in [('survey',base/'spark-sc1-counts-v1','survey_columns.csv'),
                       ('sc2',base/'spark-sc2-matched-v2','support.csv'),
                       ('cad1',week7_gear.ROOT/'CAD1-primary-20261125','support.csv'),
                       ('lgh2',week7_gear.ROOT/'LGH2-survey-20261125','support.csv')]:
        term=d/'COMPLETE.json'
        file=d/'gated-return'/name
        refs=read(term)
        digests=refs.get('aggregate_sha256',refs.get('aggregates'))
        if not refs['verified'] or digests[name]!=filehash(file):
            raise ValueError('Historical gated return differs')
        with file.open(newline='') as stream:
            rowfiles[key]=list(csv.DictReader(stream))
        pins.extend([term,file])
    cols=('user_id','partner_id','conversation_id','date','i_like_you','you_like_me','technical_quality',
          'arousal','how_enjoyable','laughter','affect','pre_affect','you_are_funny','i_think_your_status')
    obs={row['column']:int(row['n']) for row in rowfiles['survey'] if row['column'] in cols}
    if set(obs)!=set(cols):
        raise ValueError('Historical support lacks a survey column')
    counts={int(row['kind']):int(row['n']) for row in rowfiles['cad1'] if row['reading']=='1'}
    return dict(survey=obs,cad1=[counts[1],counts[2]],lgh2=int(rowfiles['lgh2'][0]['n']),sc2=int(rowfiles['sc2'][0]['n'])),pins


def main():
    import openpyxl
    import pyarrow as pa
    import pyarrow.parquet as pq
    archive=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    docs=archive/'private/candor/docs/data_dictionary/survey.csv'
    workbook=archive/'_handoffs/repo-requests/DC-20261125-CANDOR/CANDOR_LEGACY_DICTIONARY.xlsx'
    if filehash(docs)!='7feaf9a5a3b4a12d091036ae30d7ba78c66f071f1fbbce81f038f2d51b3d9314' or filehash(workbook)!='2c7d1fbb1ab51406aac702d4bf76b83e010574519a9ca654f7dcce87c2cad2d1':
        raise ValueError('Survey documentation differs')
    book=openpyxl.load_workbook(workbook,read_only=True,data_only=True)
    try:
        labels=[r[6] for r in book['survey.csv'].values if r[0] in ('i_like_you','you_like_me')]
        if labels!=['1 - Not very much, 2, 3, 4, 5, 6, 7 - Very much']*2:
            raise ValueError('Historical response key differs')
    finally:
        book.close()
    known,old_pins=previous()
    if read(HOST)['installed_gate_sha256']!=filehash(GATE):
        raise ValueError('Rehearsal gate differs')
    panel,example_known=run_path(str(TEST))['sample']()
    testroot=STATE/'fixtures'/(UNIT+'-'+uuid4().hex[:12])
    data,out,refusal=[testroot/n for n in ('data','out','refusal')]
    for d in (data/'surveys',out,refusal):
        d.mkdir(parents=True)
    file=data/'surveys/survey.parquet'
    def program(df,name):
        pq.write_table(pa.Table.from_pandas(df,preserve_index=False),file)
        config=dict(pin=['surveys/survey.parquet',file.stat().st_size,filehash(file)],previous=example_known,draws=48)
        entry=testroot/name
        entry.write_bytes(bundle.package(STUDY,MODULES,config,CAP,fixture=True))
        return entry
    example=program(panel,'valid.py')
    subprocess.run([sys.executable,'-B',str(example),str(data),str(out)],check=True)
    if subprocess.check_output([sys.executable,'-I','-B',str(GATE),str(out)],text=True).strip()!='gate passed':
        raise ValueError('Synthetic return failed gate')
    with (out/'liking.csv').open() as stream:
        records={int(r['measure']):r for r in csv.DictReader(stream)}
    if set(records)!=set(range(1,10)) or float(records[1]['upper'])>=0 or float(records[3]['lower'])<=0 or not all(int(r['n'])==160 for r in records.values()):
        raise ValueError('Constructed replay failed')
    panel.loc[0,'you_like_me']=0
    bad=program(panel,'invalid.py')
    rc=subprocess.run([sys.executable,'-B',str(bad),str(data),str(refusal)]).returncode
    if rc!=24 or any(refusal.iterdir()):
        raise ValueError('Unknown response did not refuse')
    evidence=testroot/'REHEARSAL.json'
    freeze(evidence,dict(all_data='constructed',entry=filehash(example),domain_refusal=rc,outputs={f.name:filehash(f) for f in out.iterdir()}))
    real=STATE/'sealed'/UNIT/'run.py'
    real.parent.mkdir(parents=True,exist_ok=True)
    payload=bundle.package(STUDY,MODULES,dict(pin=PINS['survey'],previous=known,draws=2000),CAP)
    if real.exists() and real.read_bytes()!=payload:
        raise ValueError('Existing reviewed entry differs')
    if not real.exists():real.write_bytes(payload)
    paths=[*old_pins,docs,workbook,gear.AUTHORITY,ROOT/'docs/design/stage-15/week8/LKG1.md',TEST,Path(__file__).resolve(),
           *MODULES,bundle.SUPPORT,bundle.RELEASE,Path(bundle.__file__),ROOT/'tools/week8_sealed.py',
           ROOT/'tools/week8_spark.ps1',Path(gear.__file__),GATE,HOST,evidence,real]
    freeze(STATE/'reviews'/(UNIT+'.json'),dict(unit=UNIT,card='LKG1',source='candor',tables=['liking.csv','support.csv'],
        cap=CAP,fixture_gate_passed=True,fixture_sha256=filehash(evidence),pins={str(p):filehash(p) for p in paths}))
    print('Rehearsed LKG1 original-layout entry and response-code refusal',filehash(real))


if __name__=='__main__':
    main()
