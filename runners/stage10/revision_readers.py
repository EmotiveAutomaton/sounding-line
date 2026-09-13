"""Common-budget local revision readers and adaptive-effort callbacks.

DESIGN CHECK: LESSONS2-5 and Stage 10 six-strategy contract. Same tasks/options,
complete native execution, no unmarked fallback, complete raw-cost replay and
training-only memory hold for null and alternative. Both naming conditions size
against grounded names; missing support remains a recorded route limitation.
"""
import hashlib
from pathlib import Path
import time
from . import ollama, revision_programs as programs, revision_proposal as proposal, revision_memory as memory, effort
from .contracts import canonical, digest, parse_forecast
from .queue import read


def identity():
    names=['revision_readers.py','revision_programs.py','revision_proposal.py','revision_memory.py','revision_source.py',
           'contracts.py','ollama.py','reader.py','effort.py']
    return {'runners/stage10/'+n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in names}


def worst_feedback(task):
    actions=list(programs.descriptions(task))
    candidates=[{'goal_hypothesis':'bounded conjecture','program':{'feature':'constant','threshold':i+1,
        'below':actions[i%len(actions)],'otherwise':actions[(i+1)%len(actions)]}} for i in range(8)]
    return programs.evaluate(task,candidates)


class Readers:
    def __init__(self,training,answers):
        self.training,self.answers=training,answers
        self.library=memory.induce(training,answers)
        self.sources={**identity(),'training-public':digest(training),'training-answers':digest(answers),
                      'library':digest(self.library),'model-profile':digest([ollama.MODEL,ollama.MODEL_DIGEST])}

    def representation(self,task,arm):
        def fits(value):
            try:
                proposal.request_for(task,worst_feedback(task),value)
                ollama.request_for(task,examples=value['episodes'],context_tokens=16384)
                return True
            except ValueError:return False
        return memory.representation(task,self.training,self.answers,self.library,procedures=arm.startswith('R4'),
            naming='opaque' if arm=='R4-opaque' else 'grounded',fits=fits)

    def preflight(self,task):
        programs.features(task);ollama.request_for(task,context_tokens=16384)
        proposal.request_for(task,worst_feedback(task))
        for arm in ['R1','R4-grounded','R4-opaque']:self.representation(task,arm)
        return True

    def route(self,task,output,arm,allowance=768):
        if arm not in {'R0','R1','R2','R3','R4-grounded','R4-opaque'} or allowance not in {256,512,768}:
            raise ValueError('undeclared revision route/budget')
        if arm in {'R2','R3','R4-grounded','R4-opaque'} and allowance not in {512,768}:raise ValueError('two-round route requires its full allocated budget')
        if task.task_id in {r['task_id'] for r in self.training}:raise ValueError('target is a training example')
        if identity()!={k:v for k,v in self.sources.items() if k.startswith('runners/')}:
            raise ValueError('revision source changed during execution')
        binding=digest({'sources':self.sources,'task':task.public(),'task_id':task.task_id,'arm':arm,'allowance':allowance})
        terminal=output/'COMPLETE.json';saved=read(terminal) if terminal.exists() else None
        if saved and saved['binding']!=binding:raise ValueError('revision route binding changed')
        if saved:
            actual={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in output.rglob('*') if p.is_file() and p!=terminal}
            if actual!=saved['files']:raise ValueError('revision retained file inventory changed')
            for name,expected in saved['files'].items():
                p=output/name
                if not p.resolve().is_relative_to(output.resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
                    raise ValueError('revision retained file changed')
        output.mkdir(parents=True,exist_ok=True)
        input_record={'binding':binding,'task':task.public(),'sources':self.sources,'arm':arm,'allowance':allowance}
        if (output/'INPUT.json').exists():
            if read(output/'INPUT.json')!=input_record:raise ValueError('partial route binding differs')
        else:ollama.write_new(output/'INPUT.json',input_record)
        started=time.perf_counter();calls=[];executions=[];forecast=None;state='INVALID';rep=None
        if arm in {'R1','R4-grounded','R4-opaque'}:
            rep,selection=self.representation(task,arm)
            if (output/'REPRESENTATION.json').exists():
                if read(output/'REPRESENTATION.json')!={'payload':rep,'selection':selection}:raise ValueError('revision memory changed')
            else:ollama.write_new(output/'REPRESENTATION.json',{'payload':rep,'selection':selection})
        if arm in {'R0','R1','R2'}:
            current=task
            from dataclasses import replace
            rounds=2 if arm=='R2' else 1
            for i in range(rounds):
                directory=output/f'call-{i}'
                if saved and not (directory/'ATTEMPT.json').exists():raise ValueError('complete revision route lacks an attempt')
                call=ollama.call(current,directory,generated_tokens=allowance//rounds,context_tokens=16384,
                    examples=rep['episodes'] if rep else None,
                    instruction='Reconsider the original source and your unverified earlier answer; no additional observation.' if i else 'Predict directly using only the declared evidence and any permitted concrete episodes.')
                raw=read(directory/'RAW.json');state='INVALID';forecast=None
                try:
                    if raw.get('done') is not True or raw.get('done_reason')!='stop':raise ValueError('truncated answer')
                    forecast=parse_forecast(raw['message']['content'],current);state='VALID'
                except (ValueError,KeyError,TypeError):pass
                if (call['status'],call['forecast'])!=(state,forecast) or call['cost']!={k:raw.get(k) for k in call['cost']}:
                    raise ValueError('retained direct parse or cost differs')
                calls.append(call)
                if i==0 and rounds==2:
                    current=replace(task,evidence={'original_source_evidence':task.evidence,
                        'reader_scratchpad':{'origin':'unverified response from this reader, not observed truth','parse_status':state,'draft':raw.get('message',{}).get('content','')}})
        else:
            feedback=None
            for i in range(2):
                directory=output/f'proposal-{i}'
                if saved and not (directory/'ATTEMPT.json').exists():raise ValueError('complete proposal route lacks an attempt')
                call=proposal.call(task,directory,feedback,rep,generated_tokens=allowance//2);calls.append(call)
                if call['status']!='VALID':break
                feedback=programs.evaluate(task,call['proposal']['candidates']);executions.append(feedback)
                path=output/f'execution-{i}.json'
                if path.exists():
                    if read(path)!=feedback:raise ValueError('saved native execution changed')
                else:ollama.write_new(path,feedback)
            if len(calls)==2 and calls[-1]['status']=='VALID':
                forecast={'choice':calls[-1]['proposal']['choice'],'probabilities':feedback['probabilities'],
                          'insufficient_evidence':calls[-1]['proposal']['insufficient_support'],
                          'explanation':'Equal mixture of executed approximate released-edit rules; generated choice retained separately.'}
                parse_forecast(canonical(forecast),task);state='VALID'
        cost={'wall_seconds':time.perf_counter()-started,'model_calls':len(calls),
              'input_tokens':sum(c['cost']['prompt_eval_count'] for c in calls),'output_tokens':sum(c['cost']['eval_count'] for c in calls),
              'executor_evaluations':sum(e['executor_evaluations'] for e in executions),
              'reasoning_tokens':None,'reasoning_tokens_status':'not separately exposed'}
        if saved:cost['wall_seconds']=read(output/'RESULT.json')['cost']['wall_seconds']
        if cost['wall_seconds']<sum(c['wall_seconds'] for c in calls):raise ValueError('callback cost omits model wall time')
        result={'status':state,'forecast':forecast,'evidence_sha256':digest(task.public()),'maximum_generated_tokens':allowance,'cost':cost}
        effort.check_attempt(task,result,allowance)
        if saved:
            if read(output/'RESULT.json')!=result:raise ValueError('complete revision result does not reconstruct')
            return result
        ollama.write_new(output/'RESULT.json',result)
        ollama.write_new(terminal,{'status':'COMPLETE','binding':binding,'files':{p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file()}})
        return result

    def initial(self,task,output,allowance):return self.route(task,output,'R0',allowance)
    def retrieval(self,task,output,allowance):return self.route(task,output,'R1',allowance)
    def structured(self,task,output,allowance):return self.route(task,output,'R3',allowance)
