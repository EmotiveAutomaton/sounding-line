import copy

import pytest

from runners.stage9 import training_jobs as jobs


def fixture(monkeypatch):
    monkeypatch.setattr(jobs,'parameter_partition',lambda world:world['partition'])
    sources=[{'key':str(i),'lineages':[str(i)],'input_ids':[1,2,3],
              'raw_record':{'domain':'essay' if i%2 else 'workshop_doc'}} for i in range(1600)]
    rows=[{'key':s['key'],'lineages':s['lineages'][:],'input_ids':[1,2,3],
           'labels':[1,2,3],'kind':'original_replay'} for s in sources]
    corpus={'split':'training','examples':rows,'validation':[{'input_ids':[1,2,3]}],
            'validation_choices':[{'key':'dev'+str(i),'parameter_partition':'development',
                                   'options':{'stop':'STOP','action':'do'},'truth':'action'} for i in range(96)]}
    pool={'candidate_examples':sources,'private_worlds':{s['key']:{'partition':'training'} for s in sources}}
    return corpus,copy.deepcopy(corpus),pool


def test_factorial_and_unidentified_invocation(monkeypatch):
    assert len(jobs.FITS)==len(set(jobs.FITS))==24
    assert {(f,r):{s for ff,rr,s in jobs.FITS if (ff,rr)==(f,r)} for f,r,_ in jobs.FITS}=={
        (f,r):{9001,9002,9003} for f in ('qwen','smollm') for r in jobs.RECIPES}
    monkeypatch.delenv('S9_CELL_IDENTITY',raising=False)
    with pytest.raises(ValueError,match='identity'):jobs.cell_identity()
    with pytest.raises(ValueError,match='factorial'):jobs.training_root('qwen','original_expert',99001)


def test_exact_replay_then_reject_changed_exposure(monkeypatch):
    corpus,reference,pool=fixture(monkeypatch)
    assert jobs.validate_corpus(corpus,reference,pool,'original_expert')['cells']['original_expert']['examples']==1600
    corpus['examples'][0]['lineages']=['another-maker']
    with pytest.raises(ValueError,match='source exposure'):jobs.validate_corpus(corpus,reference,pool,'original_expert')


def test_held_parameter_and_omitted_stop_refuse(monkeypatch):
    corpus,reference,pool=fixture(monkeypatch)
    pool['private_worlds']['0']['partition']='reserve'
    with pytest.raises(ValueError,match='held-out'):jobs.validate_corpus(corpus,reference,pool,'original_expert')
    pool['private_worlds']['0']['partition']='training'
    for data in (corpus,reference):del data['validation_choices'][0]['options']['stop']
    with pytest.raises(ValueError,match='STOP'):jobs.validate_corpus(corpus,reference,pool,'original_expert')


def test_own_token_and_common_validation_refuse(monkeypatch):
    corpus,reference,pool=fixture(monkeypatch)
    corpus['examples'][0]['labels'][1]=9
    with pytest.raises(ValueError,match='target labels'):jobs.validate_corpus(corpus,reference,pool,'original_expert')
    corpus['examples'][0]['labels'][1]=2
    corpus['validation_choices'][0]['truth']='stop'
    with pytest.raises(ValueError,match='share exact development'):jobs.validate_corpus(corpus,reference,pool,'original_expert')


def test_discarded_rehearsal_cannot_enter_scientific_namespace(monkeypatch,tmp_path):
    monkeypatch.setattr(jobs,'ROOT',tmp_path)
    monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    monkeypatch.setattr(jobs,'rehearsal_input',lambda family:pytest.fail('invalid scope reached inputs'))
    with pytest.raises(ValueError,match='namespace'):
        jobs.run_fit('qwen','both_mixed',997901,tmp_path/'COMPLETE.json',tmp_path/'private/scientific-training')
    with pytest.raises(ValueError,match='namespace'):
        jobs.run_fit('qwen','both_mixed',9001,tmp_path/'COMPLETE.json',tmp_path/'private/training-handler-pilots/qwen')


def test_fitting_receipt_requires_actual_complete_optimizer_and_checkpoint(monkeypatch,tmp_path):
    from runners.stage9 import train as trainer
    from runners.stage9.common import write,file_hash,digest,closure
    path=tmp_path/'corpus.json';output=tmp_path/'fit'
    write(path,{'examples':[{'labels':[1,2,3]} for _ in range(64)]})
    fitted={'corpus_sha256':file_hash(path),'epochs':1,'batch':4,'accumulation':2}
    write(output/'IDENTITY.json',fitted)
    write(output/'checkpoint/weights.json',{'actual_fixture_weights':[1,2]})
    receipt={'identity_sha256':digest(fitted),'curve':[{'updates':8}],
        'exposure':{'supervised_tokens':128},'selected_checkpoint':'checkpoint',
        'selected_checkpoint_sha256':closure([output/'checkpoint'])['sha256']}
    calls=[]
    def fit(*args,**kwargs):calls.append(kwargs);return receipt
    monkeypatch.setattr(trainer,'train',fit)
    assert jobs.execute_fit(path,output,'qwen',997901,epochs=1,expected_examples=64)==receipt
    assert calls[0]['loss_mode']=='streamed' and calls[0]['epochs']==1 and calls[0]['checkpoint_every']==25
    receipt['curve'][0]['updates']=7
    with pytest.raises(ValueError,match='reconcile'):
        jobs.execute_fit(path,output,'qwen',997901,epochs=1,expected_examples=64)
    receipt['curve'][0]['updates']=8
    write(output/'checkpoint/weights.json',{'actual_fixture_weights':[3,4]})
    with pytest.raises(ValueError,match='reconcile'):
        jobs.execute_fit(path,output,'qwen',997901,epochs=1,expected_examples=64)
