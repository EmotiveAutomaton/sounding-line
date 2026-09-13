"""Project-balanced training stumps and concrete revision episodes.

DESIGN CHECK: Stage 10 R1/R4 storage comparison and LESSONS2-5. Constant/noisy
training can retain an empty library. A repeatable feature boundary may compress
across projects. Only training labels select rules; whole episodes stay intact.
Names are grounded in definitions, never withheld labels or actual personal goals.
"""
from collections import Counter, defaultdict
import math
from . import revision_programs as programs
from .contracts import canonical, digest
from .reader import from_record, tokens

STORE_BYTES=6000


def joined(training, answers):
    truth={r['task_id']:r for r in answers}
    if len(truth)!=len(answers) or set(truth)!={r['task_id'] for r in training} or len(truth)!=len(training):
        raise ValueError('training join is not one to one')
    rows=[]
    for record in training:
        task=from_record(record);answer=truth[task.task_id]
        description=dict(task.choices).get(answer['correct_choice'])
        action=next((k for k,v in programs.descriptions(task).items() if v==description),None)
        if action is None or not answer.get('writer_component') or not answer.get('source_event'):
            raise ValueError('missing training label/project/boundary')
        rows.append({'record':record,'task':task,'action':action,'group':answer['writer_component'],
                     'event':answer['source_event'],'features':programs.features(task)})
    return rows


def induce(training, answers):
    rows=joined(training,answers);buckets=defaultdict(list);libraries={}
    for row in rows:buckets[canonical([row['task'].family,row['task'].evidence_view])].append(row)
    for key,own in buckets.items():
        if len({r['event'] for r in own})!=len(own):raise ValueError('duplicated training boundary within a target/view')
        counts=Counter(r['group'] for r in own);weights=[1/(len(counts)*counts[r['group']]) for r in own]
        actions=programs.descriptions(own[0]['task'])
        baseline=min(sum(w for r,w in zip(own,weights) if r['action']!=a) for a in actions)
        candidates=[]
        for feature in sorted(set(programs.FEATURES)-{'constant'}):
            values=sorted({r['features'][feature] for r in own})
            boundaries=[(a+b)/2 for a,b in zip(values,values[1:])]
            if len(boundaries)>16:boundaries=[boundaries[i*(len(boundaries)-1)//15] for i in range(16)]
            for threshold in boundaries:
                partitions=[[i for i,r in enumerate(own) if (r['features'][feature]<threshold)==below] for below in [True,False]]
                if any(len({own[i]['group'] for i in part})<2 for part in partitions):continue
                predicted=[min(actions,key=lambda a:(sum(weights[i] for i in part if own[i]['action']!=a),a)) for part in partitions]
                if predicted[0]==predicted[1]:continue
                loss=sum(weights[i] for part,a in zip(partitions,predicted) for i in part if own[i]['action']!=a)
                if loss>=baseline:continue
                p={'feature':feature,'threshold':threshold,'below':predicted[0],'otherwise':predicted[1]}
                programs.validate(p,own[0]['task'])
                candidates.append({'program':p,'training_loss':loss,'training_projects':len(counts),
                    'definition':f"If {feature} is below {threshold:g}, predict {predicted[0]}; otherwise {predicted[1]}."})
        selected=[];seen=set()
        for candidate in sorted(candidates,key=lambda c:(c['training_loss'],canonical(c['program']))):
            if candidate['program']['feature'] in seen:continue
            seen.add(candidate['program']['feature']);selected.append(candidate)
            if len(selected)==3:break
        libraries[key]=selected
    return {'training_sha256':digest(training),'answers_sha256':digest(answers),'libraries':libraries,
            'rule': 'training error below best constant; each branch supported by at least two projects',
            'maximum_representation_bytes':STORE_BYTES,'scope':'training compression only; predictive comparison remains separate'}


def representation(task, training, answers, library, *, procedures, naming='grounded', fits=lambda value: True):
    if library['training_sha256']!=digest(training) or library['answers_sha256']!=digest(answers):
        raise ValueError('training library source changed')
    key=canonical([task.family,task.evidence_view]);rules=library['libraries'][key] if procedures else []
    named=[{'name':f'procedure_{i+1}', 'grounded_name':r['definition'], 'program':r['program'],
            'training_projects':r['training_projects']} for i,r in enumerate(rules)]
    payload={'procedures':named,'episodes':[]}
    scored=[];target=tokens(task.evidence);target_norm=math.sqrt(sum(x*x for x in target.values()))
    truth={r['task_id']:r for r in answers}
    for record in training:
        source=from_record(record)
        if source.family!=task.family or source.evidence_view!=task.evidence_view:continue
        if source.task_id==task.task_id:raise ValueError('target leaked into training representation')
        count=tokens(source.evidence);denom=target_norm*math.sqrt(sum(x*x for x in count.values()))
        similarity=sum(v*count.get(k,0) for k,v in target.items())/denom if denom else 0
        example={'evidence':source.evidence,'observed_outcome':dict(source.choices)[truth[source.task_id]['correct_choice']]}
        scored.append((-similarity,source.task_id,example))
    ids=[];skipped=[]
    for _,identifier,example in sorted(scored):
        proposal={**payload,'episodes':[*payload['episodes'],example]}
        if len(canonical(proposal).encode('utf8'))>STORE_BYTES or not fits(proposal):
            skipped.append(identifier);continue
        payload=proposal;ids.append(identifier)
        if len(ids)==2:break
    if not ids:raise ValueError('no whole training episode fits common representation allowance')
    if naming=='opaque':
        payload={**payload,'procedures':[{k:v for k,v in r.items() if k!='grounded_name'} for r in payload['procedures']]}
    elif naming!='grounded':raise ValueError('undeclared naming comparison')
    return payload,{'selected_training_ids':ids,'skipped_training_ids':skipped,'library_sha256':digest(library),
                    'maximum_bytes':STORE_BYTES,'bytes':len(canonical(payload).encode('utf8')),
                    'selection_sizes_against_grounded_names_for_both_conditions':True}
