"""Native known-answer MD4 source and full consumer; no human estimates."""
from pathlib import Path
import argparse,csv,json,subprocess,sys
import numpy as np
from . import week5_md4_source as s
from . import week5_md4_analysis as a

def write_csv(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    header=sorted(set().union(*(r.keys() for r in data)))
    with path.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,header);writer.writeheader();writer.writerows(data)

def fixture_rows(cohort,person,slope):
    random=cohort=='Stability01-RandomVer2';rest=not random
    rows=[dict(participant=person,blockHappySlider_response=.7)]
    rows[0]={'participant':person,'blockHappySlider.response':.7,'blockHappySlider.rt':1.5,
             'iriDur':27,'expName':'Mmi_Motion' if cohort=='Motion' else 'fixture','condition':'random' if random else ''}
    dt=30 if rest else 13
    for i in range(1,19):
        row={'participant':person,'happySlider.response':.7+slope*i*dt/60,'happySlider.rt':1.5}
        if rest:row['returnLoop.ran']=1
        else:row.update({'choice':'gamble','choiceKey.rt':2,'doRating':'Yes'})
        rows.append(row)
    rows.append({'participant':person,'blockHappySlider.response':.2,'blockHappySlider.rt':1.5})
    return rows

def construct(path):
    path=Path(path);files=[];mapping={};slopes={'Recovery1':-.010,'Motion':-.004,'Stability01-RandomVer2':-.008}
    ordinal=0
    for cohort,slope in slopes.items():
        check=[]
        for person in range(24):
            ordinal+=1;relative=f'working/member_{ordinal:05}.csv'
            write_csv(path/relative,fixture_rows(cohort,str(person),slope))
            files.append(dict(file=relative,cohort=cohort,group='PilotData',sha256=s.sha(path/relative)))
            check.append({'participant':str(person),'isComplete':'True'})
        relative=f'working/check_{cohort}.csv';write_csv(path/relative,check)
        mapping[cohort]=dict(file=relative,sha256=s.sha(path/relative))
    s.save(path/'SANITIZATION_MANIFEST.json',dict(constructed_fixture=True,archive_sha256='constructed',files=files))
    s.save(path/'cohort-map.json',dict(cohort_data_checks=mapping));(path/'salt.bin').write_bytes(bytes(range(32)))
    return dict(source=str(path),cohort_map=str(path/'cohort-map.json'),cohort_map_sha256=s.sha(path/'cohort-map.json'),salt=str(path/'salt.bin'))

def run(path):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    inputs=construct(path/'source');config=dict(constructed_fixture=True,draws=2000)
    s.save(path/'INPUTS.json',inputs);s.save(path/'CONFIG.json',config)
    s.execute(path/'projection',inputs,config);s.verify(path/'projection',inputs,config)
    analysis_inputs=dict(ratings=str(path/'projection'/'PRIVATE_RATINGS.parquet'))
    a.execute(path/'analysis',analysis_inputs,config)
    result=json.loads((path/'analysis'/'SCIENCE.json').read_text('utf8'))
    assert abs(result['primary']['contrasts']['visuomotor_minus_rest']['estimate']-.006)<1e-12
    assert result['primary']['reading']=='supports'
    frame=a.load(analysis_inputs,config)
    # The exact-null and contrary worlds retain each native time and cluster.
    for world,slopes in [('null',dict(rest=-.008,visuomotor=-.008,random_gambling=-.008)),
                         ('opposite',dict(rest=-.004,visuomotor=-.010,random_gambling=-.008))]:
        changed=frame.copy();changed['mood']=.7+changed.minute*np.array([slopes[c] for c in changed.condition])
        calculated=a.analyse(changed,2000);assert calculated['primary']['reading']=='against'
        s.save(path/(world+'.json'),calculated)
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_md4_fixture','--output',str(path),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-2000:])
    record=dict(constructed=True,scientific_admission=False,passed=True,
                checks=['native full source projection','known rest/task/random event durations','known0.006 slope contrast',
                        'exact-null against','opposite-order against','fresh process entire source/2000draw replay','independent person OLS'],
                source_pins={name:s.sha(Path(__file__).with_name(name)) for name in ('week5_md4_source.py','week5_md4_analysis.py','week5_md4_fixture.py')},
                replay=json.loads(child.stdout))
    s.save(path/'COMPLETE.json',record);return dict(passed=True,checks=len(record['checks']))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--verify',action='store_true');args=p.parse_args();path=Path(args.output)
    if args.verify:
        inputs=json.loads((path/'INPUTS.json').read_text('utf8'));config=json.loads((path/'CONFIG.json').read_text('utf8'))
        result=dict(source=s.verify(path/'projection',inputs,config),analysis=a.verify(path/'analysis',dict(ratings=str(path/'projection'/'PRIVATE_RATINGS.parquet')),config))
    else:result=run(path)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
