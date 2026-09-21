"""Single-owner controlled tiny reader and bounded causal consumer.

DESIGN CHECK: LESSONS 3-5; THREE_COGNITIVE_LAYERS causal gate. NULL: a constant
or incapable reader cannot license an intervention result. ALTERNATIVE: correct
interchange must be judged against random, shuffled, wrong-variable, no-op and
full-state controls. Fitting uses training examples; intervention fitting uses
development pairs only. Test labels never select architecture, rank or dose.
The Ghost export and both owner receipts are prerequisites, not invented data.
"""
from collections import Counter,defaultdict
import json
from pathlib import Path
import random
import statistics
import time
from .common import read,freeze,atomic,digest,filehash,own_cpu

HEADS={'operation':6,'local_goal':3}
RECIPE=dict(hidden=32,embedding=16,epochs=20,batch_size=64,learning_rate=.001,seed=120921,
            alignment_rank=1,alignment_epochs=20,alignment_lr=.01,dose=1.)


def create(recipe):
    import torch
    class TinyReader(torch.nn.Module):
        def __init__(self):
            super().__init__();self.embedding=torch.nn.Embedding(257,recipe['embedding'],padding_idx=256)
            self.gru=torch.nn.GRU(recipe['embedding'],recipe['hidden'],batch_first=True)
            self.heads=torch.nn.ModuleDict({k:torch.nn.Linear(recipe['hidden'],n) for k,n in HEADS.items()})
        def encode(self,tokens,lengths):
            packed=torch.nn.utils.rnn.pack_padded_sequence(self.embedding(tokens),lengths.cpu(),batch_first=True,enforce_sorted=False)
            _,h=self.gru(packed);return h[-1]
        def decode(self,h):return {k:layer(h) for k,layer in self.heads.items()}
        def forward(self,tokens,lengths):return self.decode(self.encode(tokens,lengths))
    return TinyReader()


