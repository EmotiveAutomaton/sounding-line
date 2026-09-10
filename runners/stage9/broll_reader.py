"""Public B-roll selection forecasts, with independent Bernoulli opportunities.

DESIGN CHECK: H03/X02/X04/X05; LESSONS 2--5. NULL: empty history reproduces
population predictions and a copied history cannot increase evidence. ALTERNATIVE:
a stable part-of-speech preference transfers to new words and wrong-person context
reverses it. No future selection, participant ID or script path enters this reader.
All rivals use the same commission, offered vocabulary and instructed budget.
"""
from collections import Counter
import hashlib,json,math,time,traceback

TAGS={'UNTAGGED','adj','adverb','noun','proper noun','verb'}
GOALS={'informative','entertaining'}
ARMS=('uniform','frequency','noun_adjective','commission','population_pos','population_word',
    'budget_only','person_pos','person_word')


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def stimulus(value):
    if not isinstance(value,dict) or set(value)!={'support','pos','counts'}:raise ValueError('only declared public script features permitted')
    words=value['support']
    if not isinstance(words,list) or not words or len(words)!=len(set(words)) or any(not isinstance(w,str) or not w for w in words):
        raise ValueError('complete unique normalized word support required')
    if set(value['pos'])!=set(words) or set(value['counts'])!=set(words):raise ValueError('script feature support differs')
    if any(v not in TAGS for v in value['pos'].values()):raise ValueError('unknown released part-of-speech tag')
    if any(type(v) is not int or v<1 for v in value['counts'].values()):raise ValueError('positive released word counts required')
    return words


def counts(value):
    if not isinstance(value,list) or len(value)!=2 or any(type(v) not in (float,int) or not math.isfinite(v) for v in value):
        raise ValueError('finite selected/opportunity counts required')
    if not 0<=value[0]<=value[1]:raise ValueError('invalid selection opportunity counts')
    return value


def validate_model(model):
    if set(model)!={'version','pos','words','global'} or model['version']!='broll-selection-rivals-v1':raise ValueError('unknown fitted B-roll model')
    if set(model['pos'])!=GOALS or set(model['words'])!=GOALS or set(model['global'])!=GOALS:raise ValueError('complete commission support required')
    for goal in GOALS:
        counts(model['global'][goal])
        if set(model['pos'][goal])!=TAGS:raise ValueError('complete fitted part-of-speech support required')
        for value in (*model['pos'][goal].values(),*model['words'][goal].values()):counts(value)


def forecasts(evidence,model):
    if set(evidence)!={'stimulus','commission','history'} or evidence['commission'] not in GOALS:
        raise ValueError('only current public stimulus, commission and earlier selection records permitted')
    validate_model(model);target=evidence['stimulus'];words=stimulus(target);goal=evidence['commission']
    selected_pos=Counter();total_pos=Counter();selected_word=Counter();total_word=Counter();seen={digest(target)}
    if not isinstance(evidence['history'],list):raise ValueError('explicit earlier history required')
    for row in evidence['history']:
        if set(row)!={'stimulus','selected'}:raise ValueError('private or unknown history fields')
        own=row['stimulus'];support=stimulus(own);ys=row['selected'];key=digest(own)
        if key in seen:raise ValueError('target or duplicate script in earlier history')
        seen.add(key)
        if len(ys)!=len(support) or any(type(y) is not int or y not in (0,1) for y in ys):raise ValueError('complete Bernoulli selection vector required')
        for word,y in zip(support,ys):
            tag=own['pos'][word];selected_pos[tag]+=y;total_pos[tag]+=1;selected_word[word]+=y;total_word[word]+=1
    chosen,total=model['global'][goal];global_p=(chosen+1)/(total+2)
    pos_p={tag:(v[0]+20*global_p)/(v[1]+20) for tag,v in model['pos'][goal].items()}
    history_total=sum(total_pos.values());budget=(sum(selected_pos.values())+20*global_p)/(history_total+20)
    weights={'uniform':[1.]*len(words),'frequency':[target['counts'][w] for w in words],
        'noun_adjective':[1. if target['pos'][w] in ('noun','proper noun','adj') else .02 for w in words]}
    output={arm:[min(1.,17.5*w/sum(values)) for w in values] for arm,values in weights.items()}
    output.update({arm:[] for arm in ARMS if arm not in output})
    for word in words:
        tag=target['pos'][word];p=pos_p[tag];n,m=model['words'][goal].get(word,[0.,0.]);lexical=(n+20*p)/(m+20)
        values={'commission':global_p,'population_pos':p,'population_word':lexical,'budget_only':budget,
            'person_pos':(selected_pos[tag]+20*p)/(total_pos[tag]+20),
            'person_word':(selected_word[word]+20*lexical)/(total_word[word]+20)}
        for arm,value in values.items():output[arm].append(value)
    if set(output)!=set(ARMS) or any(len(v)!=len(words) or any(not math.isfinite(p) or not 0<=p<=1 for p in v) for v in output.values()):
        raise ValueError('incomplete or invalid Bernoulli forecasts')
    return output


def run(evidence,task):
    if set(task)!={'operation','parameters','parameters_sha256','information_sha256'} or task['operation']!='broll_selection_models':
        raise ValueError('explicit ordinary selection operation required')
    if task['parameters_sha256']!=digest(task['parameters']) or task['information_sha256']!=digest(evidence):raise ValueError('changed model or evidence')
    return {'valid':True,'probabilities':forecasts(evidence,task['parameters']),'parameters_sha256':task['parameters_sha256'],
        'scope':'recorded word-type selection probabilities; no mutually exclusive normalization or unobserved imagery claim'}


def main():
    from . import base
    start=time.monotonic()
    try:
        with open('task.json',encoding='utf-8') as f:task=json.load(f)
        if task.get('probe'):base.save('receipt',base.probe(task));return 0
        with open('evidence.json',encoding='utf-8') as f:evidence=json.load(f)
        base.save('prediction',run(evidence,task));base.save('receipt',{'valid':True,'wall_seconds':time.monotonic()-start,'loaded_sources':base.loaded_sources()})
        return 0
    except Exception:
        base.save('error',{'valid':False,'traceback':traceback.format_exc()});return 1
