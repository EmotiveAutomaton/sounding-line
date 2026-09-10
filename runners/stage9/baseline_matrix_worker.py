"""Execute all declared cheap comparators independently of program inference.

DESIGN CHECK: M01/M04/C08/X02/X05/X06; LESSONS 3--5, CONTROLS 2/6.
NULL: identical evidence gives identical forecasts; repetition adds no information.
ALTERNATIVE: visible marks and genuine history can change predictions. Missing or
invalid inputs refuse this complete baseline matrix, but another inference route's
failure cannot invalidate it. Supplied support is shared by every comparator.
"""
import copy
import json
import time
import traceback

from .base import loaded_sources,probe,save
from .artifact_view import support,validate
from .choice_features import cheap_adaptation,predict
from .program_inference import Budget,identity
from .single_worker import extended_json


def brief_prediction(evidence,parameters):
    """Ordinary context and the offered menu; the content of the marks is omitted."""
    validate(evidence)
    brief=copy.deepcopy(evidence)
    brief['earlier']=[];brief['current']['marks']=[]
    if brief['view']=='process_record':
        brief['current']['events']=[];brief['current']['observed_stop']=None
    brief['support']=support(brief['current'],brief['view'])
    forecast=predict(brief,parameters)
    total=sum(forecast[a] for a in evidence['support'])
    if total<=0:raise ValueError('brief comparator gives no mass to the offered menu')
    return {a:forecast[a]/total for a in evidence['support']}


def main():
    started=time.monotonic()
    try:
        with open('task.json',encoding='utf-8') as stream:task=json.load(stream)
        if task.get('probe'):
            save('receipt',probe(task));return 0
        with open('evidence.json',encoding='utf-8') as stream:bundle=json.load(stream)
        if set(bundle)!={'evidences','models','population_types'}:
            raise ValueError('undeclared baseline matrix inputs')
        if task['information_sha256']!=identity(bundle) or task['operation']!='baseline_matrix':
            raise ValueError('baseline information identity mismatch')
        if not 1<=len(bundle['evidences'])<=64 or not 1<=len(bundle['models'])<=8:
            raise ValueError('baseline matrix exceeds declared envelope')
        if task['strengths']!=[8.,16.,32.] or type(task['budget']) is not int or not 1<=task['budget']<=10000:
            raise ValueError('undeclared adaptation selection grid or budget')
        budget=Budget(task['budget']);rows={}
        for name,evidence in bundle['evidences'].items():
            validate(evidence);rows[name]={}
            for key,parameters in bundle['models'].items():
                if parameters['individual'] is not False:
                    raise ValueError('population model cannot silently condition on individuals')
                budget.charge(2)
                rows[name][key+'|population']=predict(evidence,parameters)
                rows[name][key+'|brief']=brief_prediction(evidence,parameters)
                for strength in task['strengths']:
                    budget.charge()
                    offsets=cheap_adaptation(evidence,bundle['population_types'],strength)
                    rows[name][key+'|cheap-'+str(strength)]=predict(evidence,parameters,offsets)
        save('prediction',extended_json({'valid':True,'predictions':rows,'evaluations_used':budget.used,
            'information_sha256':identity(bundle),'operation':'baseline_matrix',
            'assistance':'trained conditional-choice parameters and fixed bag-of-marks adaptation'}))
        save('receipt',{'valid':True,'wall_seconds':time.monotonic()-started,'loaded_sources':loaded_sources()})
        return 0
    except Exception:
        save('error',{'valid':False,'traceback':traceback.format_exc()});return 1