def tokens(public):
    # Exact public allowlist is the source's, including nested observations.
    allowed={'schema','tier','inputs'}
    if set(public)!=allowed or public['schema']!='v19.local.public.1':raise ValueError('tiny reader needs a Ghost public projection')
    tier=public['tier'];fields={'artifact'}
    if tier!='E0':fields|={'initial','requested_purpose'}
    if tier in ('E2-sparse','E2-full'):fields.add('observations')
    if tier=='E1-corrected':fields.add('reports')
    if tier not in ('E0','E1','E2-sparse','E2-full','E1-corrected') or set(public['inputs'])!=fields:raise ValueError('hidden or missing public input')
    def bits(value):return isinstance(value,list) and len(value)==3 and all(type(x) is int and x in (0,1) for x in value)
    if not bits(public['inputs']['artifact']):raise ValueError('invalid finite artifact')
    if tier!='E0' and (not bits(public['inputs']['initial']) or type(public['inputs']['requested_purpose']) is not int or public['inputs']['requested_purpose'] not in (0,1)):
        raise ValueError('invalid finite context')
    for e in public['inputs'].get('observations',[]):
        if set(e)!={'step','operation','before','after','tool_proposal'}:raise ValueError('evaluator field in tiny observations')
        if type(e['step']) is not int or e['step'] not in (0,1,2) or e['operation'] not in ('edit-claim','repair-evidence','replace-presentation','accept-tool','inspect','undo'):
            raise ValueError('invalid finite operation')
        if not bits(e['before']) or not bits(e['after']) or (e['tool_proposal'] is not None and not bits(e['tool_proposal'])):raise ValueError('invalid finite observation state')
    for report in public['inputs'].get('reports',[]):
        if set(report)!={'status','requested_purpose'} or report['status'] not in ('retracted','correction') or type(report['requested_purpose']) is not int or report['requested_purpose'] not in (0,1):raise ValueError('invalid finite report')
    encoded=list(json.dumps(public,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode())
    if not encoded or len(encoded)>1024:raise ValueError('tiny sequence outside declared support')
    return encoded


def batch(rows):
    import torch
    values=[tokens(r['public']) for r in rows];lengths=torch.tensor([len(x) for x in values])
    x=torch.full((len(rows),int(lengths.max())),256,dtype=torch.long)
    for i,v in enumerate(values):x[i,:len(v)]=torch.tensor(v)
    return x,lengths


def loss(logits,targets):
    import torch
    return sum(-(targets[k]*torch.log_softmax(v,dim=-1)).sum(-1).mean() for k,v in logits.items())/len(HEADS)


def target_batch(rows,labels):
    import torch
    from .common import distribution
    result={}
    for k,n in HEADS.items():
        values=[labels[r['id']][k] for r in rows]
        if not all(distribution(v,[1.]+[0.]*(n-1))['valid'] for v in values):raise ValueError('invalid finite tiny target')
        result[k]=torch.tensor(values,dtype=torch.float32)
    return result


def evaluate(model,rows,labels,pulse=lambda **k:None):
    import torch
    from .common import distribution
    result=[]
    model.eval()
    with torch.no_grad():
        for start in range(0,len(rows),64):
            pulse(phase='tiny-development-evaluation',completed=start,total=len(rows))
            own=rows[start:start+64];pred=model(*batch(own));target_batch(own,labels)
            for i,r in enumerate(own):
                for k in HEADS:
                    p=torch.softmax(pred[k][i],-1).tolist();truth=labels[r['id']][k]
                    result.append(dict(id=r['id'],lineage=r['lineage'],head=k,p=p,truth=truth,
                        modal_class=max(range(len(truth)),key=truth.__getitem__),**distribution(p,truth)))
    return result


def capability(rows):
    result={}
    for head,n in HEADS.items():
        selected=[r for r in rows if r['head']==head];counts=Counter(r['modal_class'] for r in selected)
        per_class={c:statistics.mean(r['accuracy'] for r in selected if r['modal_class']==c) for c in counts}
        # A valid probability target need not make every rare operation modal.
        # Require varied modal answers, then check the full distribution too.
        covered=len(counts)>=2 and min(counts.values(),default=0)>=10
        balanced=statistics.mean(per_class.values()) if per_class else 0
        tv=statistics.mean(sum(abs(p-t) for p,t in zip(r['p'],r['truth']))/2 for r in selected) if selected else 1
        result[head]=dict(class_counts=dict(counts),balanced_modal_agreement=balanced,
                          mean_total_variation=tv,admitted=covered and balanced>=.8 and tv<=.1,coverage_sufficient=covered)
    return dict(admitted=all(r['admitted'] for r in result.values()),heads=result,
                scope='finite task capability only; ambiguity and generator dependence retained')


def validate_owner(card,recipe):
    receipts=[read(p) for p in card['owner_receipts']]
    if {r['project'] for r in receipts}!={'Sounding Line','Ghost'}:raise ValueError('both project owner receipts required')
    if any(r.get('training_owner')!='Sounding Line' or r.get('combined_settings_maximum')!=2 or r.get('status')!='accepted' for r in receipts):
        raise ValueError('shared owner or setting ceiling not accepted')
    if len({r['source_roster_sha256'] for r in receipts})!=1 or receipts[0]['source_roster_sha256']!=filehash(card['dataset_manifest']):
        raise ValueError('shared training roster not identical')
    if any(r.get('recipe_sha256')!=digest(recipe) for r in receipts):raise ValueError('shared recipe not identical')


def dataset(card,include_test=False):
    path=Path(card['dataset_manifest']);manifest=read(path)
    if manifest['schema']!='ghost.shared-tiny.1':raise ValueError('unrecognized shared training dataset')
    for name,h in manifest['files'].items():
        if filehash(path.parent/name)!=h:raise ValueError('shared dataset bytes differ')
    examples={k:read(path.parent/manifest['splits'][k]['public']) for k in ('train','development','test')}
    # Hashes and public split identities may be audited before fitting. Test
    # target payloads are not opened by a fit or development gate.
    labels={k:{r['id']:r for r in read(path.parent/manifest['splits'][k]['evaluator'])}
            for k in examples if include_test or k!='test'}
    lineages={k:{r['lineage'] for r in v} for k,v in examples.items()}
    for a,b in [('train','development'),('train','test'),('development','test')]:
        if lineages[a]&lineages[b]:raise ValueError('coefficient lineage crosses tiny splits')
    for k,values in examples.items():
        if not values or len({r['id'] for r in values})!=len(values) or (k in labels and set(labels[k])!={r['id'] for r in values}):raise ValueError('tiny source/evaluator roster mismatch')
        for r in values:tokens(r['public'])
    return examples,labels,manifest


def fit(out,card,pulse,raw):
    raise RuntimeError('Ghost is the designated shared fit/accounting owner; no Sounding Line fit dispatch')


def _retained_unadmitted_fit(out,card,pulse,raw):
    import torch
    from tools.codex_common import singleton
    recipe=dict(RECIPE,**card.get('recipe',{}));validate_owner(card,recipe);examples,labels,manifest=dataset(card)
    if recipe['seed'] not in (120921,120922):raise ValueError('undeclared shared setting')
    torch.set_num_threads(1);torch.manual_seed(recipe['seed']);model=create(recipe)
    from runners.stage9.process_identity import native_identity
    setting=raw/'shared-tiny'/('setting-'+str(recipe['seed'])+'.json');resume=card.get('resume_from')
    with singleton(raw/'locks/shared-tiny-settings.lock'):
        prior=list((raw/'shared-tiny').glob('setting-*.json'))
        if resume:
            previous=read(setting)
            if previous['status']!='started' or previous['recipe']!=recipe:raise ValueError('not an interrupted identical setting')
            actual=native_identity(previous['native']['pid'])
            if actual is not None:raise ValueError('previous setting owner is live or PID reused; inspect before resume')
        elif setting.exists() or len(prior)>=2:raise ValueError('shared setting consumed; no blind repeat')
        state=dict(status='started',owner='Sounding Line',recipe=recipe,source_manifest_sha256=filehash(card['dataset_manifest']),native=native_identity(),job=card['id'])
        if resume:atomic(setting,state)
        else:freeze(setting,state)
    opt=torch.optim.Adam(model.parameters(),lr=recipe['learning_rate']);rng=random.Random(recipe['seed']);history=[]
    first_epoch=0
    if resume:
        if not Path(resume).resolve().is_relative_to(raw.resolve()):raise ValueError('checkpoint outside owned stage')
        saved=torch.load(resume,map_location='cpu',weights_only=True)
        if saved['recipe']!=recipe or saved['source_sha256']!=filehash(card['dataset_manifest']) or saved['implementation_sha256']!=filehash(__file__):
            raise ValueError('checkpoint recipe, source or implementation differs')
        model.load_state_dict(saved['model']);opt.load_state_dict(saved['optimizer']);torch.set_rng_state(saved['torch_rng']);rng.setstate(saved['python_rng'])
        first_epoch=saved['epoch']+1;history=list(saved['history'])+[dict(epoch=saved['epoch'],mean_loss=saved['epoch_mean_loss'],checkpoint_sha256=filehash(resume))]
        checkpoint=Path(resume)
    train=examples['train']
    for epoch in range(first_epoch,recipe['epochs']):
        model.train();order=list(range(len(train)));rng.shuffle(order);epoch_losses=[]
        for start in range(0,len(order),recipe['batch_size']):
            pulse(phase='shared-tiny-fit',epoch=epoch,batch=start//recipe['batch_size'])
            rows=[train[i] for i in order[start:start+recipe['batch_size']]];opt.zero_grad()
            value=loss(model(*batch(rows)),target_batch(rows,labels['train']))
            if not torch.isfinite(value):raise ValueError('tiny numerical fit failure')
            value.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.);opt.step();epoch_losses.append(float(value.detach()))
        checkpoint=out/f'epoch-{epoch:02d}.pt'
        torch.save(dict(model=model.state_dict(),optimizer=opt.state_dict(),torch_rng=torch.get_rng_state(),
            python_rng=rng.getstate(),recipe=recipe,epoch=epoch,history=history,epoch_mean_loss=statistics.mean(epoch_losses),
            implementation_sha256=filehash(__file__),source_sha256=filehash(card['dataset_manifest'])),checkpoint)
        history.append(dict(epoch=epoch,mean_loss=statistics.mean(epoch_losses),checkpoint_sha256=filehash(checkpoint)))
    development=evaluate(model,examples['development'],labels['development'],pulse);gate=capability(development)
    freeze(out/'TRAINING.json',history);freeze(out/'DEVELOPMENT.json',development);freeze(out/'CAPABILITY.json',gate)
    freeze(out/'MODEL.json',dict(recipe=recipe,checkpoint=str(checkpoint),checkpoint_sha256=filehash(checkpoint),
        dataset_manifest=card['dataset_manifest'],dataset_manifest_sha256=filehash(card['dataset_manifest']),torch_version=torch.__version__))
    atomic(setting,dict(state,status='complete',capability=gate['admitted']))
    if gate['admitted']:freeze(out/'MODEL_READY.json',dict(status='complete',model_sha256=filehash(out/'MODEL.json'),scope=gate['scope']))
    return dict(status='complete',kind='scientific',capability=gate,settings_consumed=1,
        scope='one shared tiny setting; no intervention result or human mechanism claim',
        controls=dict(no_test_selection=True,separate_lineages=True,public_features_only=True,checkpoints_retained=True),
        files={n:filehash(out/n) for n in ('TRAINING.json','DEVELOPMENT.json','CAPABILITY.json','MODEL.json')})


def fit_basis(model,pairs,rank,seed,shuffle=False,pulse=lambda **k:None):
    import torch
    from runners.stage11_2.alignment import interchange
    torch.manual_seed(seed);q=torch.nn.Parameter(torch.randn(model.gru.hidden_size,rank)*.02)
    opt=torch.optim.Adam([q],lr=.01);targets=[p['counterfactual'] for p in pairs]
    if shuffle:random.Random(seed).shuffle(targets)
    for epoch in range(RECIPE['alignment_epochs']):
        for index,(row,target) in enumerate(zip(pairs,targets)):
            if index%32==0:pulse(phase='development-only-alignment',epoch=epoch,pair=index)
            opt.zero_grad();basis=torch.linalg.qr(q,mode='reduced')[0]
            changed=interchange(row['base'],row['donor'],basis)
            value=loss(model.decode(changed),{k:torch.tensor([target[k]],dtype=torch.float32) for k in HEADS})
            value.backward();opt.step()
    return torch.linalg.qr(q.detach(),mode='reduced')[0]


def causal(out,card,pulse,raw):
    import torch
    from runners.stage11_2.alignment import interchange
    from .common import distribution
    source=raw/'jobs'/card['fit_card'];gate=read(source/'CAPABILITY.json')
    if gate.get('admitted') is not True:raise ValueError('actual tiny capability gate failed')
    record=read(source/'MODEL.json');checkpoint=Path(record['checkpoint'])
    if filehash(checkpoint)!=record['checkpoint_sha256']:raise ValueError('fitted checkpoint differs')
    saved=torch.load(checkpoint,map_location='cpu',weights_only=True);model=create(record['recipe']);model.load_state_dict(saved['model']);model.eval()
    for parameter in model.parameters():parameter.requires_grad_(False)
    paired=read(card['pairs']);cache={}
    for split in ('development','test'):
        cache[split]=[]
        for row in paired[split]:
            hidden={}
            with torch.no_grad():
                for name in ('base','donor','wrong_variable'):
                    hidden[name]=model.encode(*batch([{'public':row[name]}])).detach()
            cache[split].append(dict(row,**hidden))
    if {r['lineage'] for r in cache['development']}&{r['lineage'] for r in cache['test']}:raise ValueError('causal lineage crossover')
    if not cache['development'] or not cache['test']:raise ValueError('empty causal comparison')
    pulse(phase='development-only-alignment')
    learned=fit_basis(model,cache['development'],1,120921,pulse=pulse);shuffled=fit_basis(model,cache['development'],1,120922,True,pulse)
    torch.manual_seed(120921);random_basis=torch.linalg.qr(torch.randn_like(learned),mode='reduced')[0]
    torch.save(dict(learned=learned,shuffled=shuffled,random=random_basis),out/'BASIS.pt')
    results=[]
    for i,row in enumerate(cache['test']):
        pulse(phase='all-causal-controls',completed=i,total=len(cache['test']))
        h,d=row['base'],row['donor'];intended=interchange(h,d,learned)-h
        deltas=dict(correct=intended,random=interchange(h,d,random_basis)-h,
            shuffled=interchange(h,d,shuffled)-h,wrong_variable=row['wrong_variable']-h,noop=torch.zeros_like(h),full_state=d-h)
        for name in ('random','shuffled','wrong_variable'):
            deltas[name]=deltas[name]*intended.norm()/deltas[name].norm().clamp_min(1e-12)
        if not torch.equal(interchange(h,d,learned,alpha=0),h):raise ValueError('no-op intervention changed state')
        for name,delta in deltas.items():
            pred=model.decode(h+delta)
            for head in HEADS:
                p=torch.softmax(pred[head][0],-1).tolist()
                results.append(dict(id=row['id'],lineage=row['lineage'],arm=name,head=head,
                    counterfactual=distribution(p,row['counterfactual'][head]),ordinary=distribution(p,row['ordinary'][head]),
                    intervention_norm=float(delta.norm()),off_manifold='not established absent; controls and ordinary-task damage reported'))
    freeze(out/'ROWS.json',results)
    return dict(status='complete',kind='scientific',rows=len(results),test_lineages=len({r['lineage'] for r in results}),
        scope='finite learned-reader interchange; selectivity requires complete control comparison, not a congruent-arm score',
        controls=dict(capability_passed=True,development_only_alignment=True,all_six_controls=True,no_op_exact=True,frozen_model=True),
        files={'ROWS.json':filehash(out/'ROWS.json'),'BASIS.pt':filehash(out/'BASIS.pt')})
