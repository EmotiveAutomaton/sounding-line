"""Verify the CANDOR dictionaries and qualify the reciprocal trait and standing tables."""
import csv
from pathlib import Path
from runpy import run_path
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import week8_prepare_lkg1 as prior,week8_study_package as package
from runners.stage14.common import filehash,freeze,read
from runners.drive.sealed import week8_package as bundle
from runners.drive.sealed.week6_sc1_counts_v1 import PINS

UNIT='LKG2-speaker-traits-standing-DN'
CAP=20000
STUDY=bundle.LIB/'week8_lkg2.py'
TRAITS=('extraversion','agreeable','conscientious','neurotic','open')
EXTRA=[p+t for p in ('my_','your_') for t in TRAITS]+['you_think_my_status','i_think_your_status']


def main():
    import openpyxl
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    archive=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    docs=archive/'private/candor/docs/data_dictionary/survey.csv'
    workbook=archive/'_handoffs/repo-requests/DC-20261125-CANDOR/CANDOR_LEGACY_DICTIONARY.xlsx'
    if filehash(docs)!='7feaf9a5a3b4a12d091036ae30d7ba78c66f071f1fbbce81f038f2d51b3d9314' or filehash(workbook)!='2c7d1fbb1ab51406aac702d4bf76b83e010574519a9ca654f7dcce87c2cad2d1':
        raise ValueError('Survey documentation changed')
    with docs.open(encoding='utf-8-sig',newline='') as f:
        document={r['column']:r for r in csv.DictReader(f)}
    book=openpyxl.load_workbook(workbook,read_only=True,data_only=True)
    try:
        labels={r[0]:r[6] for r in book['survey.csv'].values if r[0] in EXTRA}
    finally:
        book.close()
    for k in EXTRA:
        if k not in document or not document[k]['question_text'] or k not in labels:
            raise ValueError('Provider metadata did not bind the registered fields')
        if k in EXTRA[-2:]:
            if labels[k]!='10, 9, 8, 7, 6, 5, 4, 3, 2, 1':
                raise ValueError('Standing ladder differs')
        elif not labels[k].startswith('1 - Disagree strongly') or not labels[k].endswith('5 - Agree strongly'):
            raise ValueError('Trait scale differs')
    real_known,pins=prior.previous()
    census=prior.OLD/'lattice-20261120/spark-sc1-counts-v1/gated-return/survey_columns.csv'
    with census.open(newline='') as f:
        census_counts={r['column']:int(r['n']) for r in csv.DictReader(f) if r['column'] in EXTRA}
    known_input=prior.gear.ROOT/'LKG1-liking-gap'
    if not (known_input/'FAILED.json').is_file() or (known_input/'gated-return').exists():
        raise ValueError('Reconcile the earlier liking return before a new release')
    scratch=prior.STATE/'fixtures'/(UNIT+'-'+uuid4().hex[:10])
    mount=scratch/'data'
    (mount/'surveys').mkdir(parents=True)
    df,example=run_path(str(prior.TEST))['sample']()
    for col in EXTRA[:10]:
        author=df.user_id if col.startswith('my_') else df.partner_id
        df[col]=author.str.slice(1).astype(int)%5+1.
    df['i_like_you']=3
    df['you_like_me']=df.my_extraversion+1
    df['i_think_your_status']=5.
    df['you_think_my_status']=df.my_extraversion+3.
    spec=[STUDY,*prior.MODULES,bundle.LIB/'r48_forms.py']
    def test(name):
        file=mount/'surveys/survey.parquet'
        pq.write_table(pa.Table.from_pandas(df,preserve_index=False),file)
        config=dict(pin=['surveys/survey.parquet',file.stat().st_size,filehash(file)],previous=example,
                    trait_counts={k:160 for k in EXTRA},draws=60)
        prog=scratch/(name+'.py')
        prog.write_bytes(bundle.package(STUDY,spec,config,CAP,fixture=True))
        out=scratch/name;out.mkdir()
        subprocess.run([sys.executable,'-B',str(prog),str(mount),str(out)],check=True)
        package.gate(out)
        with (out/'comparisons.csv').open(newline='') as f:
            return {int(r['measure']):r for r in csv.DictReader(f)}
    rows=test('planted')
    if set(rows)!=set(range(1,14)) or any(int(r['n'])!=160 for r in rows.values()):
        raise ValueError('Incorrect contributing people or measures')
    if not all(abs(float(rows[k]['estimate'])-v)<1e-8 for k,v in [(1,1),(6,1),(4,-1),(9,-1),(12,1),(13,1)]):
        raise ValueError('Directed rating, scale orientation or standing repeat failed')
    df.loc[0,'my_neurotic']=19
    other=test('single-field-refusal')
    if set(other)!=set(rows)-{4}:
        raise ValueError('Unbound trait incorrectly affected another component')
    proof=scratch/'REHEARSAL.json'
    freeze(proof,dict(constructed=True,people=160,forms=['fine','coarse','summary'],distinct_people_checked=True,checks=['two-way keys','sender and receiver roles','stability orientation','standing repeat',
            'single-field refusal','historical release membership','independent source replay','installed gate'],output=filehash(scratch/'planted/comparisons.csv')))
    plan=dict(pin=PINS['survey'],previous=real_known,trait_counts=census_counts,draws=2000)
    source=bundle.package(STUDY,spec,plan,CAP)
    pending=[*pins,census,known_input/'FAILED.json',docs,workbook,prior.TEST,Path(prior.__file__),Path(__file__),
             ROOT/'docs/design/stage-15/week8/LKG2.md',*spec,Path(bundle.__file__),bundle.RELEASE,bundle.SUPPORT]
    print(UNIT,package.admit(UNIT,'LKG2','candor',CAP,['comparisons.csv'],source,proof,pending))


if __name__=='__main__':
    main()
