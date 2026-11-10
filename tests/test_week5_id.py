from pathlib import Path
import csv,io,tarfile
import pandas as pd
from runners.drive.cards import week5_id_source as s,week5_id_analysis as a


def test_full_source_pair_and_temporal_half_contract(tmp_path,monkeypatch):
    rows=[]
    for person,sessions in [('steady',1),('other',1),('returning',2)]:
        for session in range(sessions):
            for order in range(1,14):
                kind='Species' if order<=3 else 'Random' if order>=7 else 'Other'
                save_human=not(person=='other' and order==1)
                for side in [0,1]:
                    r=dict.fromkeys(s.HUMANS+s.PET,0)
                    r['Man']=int(side==0);r['Dog']=(2 if kind=='Random' else 1)*int(side==1)
                    r.update(ResponseID=f'{person}-{session}-{order}',UserID=person,ExtendedSessionID=f'{person}-{session}',
                             ScenarioOrder=order,ScenarioType=kind,ScenarioTypeStrict=kind,Intervention=side,
                             Saved=int(save_human if side==0 else not save_human),NumberOfCharacters=r['Man']+r['Dog'])
                    rows.append(r)
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=s.BASE+s.HUMANS+s.PET);writer.writeheader();writer.writerows(rows)
    data=stream.getvalue().encode();archive=tmp_path/'fixture.tar.gz'
    with tarfile.open(archive,'w:gz') as t:
        entry=tarfile.TarInfo('SharedResponses.csv');entry.size=len(data);t.addfile(entry,io.BytesIO(data))
    salt=tmp_path/'salt';salt.write_bytes(b'x'*32);monkeypatch.setattr(s,'SOURCE_SHA',s.common.sha(archive))
    inputs={'source':str(archive),'salt':str(salt)};r=s.execute(tmp_path/'run',inputs,{})
    assert r['counts']['single_complete_13_scenario_fingerprints']==2
    assert r['counts']['multi_session_fingerprints_excluded_primary']==1
    assert s.verify(tmp_path/'run',inputs,{})['verified']
    frame=pd.read_parquet(tmp_path/'run/cases.parquet');cases,counts=a.cases(frame)
    assert len(cases)==14 and cases.person.nunique()==2 and cases.exposure.eq(3).all()
    assert counts['steady_outnumbered_cases']==7
    assert a.analyse(cases)['status']=='design cannot test'
    a.execute(tmp_path/'case-run',{'source':str(tmp_path/'run/cases.parquet')},{'phase':'cases'})
    assert a.verify(tmp_path/'case-run',{'source':str(tmp_path/'run/cases.parquet')},{'phase':'cases'})['verified']


def test_quantity_ratio_is_log2_pets_over_humans():
    rows=[]
    for who,steady in [('first',True),('second',False)]:
        for order in range(1,4):rows.append(dict(person=who,session='one',order=order,kind='Species',humans=1,pets=1,human_saved=int(steady or order>1),primary_session=True,sessions=1))
        rows.append(dict(person=who,session='one',order=7,kind='Random',humans=2,pets=8,human_saved=1,primary_session=True,sessions=1))
    cases,_=a.cases(pd.DataFrame(rows));assert cases.log_ratio.eq(2).all()
