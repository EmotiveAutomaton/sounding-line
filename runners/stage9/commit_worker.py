"""Restricted diff-description reader with all ordinary controls in one call.

DESIGN CHECK: H06/X02/X06; LESSONS 3--5. NULL: changed model/input identity or
private metadata refuses. ALTERNATIVE: every registered rival returns the same
complete candidate support. No labels, source loader or fitting library is loaded.
"""
import hashlib,json,time,traceback
from . import base,commit_features


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def run(evidence,task):
    if task['operation']!='commit_description_models' or task['information_sha256']!=digest(evidence):raise ValueError('description operation/input differs')
    models=task['parameters']
    if set(models)!={'all','surface','description_only','uniform','lexical_overlap','filename_overlap'} or task['parameters_sha256']!=digest(models):
        raise ValueError('complete registered description model set required')
    return {'valid':True,'probabilities':{k:commit_features.predict(evidence,m) for k,m in models.items()},
        'parameters_sha256':digest(models),'scope':'diff to stated description; no individual-maker or hidden-intention claim'}


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
