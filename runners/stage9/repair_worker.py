"""Restricted local-consequence baseline inference, without constructor or labels.

DESIGN CHECK: C03/X02/X06; LESSONS 3--5, CONTROLS 6. NULL: undeclared
inputs and absent/changed models refuse execution. ALTERNATIVE: all six fitted
comparators return the same complete probabilities as direct public-only code.
"""
import hashlib,json,time,traceback
from .base import loaded_sources,probe,save
from .repair_features import predict,validate


def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def main():
    start=time.monotonic()
    try:
        with open('task.json',encoding='utf-8') as f:task=json.load(f)
        if task.get('probe'):save('receipt',probe(task));return 0
        with open('evidence.json',encoding='utf-8') as f:bundle=json.load(f)
        if set(bundle)!={'evidence','models'} or task!={'operation':'repair_baselines','information_sha256':identity(bundle)}:
            raise ValueError('undeclared local baseline inputs')
        validate(bundle['evidence'])
        if not 1<=len(bundle['models'])<=6:raise ValueError('invalid fitted comparator count')
        rows={name:predict(bundle['evidence'],parameters) for name,parameters in bundle['models'].items()}
        save('prediction',{'valid':True,'predictions':rows,'information_sha256':identity(bundle)})
        save('receipt',{'valid':True,'wall_seconds':time.monotonic()-start,'loaded_sources':loaded_sources()})
        return 0
    except Exception:save('error',{'valid':False,'traceback':traceback.format_exc()});return 1
