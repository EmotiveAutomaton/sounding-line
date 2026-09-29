from contextlib import contextmanager
from copy import deepcopy
import json
import pytest
from runners.stage13 import healing_reader as reader, healing_memory as memory, healing_detector as detector
from runners.stage13.reconstruction import ACTIONS,FIELDS
from runners.stage13.common import freeze,read
from runners.stage13 import worker,gpu


def reply(row):
    body=dict(handling={a:float(a==row['target']['handling']) for a in ACTIONS},
        facts=[dict(slot=f['slot'],exact_spans=f['exact_spans'],**{k:{label:float(label==f[k]) for label in labels} for k,labels in FIELDS.items()}) for f in row['target']['facts']],
        goal_support=[.25]*4,unknown_history=.1)
    return dict(done=True,done_reason='stop',prompt_eval_count=600,eval_count=2400,message=dict(content=json.dumps(body)))


def test_named_protocol_exact_mapping_and_refusals():
    row=reader.fixtures()[0];response=reply(row);parsed=reader.parse(response,len(row['views']['A']['endpoint']))
    assert parsed['handling']==[1.,0,0,0]
    assert response['eval_count']==2400
    bad=deepcopy(response);body=json.loads(bad['message']['content']);body['handling']['edit']=.5
    bad['message']['content']=json.dumps(body)
    with pytest.raises(ValueError,match='invalid literal'):reader.parse(bad,9)
    bad=deepcopy(response);bad['done_reason']='length'
    with pytest.raises(ValueError):reader.parse(bad,9)
    bad=deepcopy(response);bad['prompt_eval_count']=4097
    with pytest.raises(ValueError):reader.parse(bad,9)


@pytest.mark.parametrize('wrong',[False,True])
def test_actual_named_admission_handler(tmp_path,monkeypatch,wrong):
    rows=reader.fixtures();freeze(tmp_path/'input.json',rows)
    @contextmanager
    def service(*args):yield {}
    monkeypatch.setattr(gpu,'service',service)
    expected={r['views']['D']['observed_handling']:r for r in rows}
    calls=[]
    def call(evidence,arm,*args):
        calls.append(gpu.request(evidence,arm))
        r=reply(expected[evidence['observed_handling']])
        if wrong:
            body=json.loads(r['message']['content']);body['handling']={a:float(a=='accept') for a in ACTIONS};r['message']['content']=json.dumps(body)
        return dict(parsed=gpu.parse(r,len(evidence['endpoint'])))
    monkeypatch.setattr(gpu,'call',call);old=(gpu.request,gpu.parse)
    out=tmp_path/'output'
    worker.handle(dict(action='qwen-keyed-admission',args=dict(rows='input.json',views=['D'],arms=['direct'])),out,tmp_path,lambda:None)
    assert read(out/'ADMISSION.json')['admitted'] is (not wrong)
    assert len(calls)==4 and (gpu.request,gpu.parse)==old
    assert calls[0]['format']['properties']['handling']['type']=='object'


def test_real_tokenizer_information_matching_and_consumer(tmp_path):
    from transformers import AutoTokenizer
    from runners.stage13.detectors import cached_model
    tok=AutoTokenizer.from_pretrained(cached_model('openai-community/gpt2-medium'),local_files_only=True)
    train=reader.fixtures()[0];train['unit']='training';train['key']='training'
    for f in train['target']['facts']:f.update(related_slot=None,span_state='recorded',span_ids=[])
    row=deepcopy(train);row.update(unit='evaluation',key='evaluation',partition='reserve')
    row['views']['C']=row['views']['D']
    rendered,meta=memory.prompts(row,[train],tok,'C')
    assert len(set(meta['native_tokens'][m] for m in memory.MODES if m!='raw-unpadded'))==1
    assert all(s.endswith('Recorded action:') for s in rendered.values())
    records=[]
    from runners.stage13.scoring import proper_loss
    for view in ('A','C'):
        for mode in memory.MODES:
            p=[1.,0,0,0,0]
            records.append(dict(key=row['key'],unit=row['unit'],partition='reserve',view=view,mode=mode,probabilities=p,truth=0,scores=proper_loss(p,0,5)))
    result=memory.summarize(records,[row])
    assert result['paired']['reserve/C/linked-minus-raw']['log_loss']['mean']==0
    assert result['paired']['reserve/C/linked-minus-raw']['log_loss']['low'] is None
    with pytest.raises(ValueError,match='incomplete'):memory.summarize(records[:-1],[row])
    with pytest.raises(ValueError,match='source split'):memory.prompts(train,[train],tok,'D')


