"""Restricted prospective writing reader, with source-native targets and views.

DESIGN CHECK: H07/H08/X02/X06; LESSONS 3--5. NULL: unknown model, future-label
fields or changed input/parameter identity refuses. ALTERNATIVE: all current-text
and eligible prior-record rivals return complete distributions. No source, labels,
fitting library, maker IDs or reconstructed future draft enters this worker.
"""
import hashlib,json,time,traceback
from . import base,record_features


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def run(evidence,task):
    if task['operation']!='prospective_record_models' or task['information_sha256']!=digest(evidence):raise ValueError('prospective operation/input identity differs')
    models=task['parameters'];kind=task['kind'];record=task['record']
    if kind not in record_features.SUPPORT or type(record) is not bool:raise ValueError('explicit native target and view required')
    expected={'lexical','surface','class_prior','majority'}|({'previous_transition','persistence'} if record else set())
    if set(models)!=expected or task['parameters_sha256']!=digest(models) or any(m['kind']!=kind for m in models.values()):
        raise ValueError('complete source-native model set required')
    expected_fields=({'document','suggestions','earlier_handling'} if record else {'document','suggestions'}) if kind=='coauthor' else (
        {'document','previous_document','previous_category','previous_location'} if record else {'document'})
    if set(evidence)!=expected_fields:raise ValueError('prospective evidence differs from its declared view')
    return {'valid':True,'probabilities':{k:record_features.predict(evidence,m) for k,m in models.items()},
        'parameters_sha256':digest(models),'kind':kind,'record':record,
        'scope':'source-defined prospective handling or next released edit; no maker-intention claim'}


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
