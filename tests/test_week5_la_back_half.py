from pathlib import Path
import json
import zipfile
import numpy as np
import pytest
from runners.drive.cards import week5_la_back_half as m
from runners.drive.cards import week5_la_back_half_source as s
from runners.drive.cards import week5_la_back_half_fixture as f


def test_complete_handler_replay_and_continuation(tmp_path):
    assert f.execute(tmp_path, {}, {})["passed"]
    assert f.verify(tmp_path, {}, {})["verified"]


def test_absorbed_lpm_matches_dense_dummy_oracle_and_absorbs_starter():
    rng = np.random.default_rng(174)
    persons = np.tile(np.arange(4), 30).astype(str)
    events = np.repeat(np.arange(30), 4).astype(str)
    x = rng.normal(size=(120, 3))
    y = .4*x[:, 0] - .2*x[:, 1] + rng.normal(size=120)
    residual = m.absorb_laugh_person(np.column_stack((x, y)), events, persons)
    actual = m.partial(residual[:, :3].T@residual[:, :3], residual[:, :3].T@residual[:, 3])
    full = np.column_stack((x, np.ones(120), m.columns(events), m.columns(persons)))
    assert abs(actual - np.linalg.lstsq(full, y, rcond=None)[0][0]) < 1e-11
    starter = np.repeat(rng.normal(size=30), 4)
    absorbed = m.absorb_laugh_person(starter[:, None], events, persons)
    assert np.max(np.abs(absorbed)) < 1e-12


def test_signed_exact_null_and_weighted_speaker_oracle():
    rng = np.random.default_rng(175)
    persons = np.tile(np.arange(12), 10).astype(str)
    meetings = np.repeat(np.arange(30), 4).astype(str)
    x = rng.normal(size=(120, 3))
    counts = np.arange(30) % 3
    ordered = sorted(set(meetings)); lookup = {v: i for i, v in enumerate(ordered)}
    w = np.array([counts[lookup[k]] for k in meetings])
    for sign in (-1, 0, 1):
        y = sign*.35*x[:, 0] + .2*x[:, 1] + np.array([int(p) for p in persons])*.05
        answer = m.scalar_speaker_fit(x, y, persons, meetings, counts, ordered)
        full = np.column_stack((x, np.ones(120), m.columns(persons)))
        oracle = np.linalg.lstsq(full*np.sqrt(w[:, None]), y*np.sqrt(w), rcond=None)[0][0]
        assert abs(answer-oracle) < 1e-11 and abs(answer-sign*.35) < 1e-11
        draws = []
        for draw in range(2000):
            rr = np.random.default_rng(np.random.SeedSequence([m.SEED, 123, draw]))
            multiplicity = np.bincount(rr.integers(0, 30, 30), minlength=30)
            draws.append(m.scalar_speaker_fit(x, y, persons, meetings, multiplicity, ordered))
        result = m.summarize(answer, draws, .1, 30, "H12-T4")
        assert result["outcome"] == ("supports" if sign == 1 else "against")
        assert result["sees"] == 2.8*np.std(draws, ddof=1)


def test_repeat_requires_distinct_lemmas_order_and_exact_gap():
    assert m.same_order(["a", "b", "c"], ["a", "x", "c"], 2)
    assert not m.same_order(["a", "b"], ["b", "a"], 2)
    assert not m.same_order(["a", "a"], ["a", "a"], 2)
    rows=[{"id":str(i),"group":"g","order":0,"start":start,"end":start+1,"meeting":"m","laughed_after":True,"content":content}
          for i,(start,content) in enumerate([(0,["a","b"]),(30,["a","b"]),(31,["a","b"]),(80,["z"]),(100,["a","z"])])]
    kinds=[r["category"] for r in m.repetition(rows)]
    assert kinds == ["fresh","between","repeat","fresh","between"]


