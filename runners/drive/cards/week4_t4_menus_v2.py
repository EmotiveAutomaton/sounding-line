"""T4 source-ledger path repair; canonical choices and source hashes unchanged.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-02. Windows and POSIX keys must
authenticate the same file. Conflicting aliases must refuse; missing or changed
digests remain invalid. No choices, histories, populations or outcomes change.
"""
from pathlib import Path
from types import FunctionType
from . import week4_t4_menus as original

configuration=original.configuration

def normalize_pins(pins):
    result={}
    for name,value in pins.items():
        key=name.replace('\\','/')
        if key in result and result[key]!=value:
            raise ValueError('Conflicting source pin aliases')
        result[key]=value
    return result

def load(inputs,mode):
    if mode=='constructed':return original.load(inputs,mode)
    registry=original.read(inputs['source_inputs'])
    source_path=Path(registry['source_pins']).resolve()
    def bound_read(path):
        result=original.read(path)
        return normalize_pins(result) if Path(path).resolve()==source_path else result
    reader=FunctionType(original.load.__code__,dict(original.load.__globals__,read=bound_read),
                        original.load.__name__,original.load.__defaults__,original.load.__closure__)
    return reader(inputs,mode)

run=FunctionType(original.run.__code__,dict(original.run.__globals__,load=load),
                 original.run.__name__,original.run.__defaults__,original.run.__closure__)
def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
