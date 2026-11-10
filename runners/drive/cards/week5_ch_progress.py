"""Deterministic CH analysis checkpoints, including bootstrap resumes.

Only a new attempt can read a hash-bound previous checkpoint. Configuration and
all input specifications bind the cache; unfinished values remain private.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib,json,time
from .week5_ch_source import write_json,digest

ACTIVE=None


class YieldRequested(RuntimeError):pass


class Progress:
    def __init__(self,output,inputs,config):
        self.output=Path(output);self.started=time.process_time();self.calls=0;self.series={};self.last=time.monotonic()
        base_inputs={k:v for k,v in inputs.items() if k!='resume_analysis'}
        self.binding=hashlib.sha256(json.dumps([base_inputs,config],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if 'resume_analysis' in inputs:
            prior=Path(inputs['resume_analysis']['path'])
            if digest(prior)!=inputs['resume_analysis']['sha256']:raise ValueError('Analysis resume hash changed')
            state=json.loads(prior.read_text())
            if state['binding']!=self.binding:raise ValueError('Analysis resume inputs or configuration changed')
            self.series=state['series']
    def save(self):
        write_json(self.output/'CHECKPOINT.json',dict(binding=self.binding,series=self.series,complete=False),mutable=True)
        self.last=time.monotonic()
    def begin(self,label,total):
        name=f'{self.calls}:{label}';self.calls+=1
        prior=self.series.setdefault(name,dict(total=total,values=[]))
        if prior['total']!=total:raise ValueError('Analysis loop changed during resume')
        return name
    def value(self,name,index,compute):
        series=self.series[name];values=series['values']
        if (self.output/'YIELD_REQUEST.json').exists():self.save();raise YieldRequested('Producer checkpointed requested yield')
        if index<len(values):return values[index]
        if index!=len(values):raise ValueError('Nonsequential analysis checkpoint')
        value=compute();values.append(value)
        if len(values)%25==0 or time.monotonic()-self.last>=20:self.save()
        elapsed=time.process_time()-self.started
        if len(values)>=max(1,int(.05*series['total'])) and not (self.output/'PILOT.json').exists():
            write_json(self.output/'PILOT.json',dict(series=name,completed=len(values),total=series['total'],fraction=len(values)/series['total'],invocation_cpu_seconds=elapsed,forecast_series_cpu_seconds=elapsed*series['total']/len(values),basis='first 5% completed deterministic analysis iterations; not final evidence'))
        return value


@contextmanager
def tracking(output,inputs,config):
    global ACTIVE
    if ACTIVE is not None:raise RuntimeError('Nested CH runtime tracking')
    ACTIVE=Progress(output,inputs,config)
    try:yield ACTIVE
    finally:
        ACTIVE.save();ACTIVE=None


def begin(label,total):return ACTIVE.begin(label,total) if ACTIVE is not None else None


def value(name,index,compute):return ACTIVE.value(name,index,compute) if ACTIVE is not None else compute()