def test_indexed_history_matches_exhaustive_history_and_honors_yield(tmp_path):
    rng=np.random.default_rng(993)
    rows=[{'id':str(i),'group':'g','order':i//40,'start':float((i%40)*9),'end':float((i%40)*9+1),
           'meeting':str(i//40),'laughed_after':bool(i%2),'content':rng.choice(list('abcdefgh'),size=3,replace=False).tolist()} for i in range(120)]
    for row in rows:
        row['absolute_start_bounds']=[row['order']*86400+row['start']]*2
        row['absolute_end_bounds']=[row['order']*86400+row['end']]*2
    expected=[];history=[]
    for row in rows:
        eligible=[p for p in history if p['laughed_after']==row['laughed_after'] and (p['meeting']!=row['meeting'] or p['end']<=row['start']-30)]
        overlaps=[p for p in eligible if set(p['content']) & set(row['content'])]
        any_overlap=any(p['laughed_after']==row['laughed_after'] and set(p['content']) & set(row['content']) for p in history)
        expected.append('repeat' if any(m.same_order(row['content'],p['content'],2) for p in overlaps) else 'between' if any_overlap else 'fresh')
        history.append(row)
    assert [r['category'] for r in m.repetition(rows)]==expected
    (tmp_path/'YIELD_REQUEST.json').write_text('{}')
    with pytest.raises(m.RuntimeYield):m.repetition(rows,output=tmp_path)
    assert s.execute(tmp_path,{}, {})['status']=='yielded'
    assert m.execute(tmp_path,{}, {})['status']=='yielded'


def test_missing_meeting_clock_retains_only_time_invariant_categories():
    start,end=m.absolute_bounds({'source_local_day_seconds':0},10.,11.)
    assert start==[10.,86410.] and end==[11.,86411.]
    first={'id':'a','group':'g','order':0,'meeting':'a','start':0.,'end':1.,'laughed_after':True,
           'content':['alpha','beta'],'absolute_start_bounds':[0.,86400.],'absolute_end_bounds':[1.,86401.]}
    later={**first,'id':'b','order':1,'meeting':'b','start':40.,'end':41.,
           'absolute_start_bounds':[40.,86440.],'absolute_end_bounds':[41.,86441.]}
    assert m.repetition([first,later])[-1]['category']=='timing_unsupported'
    assert m.repetition([first,{**later,'content':['new','topic']}])[-1]['category']=='fresh'
    assert m.repetition([first,{**later,'absolute_start_bounds':[172840.]*2}])[-1]['category']=='repeat'
    assert m.repetition([first,{**later,'absolute_start_bounds':[20.]*2}])[-1]['category']=='between'


def test_unannotated_speech_changes_pause_and_recent_speech_without_text(tmp_path):
    inputs,_=f.pause_source(tmp_path)
    acts,laughs,metadata,lemmas=[m.gzread(inputs[k]) for k in ('acts','laughs','metadata','lemmas')]
    chosen=acts[0];other=next(p for p in metadata[chosen['meeting']]['speakers'] if p!=chosen['speaker'])
    speech=m.act_speech(acts)+[{'meeting':chosen['meeting'],'speaker':other,'start':chosen['start']-1.,'end':chosen['start']-.1}]
    rows,_=m.temporal_rows(acts,laughs,metadata,lemmas,{},speech_rows=speech)
    observed=next(r for r in rows if r['id']==chosen['id'])
    assert abs(observed['log_pause']-np.log1p(.1))<1e-12 and not observed['previous_same']
    event=[{'meeting':chosen['meeting'],'speaker':chosen['speaker'],'start':chosen['start']+2.,'end':chosen['start']+2.1,'label':'vocal'}]
    joined,_=m.joining_rows([],event,metadata,speech_rows=speech)
    assert next(r for r in joined if r['person']==other)['spoke_recently']==1.


def test_joining_quiet_window_and_tied_starter_refusal():
    metadata=f.meta(2); meeting=next(iter(metadata)); people=list(metadata[meeting]["speakers"])
    events=[{"meeting":meeting,"speaker":person,"start":t,"end":t+.1,"label":"vocal"}
            for t,person in [(3,people[0]),(4,people[1]),(7.1,people[2]),(7.1,people[3])]]
    rows,audit=m.joining_rows([],events,metadata)
    assert len(rows)==3 and sum(r["joined"] for r in rows)==1
    assert audit["ambiguous_simultaneous_starters"] == 1


def test_content_frequency_lexical_ties_and_checkpoint_refusal(tmp_path):
    acts=[{"id":f"constructed-{i}","meeting":"m","speaker":"s","corpus":"AMI","start":i,"end":i+1,
           "words":[{"text":"walked","kind":"word"},{"text":"rare"+chr(97+i%26),"kind":"word"}]} for i in range(70)]
    lemma=lambda words:["walk" if x=="walked" else x for x in words]
    assert s.prepare_lemmas(acts,tmp_path,"b",lemma,max_blocks=1) is None
    result=s.prepare_lemmas(acts,tmp_path,"b",lemma)
    assert len(result[0])==70 and result[1]["AMI"][0]=="walk"
    with pytest.raises(ValueError,match="checkpoint"):
        s.prepare_lemmas(acts,tmp_path,"changed",lemma)


def test_missing_chronology_and_individual_metadata_are_not_zero(tmp_path):
    inputs,pins=f.join_source(tmp_path)
    metadata=m.gzread(inputs["metadata"])
    for row in metadata.values():
        if row["corpus"]=="ICSI":row["start_utc_seconds"]=None
    rows,_=m.joining_rows(m.gzread(inputs["acts"]),m.gzread(inputs["laughs"]),metadata)
    stats,names,counts=m.background_design(rows,metadata,"ICSI","prior_coattendance")
    assert stats=={} and names==[] and counts["status"]=="source-held"
    for row in metadata.values():row["order_qualified"]=False
    rows,audit=m.temporal_rows(m.gzread(inputs["acts"]),m.gzread(inputs["laughs"]),metadata,[],{})
    assert rows is None and audit["status"]=="source-held"


def test_changed_source_and_draw_contract_refuse(tmp_path):
    inputs,pins=f.join_source(tmp_path)
    config={"phase":"LA4","pins":{**pins,"acts":"0"*64},"constructed_fixture":True,"draws":32}
    with pytest.raises(ValueError,match="source changed"):
        m.execute(tmp_path/"bad",inputs,config)
    with pytest.raises(ValueError,match="draw contract"):
        m.execute(tmp_path/"draw",inputs,{**config,"pins":pins,"constructed_fixture":False})
    with pytest.raises(ValueError,match="complete input pins"):
        m.execute(tmp_path/"missing",inputs,{**config,"pins":{'acts':pins['acts']}})


def test_actual_metadata_archive_adapter_and_complete_replay(tmp_path):
    archives=tmp_path/'archives';archives.mkdir()
    salt=b'c'*32; salt_path=tmp_path/'salt';salt_path.write_bytes(salt)
    ami=s.identity(salt,'AMI','meeting','ES9000a');icsi=s.identity(salt,'ICSI','meeting','Bmr900')
    ap=s.identity(salt,'AMI','speaker','ES9000a|A');ip=s.identity(salt,'ICSI','speaker','Bmr900|A')
    original={ami:{'corpus':'AMI','duration':20.,'speakers':{ap:{'native_language':'constructed-language'}}},
              icsi:{'corpus':'ICSI','duration':20.,'speakers':{ip:{'english_variety':'constructed-variety','region':'constructed-region'}}}}
    with zipfile.ZipFile(archives/'AMI.zip','w') as z:
        z.writestr('corpusResources/meetings.xml','<root><meeting observation="ES9000a" type="scenario" dateOnly="01-01-2005" startTime="12:30"><speaker nxt_agent="A" global_name="constructed-person-a" role="manager"/></meeting></root>')
        z.writestr('words/ES9000a.A.words.xml','<root><w starttime="1" endtime="2">unannotated</w><w>untimed</w><vocalsound starttime="3" endtime="4" type="laugh"/></root>')
    with zipfile.ZipFile(archives/'ICSI-core.zip','w') as z:
        z.writestr('ICSI/DialogueActs/Bmr900.A.dialog-act.xml','<root><da participant="constructed-person-i"><child href="../Words/Bmr900.A.words.xml#id(w1)"/></da></root>')
        z.writestr('ICSI/Words/Bmr900.A.words.xml','<root><w starttime="3" endtime="4">laugh</w></root>')
    with zipfile.ZipFile(archives/'ICSI-plus.zip','w') as z:z.writestr('fixture.txt','constructed duplicate layer')
    original_dir=tmp_path/'qualified';original_dir.mkdir()
    s.gzip_equal(original_dir/'ACTS.json.gz',[{'id':'constructed-act','meeting':ami}])
    s.gzip_equal(original_dir/'LAUGHS.json.gz',[])
    s.gzip_equal(original_dir/'METADATA.json.gz',original)
    config={'mode':'metadata','constructed_fixture':True,'fixture_archive_pins':{k:s.digest(archives/(k+'.zip')) for k in s.old.PINS}}
    inputs={'source':str(original_dir),'archive_root':str(archives),'identity_salt':str(salt_path)}
    result=s.execute(tmp_path/'output',inputs,config)
    assert result['chronology_held_meetings']==1
    meta=s.gzread(tmp_path/'output/METADATA_EXT.json.gz')
    assert meta[ami]['order_qualified'] and meta[ami]['series_rank']==0
    assert meta[ami]['speakers'][ap]['role']=='manager'
    assert meta[icsi]['series_rank'] is None and not meta[icsi]['order_qualified']
    assert meta[ami]['source_local_day_seconds'] is not None
    speech=s.gzread(tmp_path/'output/SPEECH.json.gz')
    assert len(speech)==2 and all(set(r)=={'meeting','speaker','start','end'} for r in speech)
    assert result['speech_counts']['AMI_unsupported_word_timing']==1
    assert s.verify(tmp_path/'output',inputs,config)['verified']
