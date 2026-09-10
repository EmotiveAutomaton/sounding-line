"""Restricted ordinary revision reader; fitted coefficients and public text only.

DESIGN CHECK: H01/H02/X02/X06; LESSONS 3--5. NULL: private fields, changed
parameters, missing model outputs or boundary leaks refuse. ALTERNATIVE: all
registered fitted rivals run with identical permitted input and fixed support.
No evaluation label, corpus loader, fitting library or dataset path is imported.
"""
import hashlib,json,time,traceback
from . import base,revision_features


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def run(evidence,task):
    if task['operation']!='revision_models' or task['information_sha256']!=digest(evidence):raise ValueError('revision operation or input identity differs')
    models=task['parameters']
    if not models or task['parameters_sha256']!=digest(models):raise ValueError('revision model identity differs')
    if len({tuple(m['classes']) for m in models.values()})!=1:raise ValueError('revision rivals use different class supports')
    forecasts={name:revision_features.predict(evidence,model) for name,model in models.items()}
    return {'valid':True,'probabilities':forecasts,'parameters_sha256':digest(models),
        'scope':'ordinary label-agreement rivals; no historical maker-intention claim'}


def main():
    start=time.monotonic()
    try:
        with open('task.json',encoding='utf-8') as f:task=json.load(f)
        if task.get('probe'):base.save('receipt',base.probe(task));return 0
        with open('evidence.json',encoding='utf-8') as f:evidence=json.load(f)
        base.save('prediction',run(evidence,task))
        base.save('receipt',{'valid':True,'wall_seconds':time.monotonic()-start,'loaded_sources':base.loaded_sources()})
        return 0
    except Exception:
        base.save('error',{'valid':False,'traceback':traceback.format_exc()});return 1
