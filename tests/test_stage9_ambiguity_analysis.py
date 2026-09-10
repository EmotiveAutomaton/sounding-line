import copy
import math
import pytest
from runners.stage9.ambiguity_jobs import QUESTIONS
from runners.stage9.ambiguity_analysis import project,profile
from runners.stage9.artifact_analysis import select
from runners.stage9.launch import handler_operation


def rows(prefix='e'):
    return [{'unit':prefix+str(i),'domain':'a' if i%2 else 'b','purpose':'p','role':'pilot',
             'questions':{q:{'truth':'h' if q.startswith('history') else 'y',
                 'support':['h','j'] if q.startswith('history') else ['x','y'],
                 'predictions':{'model':{'h':.8,'j':.2} if q.startswith('history') else {'x':.2,'y':.8},
                                'base':{'h':.5,'j':.5} if q.startswith('history') else {'x':.5,'y':.5}},
                 'validity':{'model':True,'base':True},'unique_prior_works':0} for q in QUESTIONS}}
            for i in range(4)]


def card(q):
    return {'id':q,'card':'M05','left':{'query':q,'model':'model'},'right':{'query':q,'model':'base'},
            'threshold':.05,'strata':['domain','purpose'],'required_controls':['complete target-specific support'],
            'meaning':'held-out log score on this question own historical or future target'}


def test_each_question_scores_its_own_truth_and_equal_forecasts_are_zero():
    r=rows();ids=[x['unit'] for x in r]
    out=profile(r,ids,[card(q) for q in QUESTIONS],None,'f'*64,'pilot',draws=100)
    assert len(out['contrasts'])==6
    assert all(c['overall']['mean']==pytest.approx(math.log(.8/.5)) for c in out['contrasts'])
    for row in r:
        for item in row['questions'].values():item['predictions']['model']=item['predictions']['base']
    zero=profile(r,ids,[card(q) for q in QUESTIONS],None,'f'*64,'pilot',draws=100)
    assert all(c['overall']['mean']==0 for c in zero['contrasts'])
    bad=card('history_artifact');bad['right']['query']='future_old'
    with pytest.raises(ValueError,match='different question'):profile(r,ids,[bad],None,'f'*64,'pilot')


def test_invalid_or_nonfinite_components_cannot_be_silently_dropped():
    r=rows();ids=[x['unit'] for x in r];q='history_artifact'
    r[0]['questions'][q]['validity']['model']=False
    invalid=profile(r,ids,[card(q)],None,'f'*64,'pilot',draws=100)['contrasts'][0]
    assert invalid['scored_units']==0 and invalid['assigned_units']==4 and invalid['excluded_units']==0
    r=rows();r[0]['questions'][q]['predictions']['model']={'h':0.,'j':1.}
    nonfinite=profile(r,ids,[card(q)],None,'f'*64,'pilot',draws=100)['contrasts'][0]
    assert nonfinite['scored_units']==4 and nonfinite['excluded_units']==0 and nonfinite['promotion_eligible'] is False
    del r[0]['questions']['future_record']
    with pytest.raises(ValueError):project(r,q)


def test_development_rival_cannot_reuse_evaluation_units():
    q='history_artifact';r=rows();ids=[x['unit'] for x in r]
    selection=select(project(r,q),ids,{q:['base','model']},'f'*64)
    contrast=card(q);contrast['right']={'query':q,'selected_for':q}
    with pytest.raises(ValueError,match='reuse'):profile(r,ids,[contrast],selection,'f'*64,'pilot',draws=100)
    assert handler_operation({'module':'runners.stage9.purpose_jobs','arguments':['--consumer','ambiguity']})[1]=='predict-ambiguity'
    assert handler_operation({'module':'runners.stage9.ambiguity_analysis','arguments':['--operation','evaluate']})[1]=='evaluate'


def test_full_analysis_reads_committed_neural_rows_and_checks_reentry(tmp_path,monkeypatch):
    from pathlib import Path
    from runners.stage9 import ambiguity_analysis as module
    from runners.stage9 import artifact_analysis
    from runners.stage9.common import write,read,Units,closure,digest,file_hash
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'inside',lambda p:Path(p).resolve())
    monkeypatch.setattr(artifact_analysis,'inside',lambda p:Path(p).resolve())
    monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    package='f'*64;source={'sha256':'e'*64};numeric={}
    for lane,prefix in (('development','d'),('evaluation','e')):
        data=rows(prefix)
        for row in data:row.update(case_sha256=digest(row['unit']),source_template_sha256=digest('template'+row['unit']))
        path=tmp_path/lane;numeric[lane]=path
        identity={'operation':'ambiguity-predictions-v1','selected_units':[r['unit'] for r in data],
                  'model_completion_sha256':package,'case_completion_sha256':'c'*64,'source':source}
        write(path/'IDENTITY.json',identity);write(path/'PREDICTIONS.json',data)
        write(path/'COMPLETE.json',{'execution_complete':True,'role':'pilot','identity_sha256':digest(identity),
              'assigned_units':4,'completed_units':4,'outputs':closure([path/'PREDICTIONS.json'])})
    root=tmp_path/'private/ambiguity-analysis-pilots/fixture'
    sp=tmp_path/'select-plan.json'
    write(sp,{'operation':'select','role':'pilot','queries':{q:['base','model'] for q in QUESTIONS},'contrasts':[],'package_sha256':package})
    module.run(root/'select',numeric['development'],sp,'select','pilot')
    neural=tmp_path/'neural';data=read(numeric['evaluation']/'PREDICTIONS.json')
    ni={'operation':'ambiguity','role':'pilot','cell_identity':'a'*64,'units':[r['unit'] for r in data],
        'cases_complete_sha256':'c'*64}
    store=Units(neural,ni)
    for row in data:
        out={k:row[k] for k in ('unit','domain','role','case_sha256')};out['operation']='ambiguity'
        out['result']={'source_template_sha256':row['source_template_sha256'],'questions':{
            q:{'truth':item['truth'],'support':item['support'],
               'call':{'accepted':True,'prediction':{'probs':item['predictions']['model']}}} for q,item in row['questions'].items()}}
        store.put(row['unit'],out)
    write(neural/'COMPLETE.json',{'execution_complete':True,'identity_sha256':digest(ni),'cell_identity':'a'*64,
        'outputs':closure([neural/'IDENTITY.json',neural/'units']),'completed_units':4})
    ep=tmp_path/'eval-plan.json';contrasts=[card(q) for q in QUESTIONS]
    for c in contrasts:c['left']['model']='neural';c['right']={'query':c['right']['query'],'selected_for':c['right']['query']}
    write(ep,{'operation':'evaluate','role':'pilot','queries':{},'contrasts':contrasts,'package_sha256':package})
    done=module.run(root/'evaluate',numeric['evaluation'],ep,'evaluate','pilot',root/'select/SELECTION.json',neural)
    assert done['execution_complete'] and done['assigned_units']==4
    assert all(c['overall']['mean']==0 for c in read(root/'evaluate/CONTRASTS.json')['contrasts'])
    assert module.run(root/'evaluate',numeric['evaluation'],ep,'evaluate','pilot',root/'select/SELECTION.json',neural)==done