def test_paired_estimands_and_order_invariance():
    rows=[dict(key='a1',unit='a',label=1,left=.9,right=.1),dict(key='a2',unit='a',label=1,left=.9,right=.1),dict(key='b1',unit='b',label=1,left=.1,right=.9),dict(key='a0',unit='a',label=0,left=.1,right=.1),dict(key='b0',unit='b',label=0,left=.1,right=.1)]
    result=detector.paired(rows,'left','right',.5,.5,draws=100)
    assert result==detector.paired(rows[::-1],'left','right',.5,.5,draws=100)
    assert result['estimates']['pooled_recall_gain']['mean']==pytest.approx(1/3)
    assert result['estimates']['source_average_recall_gain']['mean']==0
    identical=detector.paired(rows,'left','left',.5,.5,draws=100)
    assert all(v['mean']==v['low']==v['high']==0 for v in identical['estimates'].values())
    with pytest.raises(ValueError,match='duplicate'):detector.paired(rows+rows[:1],'left','right',.5,.5)


def test_strong_extension_actual_handler_and_fixed_cut_refusal(tmp_path,monkeypatch):
    import torch
    from types import SimpleNamespace
    from runners.stage12 import local_api
    from transformers import AutoTokenizer,AutoModelForSequenceClassification
    raw=tmp_path/'healing';raw.mkdir();(tmp_path/'results').mkdir()
    freeze(raw/'CONTRACT.json',dict(reporting='2099-01-01T00:00:00+00:00'))
    freeze(raw/'ALLOCATION.json',dict(gear=2))
    rows=[dict(key='human',unit='u',label=0,text='known human'),dict(key='machine',unit='u',label=1,text='known machine')]
    freeze(tmp_path/'source.json',rows);cuts={'0.01':.8,'0.05':.6}
    freeze(tmp_path/'jobs/train/TRAINED.json',dict(checkpoint_files={'model':'fixed'}))
    freeze(tmp_path/'jobs/cal/CALIBRATION.json',cuts)
    monkeypatch.setattr(detector,'REPO',tmp_path)
    monkeypatch.setattr(detector,'model_pins',lambda p:{'model':'fixed'})
    monkeypatch.setattr(local_api,'snapshot',lambda:dict(free_MiB=10000))
    class Batch(dict):
        def to(self,device):return self
    class Tokenizer:
        def __call__(self,texts,**kwargs):
            assert kwargs['max_length']==512 and kwargs['truncation']
            return Batch(input_ids=torch.zeros((len(texts),1)))
    class Model:
        def to(self,device):assert device=='cuda';return self
        def eval(self):return self
        def __call__(self,**kw):return SimpleNamespace(logits=torch.tensor([[5.,0.],[0.,5.]]))
    monkeypatch.setattr(AutoTokenizer,'from_pretrained',lambda *a,**k:Tokenizer())
    monkeypatch.setattr(AutoModelForSequenceClassification,'from_pretrained',lambda *a,**k:Model())
    card=dict(action='healing-strong-extension',args=dict(training='train',calibration='cal',rows='source.json'),wall_seconds=60)
    out=raw/'jobs/strong'
    worker.handle(card,out,raw,lambda:None)
    result=read(out/'PREDICTIONS.json')
    assert result['cuts']==cuts and {r['key'] for r in result['rows']}=={'human','machine'}
    assert not (tmp_path/'results/.gpu.lock').exists()
    monkeypatch.setattr(detector,'model_pins',lambda p:{'model':'changed'})
    with pytest.raises(ValueError,match='checkpoint changed'):worker.handle(card,raw/'jobs/refused',raw,lambda:None)


