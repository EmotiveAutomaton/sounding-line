"""Constructed checkpoint producer for the exact policy migration boundary.

DESIGN CHECK: LESSONS 3-5. This is infrastructure only, with no human inputs.
Changed checkpoint values or missing independent replay refuse under all
scientific outcomes. A correct copied prefix extends to the fixed known answer.
"""
from .batch_runtime import read, freeze, atomic

def execute(output,inputs,config):
    if inputs or config.get('constructed_fixture') is not True:
        raise ValueError('Constructed fixture only')
    output.mkdir(parents=True,exist_ok=True)
    p=output/'CHECKPOINT.json'
    saved=read(p)['values'] if p.exists() else []
    if saved != [2,4,6][:len(saved)] or len(saved)>3:
        raise ValueError('Changed known-answer prefix')
    end=min(3,len(saved)+config['max_new_draws'])
    atomic(p,dict(values=[2,4,6][:end]))
    return dict(status='complete' if end==3 else 'yielded',constructed_fixture=True)

def verify(output,inputs,config):
    if inputs or config.get('constructed_fixture') is not True:
        raise ValueError('Constructed fixture only')
    values=read(output/'CHECKPOINT.json')['values']
    if values != [i*2 for i in range(1,4)] or sum(values)!=12:
        raise ValueError('Independent known-answer replay differs')
    return dict(verified=True,constructed_fixture=True)
