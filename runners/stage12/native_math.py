"""Reviewed Ghost V19 numeric interface; frozen weights, no fitting.

DESIGN CHECK: LESSONS 3-5; CONTROLS 3,6. NULL: no-op and native reference
agree; constant heads cannot show selective effects. ALTERNATIVE: changed
weights, leaked evaluator inputs or unsupported architectures fail admission.
This port is not an independent implementation of the native world. Complete
source archives and per-function provenance are bound by the consumer plan.
"""
from collections import defaultdict
from itertools import product
import hashlib,json
import numpy as np
from scipy.special import erf

MAKERS=tuple(product(range(2),repeat=4))
GOALS=('meaning','dependency','presentation')
CONTEXTS=tuple(dict(initial=list(a),requested_purpose=b) for a in ((0,1,0),(1,0,1)) for b in (0,1))

def rng(*parts):
    value=json.dumps(('v18.3',*parts),sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return np.random.default_rng(int(hashlib.sha256(value).hexdigest()[:16],16))


# Reviewed source: local_world.py sha256=0c19e29c776756057fb218247f1a279c78edd7f7f6b94a13226127b97776f7ae

def law(lineage):
    random=rng('v19-local-world',lineage)
    return dict(lineage=lineage,goal_strength=float(random.uniform(.8,1.2)),
        action_rate=float(random.uniform(.65,.85)),routine_strength=float(random.uniform(.1,.3)))


def execute(artifact,previous,operation,maker):
    purpose,skill,belief,routine=maker
    a=list(artifact)
    if operation=='edit-claim':a[0]=1-a[0]
    elif operation=='repair-evidence':a[1]=(a[0]^belief) if skill else 1-a[1]
    elif operation=='replace-presentation':a[2]=1-a[2]
    elif operation=='accept-tool':
        if not skill:raise ValueError('unreachable tool use')
        a[0]=1-a[0];a[1]=a[0]  # tool proposal flips claim and repairs its dependent evidence
    elif operation=='undo':a=list(previous)
    elif operation!='inspect':raise ValueError('unknown operation')
    return tuple(a)


def choices(world,maker,artifact,step,context):
    purpose,skill,belief,routine=maker
    perceived=artifact[0]^belief
    strengths=np.array([1.5 if purpose==0 else .6,1.4 if perceived!=artifact[1] else .5,1.8 if purpose==1 else .5])
    strengths[2 if routine else 0]+=world['routine_strength']
    strengths[2 if context['requested_purpose'] else 0]+=.2  # a request need not be adopted
    strengths=np.power(strengths,world['goal_strength']);strengths/=strengths.sum()
    for goal,weight in zip(GOALS,strengths):
        action={'meaning':'accept-tool' if skill else 'edit-claim','dependency':'repair-evidence','presentation':'replace-presentation'}[goal]
        alternative='undo' if goal=='dependency' and step==2 else 'inspect'
        yield goal,action,float(weight*world['action_rate'])
        yield goal,alternative,float(weight*(1-world['action_rate']))


def enumerate_world(world):
    records=[]
    for context_index,context in enumerate(CONTEXTS):
        for maker_index,maker in enumerate(MAKERS):
            def visit(artifact,previous,steps,probability):
                if len(steps)==3:
                    records.append(dict(context_index=context_index,maker_index=maker_index,maker=list(maker),
                        initial=context['initial'],requested_purpose=context['requested_purpose'],
                        final=list(artifact),steps=steps,probability=probability/len(MAKERS)/len(CONTEXTS)))
                    return
                step=len(steps)
                for goal,operation,weight in choices(world,maker,artifact,step,context):
                    after=execute(artifact,previous,operation,maker)
                    event=dict(step=step,goal=goal,operation=operation,before=list(artifact),after=list(after),undo_buffer=list(previous),
                        dependency_edges=[[0,1]],tool_proposal=list(after) if operation=='accept-tool' else None,
                        perceived_claim=artifact[0]^maker[2])
                    visit(after,artifact,steps+[event],probability*weight)
            visit(tuple(context['initial']),tuple(context['initial']),[],1.)
    return records


# Reviewed source: interchange_fixtures.py sha256=efcf452c3f91347c84f1c089e2ad71332380cd81d825842d6a347fd10afc315f

def endpoint_law(world, maker, context):
    initial=tuple(context['initial']); mass={(initial, initial):1.}
    for step in range(3):
        following=defaultdict(float)
        for (artifact, previous), weight in mass.items():
            for _, operation, probability in choices(world,maker,artifact,step,context):
                after=execute(artifact,previous,operation,maker)
                following[after,artifact]+=weight*probability
        mass=following
    result=np.zeros(8)
    for (artifact,_),weight in mass.items():result[artifact[0]+artifact[1]*2+artifact[2]*4]+=weight
    return result


def softmax(x):
    exp=np.exp(x-x.max(-1,keepdims=True));return exp/exp.sum(-1,keepdims=True)


def decode(parameters,state):
    p=softmax((state@parameters['head.weight'].T+parameters['head.bias']).reshape(*state.shape[:-1],4,8))
    if not np.isfinite(p).all() or np.any(p<=0):raise ValueError('invalid probability')
    return p


def final_normalize(parameters,state):
    return ((state-state.mean(-1,keepdims=True))/np.sqrt(state.var(-1,keepdims=True)+1e-5)
        *parameters['encoder.norm2.weight']+parameters['encoder.norm2.bias'])


def reconstruct(parameters,codes,novel,kind,site='final'):
    # Double-precision reconstruction of the fixed final state; no Torch fitting.
    if site not in ('final','pre-final-normalization') or (site!='final' and kind!='transformer'):
        raise ValueError('unadmitted intervention site')
    if (codes.ndim!=2 or codes.dtype.kind not in 'iu' or novel.shape!=codes.shape
            or novel.dtype.kind!='b' or not codes.size):
        raise ValueError('invalid public sequence schema')
    if any(not np.isfinite(v).all() for v in parameters.values()):
        raise ValueError('nonfinite model parameter')
    a={k:v.astype(float) for k,v in parameters.items()};n,t=codes.shape
    if t!=32 or codes.min()<0 or codes.max()>31:raise ValueError('invalid observed stream')
    tokens=np.full((n,33),32);positions=np.cumsum(novel,axis=1)
    for i in range(n):tokens[i,1:1+sum(novel[i])]=codes[i,novel[i]]
    x=a['embedding.weight'][tokens]
    def linear(z,key):return z@a[key+'.weight'].T+a[key+'.bias']
    if kind=='recurrent':
        h=np.zeros((n,38));hidden=[]
        for j in range(33):
            ir,iz,iv=np.split(x[:,j]@a['encoder.weight_ih_l0'].T+a['encoder.bias_ih_l0'],3,-1)
            hr,hz,hv=np.split(h@a['encoder.weight_hh_l0'].T+a['encoder.bias_hh_l0'],3,-1)
            reset=1/(1+np.exp(-(ir+hr)));update=1/(1+np.exp(-(iz+hz)))
            h=(1-update)*np.tanh(iv+reset*hv)+update*h;hidden.append(h.copy())
        h=np.stack(hidden,1)
    elif kind=='transformer':
        x=x+a['positions'];q,k,v=np.split(x@a['encoder.self_attn.in_proj_weight'].T+a['encoder.self_attn.in_proj_bias'],3,-1)
        def heads(z):return z.reshape(n,33,4,8).transpose(0,2,1,3)
        q,k,v=map(heads,(q,k,v));scores=q@k.transpose(0,1,3,2)/np.sqrt(8)
        scores=np.where(np.triu(np.ones((33,33),bool),1),-np.inf,scores)
        attention=(softmax(scores)@v).transpose(0,2,1,3).reshape(n,33,32)
        def norm(z,key):return (z-z.mean(-1,keepdims=True))/np.sqrt(z.var(-1,keepdims=True)+1e-5)*a[key+'.weight']+a[key+'.bias']
        h=norm(x+linear(attention,'encoder.self_attn.out_proj'),'encoder.norm1')
        f=linear(h,'encoder.linear1');f=.5*f*(1+erf(f/np.sqrt(2)))
        pre=h+linear(f,'encoder.linear2')
        h=pre if site=='pre-final-normalization' else norm(pre,'encoder.norm2')
    else:raise ValueError('unadmitted saved architecture')
    state=h[np.arange(n)[:,None],positions]
    return state,decode(a,final_normalize(a,state) if site=='pre-final-normalization' else state)


def loss(target,pred):
    logs=np.zeros_like(pred);np.log(pred,out=logs,where=pred>0)
    value=-(target*logs).sum(-1)
    return np.where(np.any((target>0)&(pred<=0),axis=-1),np.inf,value)


def arrays(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}