def test_complete_detector_consumer_pairing_and_missing_row(tmp_path,monkeypatch):
    from runners.stage13 import detectors,located
    raw=tmp_path/'healing';raw.mkdir()
    rows=[dict(key=f'{u}-{label}',unit=u,label=label,**{'matched-window-direct':.1,'reconstruction-feature-fusion':.9 if label else .1,'e5_probability':.2}) for u in ('a','b') for label in (0,1)]
    cuts={n:{'0.01':.5,'0.05':.5} for n in ('matched-window-direct','reconstruction-feature-fusion','released-e5')}
    selection=dict(models={n:{} for n in ('matched-window-direct','reconstruction-feature-fusion')},cuts=cuts,calibration={n:dict(temperature=1.) for n in cuts})
    freeze(tmp_path/'input.json',rows);freeze(tmp_path/'jobs/located/MODEL.json',{});freeze(tmp_path/'jobs/selection/SELECTION.json',selection)
    for name in ('core-v1-A-reserve-summary-g2r1','reserve-extension-v1-summary-g2r1'):
        freeze(tmp_path/'manifests'/f'{name}.json',dict(args=dict(rows='input.json',blocks=[],located='located',selection='selection')))
    monkeypatch.setattr(detectors,'merge_predictions',lambda rs,paths:deepcopy(rs))
    monkeypatch.setattr(located,'features',lambda rs,model:rs)
    models=iter(('matched-window-direct','reconstruction-feature-fusion'))
    # apply_linear receives empty fixtures; choose by deterministic call order.
    calls=[]
    def apply(model,rs):
        n=('matched-window-direct','reconstruction-feature-fusion')[len(calls)%2];calls.append(n);return [r[n] for r in rs]
    monkeypatch.setattr(detectors,'apply_linear',apply)
    base=tmp_path/'jobs/core-v1-roberta-evaluate-g2r1'
    strong=[dict(key=r['key'],unit=r['unit'],label=r['label'],roberta=.1) for r in rows]
    for r in strong:freeze(base/'rows'/f"{r['key']}.json",r)
    freeze(base/'CALIBRATION.json',{'0.01':.5,'0.05':.5})
    freeze(raw/'jobs/strong/PREDICTIONS.json',dict(rows=strong,cuts={'0.01':.5,'0.05':.5}))
    card=dict(action='healing-detector-comparison',args=dict(strong='strong'))
    worker.handle(card,raw/'jobs/summary',raw,lambda:None)
    result=read(raw/'jobs/summary/ANALYSIS.json')
    assert set(result['partitions'])=={'core','extension'}
    for p in result['partitions'].values():
        assert p['paired']['0.01/roberta']['estimates']['pooled_recall_gain']['mean']==1
        assert p['paired']['0.01/roberta']['estimates']['human_false_positive_difference']['mean']==0
    from runners.stage13.common import atomic
    atomic(raw/'jobs/strong/PREDICTIONS.json',dict(rows=strong[:-1],cuts={'0.01':.5,'0.05':.5}))
    with pytest.raises(ValueError,match='coverage differs'):worker.handle(card,raw/'jobs/refusal',raw,lambda:None)


def test_checkpoint_fixed_markers_and_exit(tmp_path,monkeypatch):
    from runners.stage13 import healing_checkpoints as cp
    freeze(tmp_path/'CONTRACT.json',{k:'2000-01-01T00:00:00+00:00' for k in ('reporting','final_review','deadline')})
    monkeypatch.setattr(cp,'limit_process',lambda:None)
    monkeypatch.setattr(cp,'native_identity',lambda:dict(pid=1,created_ticks=2,executable='fixture'))
    cp.run(tmp_path)
    for k in ('reporting','final_review','deadline','EXIT'):
        r=read(tmp_path/'checkpoints'/f'{k}.json');assert r['status']=='complete' and r['scientific_verdict'] is False


def test_complete_family_capacity_accepts_and_refuses(tmp_path):
    from runners.stage13.healing_prepare import capacity
    from runners.stage13.common import atomic
    freeze(tmp_path/'CONTRACT.json',dict(reporting='2099-01-01T00:00:00+00:00'))
    freeze(tmp_path/'jobs/pilot/COMPLETE.json',dict(wall_seconds=100))
    card=dict(args=dict(family='memory',pilot='pilot',blocks=['a','b']))
    assert capacity(card,tmp_path/'pass',tmp_path,lambda:None)['admitted'] is True
    atomic(tmp_path/'CONTRACT.json',dict(reporting='2000-01-01T00:00:00+00:00'))
    assert capacity(card,tmp_path/'fail',tmp_path,lambda:None)['admitted'] is False
