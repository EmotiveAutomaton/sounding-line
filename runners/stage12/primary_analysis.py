"""Complete S-P1 analysis and explicit pre-inference statistical annotations.

DESIGN CHECK: LESSONS 2-5. NULL: equal arms have zero paired contrast; invalid
rows retain their denominator and zero-support log loss remains infinite.
ALTERNATIVE: complete paired probabilities can support a descriptive contrast.
Shared prompts and writer/text links do not become independent events. A small
dependency graph cannot license a population interval or a general method rank.
"""
from collections import defaultdict
import json
import math
import statistics
from .common import read,freeze,filehash,distribution


def dependency_groups(rows):
    parent={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for row in rows:
        a=find('writer:'+row['writer_component']);b=find('prompt:'+row['prompt_component']);parent[a]=b
    return {r['id']:find('writer:'+r['writer_component']) for r in rows}


def freeze_analysis(out,card,pulse,raw):
    primary=raw/'jobs'/card['primary_card'];rows=read(primary/'EVALUATOR_ONLY.json')
    protocol=read(primary/'S-P1.json');groups=dependency_groups(rows)
    original=read(primary/'READER_INPUTS.json');population=read(raw/'jobs'/card['population_card']/'POPULATION.json')
    labels=original[0]['labels'];train=population['train'];by=defaultdict(list)
    for r in train:by[r['unit']].append(r)
    counts=[1.]*len(labels)
    for values in by.values():
        for r in values:counts[labels.index(r['truth'])]+=1/len(values)
    prior=[v/sum(counts) for v in counts]
    plan=dict(schema='s12.primary-analysis.1',source_protocol_sha256=filehash(primary/'S-P1.json'),
        reader_inputs_sha256=filehash(primary/'READER_INPUTS.json'),source_evaluator_sha256=filehash(primary/'EVALUATOR_ONLY.json'),
        original_requests_unchanged=True,primary='writer-balanced paired half-Brier: no history minus own history',
        sensitivity_name_correction='2.8*SD/sqrt(n) is approximate detectable difference, not confidence-interval half-width',
        meaningful_margin=protocol['meaningful_margin'],writer_components=len({r['writer_component'] for r in rows}),
        prompt_components=len({r['prompt_component'] for r in rows}),dependency_components=len(set(groups.values())),
        inference='descriptive writer sensitivity only; no population interval from sparse connected components',
        aggregation='average events within session, sessions within writer component, then equal writer components',
        calibration='five fixed confidence bins on valid forecasts; invalid fraction reported separately; event and writer summaries distinct',
        conditions=['own_history','no_history','matched_training_donor','training_prior','persistence','full_training_prior'],
        full_training_prior=prior,full_training_prior_scope='additional stronger cheap control from every eligible training event, component balanced, one pseudocount per class; original frozen prior retained as separate arm',
        multiplicity='one primary contrast; secondary comparisons descriptive, no p-values or selected-winner confirmation',
        labels=labels,rows=len(rows),new_model_results_inspected=False)
    freeze(out/'ANALYSIS_PLAN.json',plan);pulse(phase='prespecified-analysis-companion')
    return dict(status='complete',kind='infrastructure',rows=len(rows),writer_components=plan['writer_components'],
        prompt_components=plan['prompt_components'],dependency_components=plan['dependency_components'],
        scope=plan['inference'],controls=dict(original_requests_preserved=True,dependencies_explicit=True,training_only_extra_prior=True),
        files={'ANALYSIS_PLAN.json':filehash(out/'ANALYSIS_PLAN.json')})


def aggregate(rows):
    conditions=sorted({r['condition'] for r in rows});result={}
    for condition in conditions:
        own=[r for r in rows if r['condition']==condition];sessions=defaultdict(list)
        for r in own:sessions[(r['writer_component'],r['session'])].append(r['score']['half_brier'])
        writers=defaultdict(list)
        for (writer,session),scores in sessions.items():writers[writer].append(statistics.mean(scores))
        means={k:statistics.mean(v) for k,v in writers.items()};bins=[]
        for i in range(5):
            group=[r for r in own if r['score']['valid'] and min(4,int(max(r['probabilities'])*5))==i]
            bins.append(dict(lower=i/5,upper=(i+1)/5,n=len(group),
                confidence=statistics.mean(max(r['probabilities']) for r in group) if group else None,
                accuracy=statistics.mean(r['score']['accuracy'] for r in group) if group else None))
        result[condition]=dict(attempted=len(own),valid=sum(r['score']['valid'] for r in own),
            writer_balanced_half_brier=statistics.mean(means.values()),writer_means=means,
            event_accuracy=statistics.mean(r['score']['accuracy'] for r in own),
            event_mean_log_loss=None if any(r['score']['log_loss_infinite'] for r in own) else statistics.mean(r['score']['log_loss'] for r in own),
            infinite_log_losses=sum(r['score']['log_loss_infinite'] for r in own),calibration_bins=bins)
    no=result['no_history']['writer_means'];own=result['own_history']['writer_means']
    if set(no)!=set(own):raise ValueError('unpaired primary writer population')
    paired=[no[k]-own[k] for k in sorted(no)]
    return dict(conditions=result,primary=dict(mean=statistics.mean(paired),n_writer_components=len(paired),
        descriptive_writer_sd=statistics.stdev(paired) if len(paired)>1 else None,population_interval=None,
        interval_status='not claimed; shared source/prompt dependencies and limited independent support'),
        dependency_components=len(set(dependency_groups([r for r in rows if r['condition']=='own_history']).values())))


def parse_raw(raw,n,context_tokens=None):
    if raw.get('done') is not True or raw.get('done_reason')!='stop':return None
    if context_tokens is not None:
        count=raw.get('prompt_eval_count')
        if type(count) is not int or not 0<count<context_tokens-1024:return None
    try:
        body=json.loads(raw['message']['content']);p=body['probabilities']
        if not distribution(p,[1.]+[0.]*(n-1))['valid']:return None
        return p
    except (ValueError,KeyError,TypeError):return None


def consume(out,card,pulse,raw):
    primary=raw/'jobs'/card['primary_card'];cloud=raw/'jobs'/card['cloud_card']
    analysis=read(raw/'jobs'/card['analysis_card']/'ANALYSIS_PLAN.json')
    expected=read(cloud/'REQUESTS.json');truth=read(primary/'EVALUATOR_ONLY.json');inputs=read(primary/'READER_INPUTS.json')
    incoming=read(card['retrieval'])
    if incoming['source_request_sha256']!=filehash(cloud/'REQUESTS.json'):raise ValueError('retrieval request scope differs')
    by={r['id']:r for r in incoming['rows']};targets={r['id']:r for r in truth};rows=[]
    if len(by)!=len(incoming['rows']) or set(by)!={r['id'] for r in expected}:raise ValueError('incomplete or repeated capable request')
    for r in expected:
        saved=by[r['id']]
        if saved['request']!=r or saved['model_profile']!=r['model_profile']:raise ValueError('retrieved request/profile differs')
        if not saved.get('cost_receipt') or not saved.get('runtime_identity'):raise ValueError('retrieval lacks cost or actual runtime identity')
        for field in ('model_digest','server_version','context_tokens','quantization'):
            if saved['runtime_identity'].get(field)!=r['model_profile'][field]:
                raise ValueError('actual returned model runtime differs: '+field)
        p=parse_raw(saved['raw_response'],len(r['public']['labels']),r['model_profile']['context_tokens']);t=targets[r['source_id']]
        target=[float(label==t['truth']) for label in r['public']['labels']]
        rows.append(dict(id=t['id'],condition=r['condition'],writer_component=t['writer_component'],prompt_component=t['prompt_component'],
            session=t['session'],probabilities=p,score=distribution(p,target)))
    for r in inputs:
        t=targets[r['id']];target=[float(label==t['truth']) for label in r['labels']]
        for name,p in [('training_prior',r['prior']),('persistence',r['persistence']),('full_training_prior',analysis['full_training_prior'])]:
            rows.append(dict(id=t['id'],condition=name,writer_component=t['writer_component'],prompt_component=t['prompt_component'],
                session=t['session'],probabilities=p,score=distribution(p,target)))
    if len(rows)!=len(truth)*6:raise ValueError('whole paired matrix incomplete')
    report=aggregate(rows);freeze(out/'ROWS.json',rows);freeze(out/'COMPARISONS.json',report);pulse(phase='complete-only-primary-analysis')
    return dict(status='complete',kind='scientific',rows=len(rows),comparisons=report,
        scope='descriptive human handling; exact returned model/profile declared; no mental-state or fresh-component claim',
        controls=dict(all_reader_arms=True,all_cheap_controls=True,raw_response_reparse=True,invalids_retained=True,zero_support_not_clipped=True),
        files={n:filehash(out/n) for n in ('ROWS.json','COMPARISONS.json')})
