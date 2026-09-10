"""Run a manually supplied matrix of artifact comparisons on shared permitted inputs.

DESIGN CHECK: M01/M04/C08/X02/X05/X06; LESSONS 3--5. NULL: undeclared data,
hidden targets, incomplete supports or budget exhaustion invalidate the whole matrix.
ALTERNATIVE: four complete comparator forecasts per explicit query, with repeated
program/work likelihoods reused but never counted as additional observations.
No query, hypothesis, source acquisition or study is invented by this worker.
"""
import json
import time
import traceback

from .base import loaded_sources, probe, save
from .choice_features import cheap_adaptation, predict
from .likelihood_table import Table
from .grouped_table import GroupedTable
from .particle_table import ParticleTable
from .program_inference import Budget, identity
from .single_worker import extended_json
from .purpose_reader import forecast as purpose_forecast
from .proposal_reader import forecast as proposal_forecast
from .context_reader import forecast as context_forecast
from .goal_reader import forecast as goal_forecast
from .cue_reader import forecast as cue_forecast
from .ambiguity_reader import forecast as ambiguity_forecast
from .constraint_reader import forecast as constraint_forecast
from .familiarity_reader import forecast as familiarity_forecast
from .selection_reader import forecast as selection_forecast
from .selection_reader import familiarity_forecast as familiarity_selection_forecast


def main():
    started = time.monotonic()
    try:
        with open('task.json',encoding='utf-8') as stream:
            task = json.load(stream)
        if task.get('probe'):
            save('receipt',probe(task)); return 0
        with open('evidence.json',encoding='utf-8') as stream:
            bundle = json.load(stream)
        if task['operation'] in ('purpose_comparison','proposal_evaluation','context_transfer','goal_transfer','context_cue','offered_history','bounded_creation','maker_familiarity','select_observation','select_familiar_observation'):
            if task['information_sha256']!=identity(bundle) or type(task['budget']) is not int or not 1<=task['budget']<=8000000:
                raise ValueError('purpose input identity or budget mismatch')
            handler={'purpose_comparison':purpose_forecast,'proposal_evaluation':proposal_forecast,
                     'context_transfer':context_forecast,'goal_transfer':goal_forecast,'context_cue':cue_forecast,
                     'offered_history':ambiguity_forecast,'bounded_creation':constraint_forecast,
                     'maker_familiarity':familiarity_forecast,'select_observation':selection_forecast,
                     'select_familiar_observation':familiarity_selection_forecast}[task['operation']]
            result=handler(bundle,Budget(task['budget']))
            save('prediction',extended_json({**result,'valid':True,'operation':task['operation']}))
            save('receipt',{'valid':True,'wall_seconds':time.monotonic()-started,'loaded_sources':loaded_sources()})
            return 0
        if set(bundle)!={'evidences','candidates','prior','shared_groups','population','population_types'}:
            raise ValueError('undeclared comparison inputs')
        if task['information_sha256']!=identity(bundle) or task['operation']!='comparison_matrix':
            raise ValueError('comparison information or operation mismatch')
        if not isinstance(bundle['evidences'],dict) or not 1<=len(bundle['evidences'])<=64:
            raise ValueError('explicit query matrix exceeds envelope')
        if type(task['budget']) is not int or not 1<=task['budget']<=8000000:
            raise ValueError('comparison budget exceeds envelope')
        if bundle['population']['individual'] or not bundle['shared_groups']:
            raise ValueError('population and hierarchy definitions missing or inconsistent')
        budget = Budget(task['budget'])
        if task['estimator']=='uniform':
            table = Table(bundle['candidates'],budget,exact_limit=task['exact_limit'],
                          permutations=task['permutations'],seed=task['seed'])
        elif task['estimator']=='grouped':
            table = GroupedTable(bundle['candidates'],budget,exact_states=task['exact_states'],
                                 draws=task['draws'],seed=task['seed'])
        elif task['estimator']=='particles':
            table = ParticleTable(bundle['candidates'],budget,particles=task['particles'],seed=task['seed'])
        else:
            raise ValueError('unknown declared erasure estimator')
        predictions = {}
        for name,evidence in bundle['evidences'].items():
            budget.charge(2)
            # All comparators receive this same evidence. The generic route's
            # declared model intentionally ignores the history fields.
            offsets = cheap_adaptation(evidence,bundle['population_types'],task['adaptation_strength'])
            flat = table.forecast(evidence,bundle['prior'])
            hierarchical = table.forecast(evidence,bundle['prior'],shared_groups=bundle['shared_groups'])
            predictions[name] = {'population':{'prediction':predict(evidence,bundle['population'])},
                'cheap_individual':{'prediction':predict(evidence,bundle['population'],offsets)},
                'program_mixture':flat,'differentiated_maker':hierarchical}
        save('prediction',extended_json({'valid':True,'predictions':predictions,'evaluations_used':budget.used,
            'cache_hits':table.cache_hits,'information_sha256':identity(bundle),
            'assistance':'declared executable program and numerical population models',
            'operation':'comparison_matrix','estimator':task['estimator']}))
        save('receipt',{'valid':True,'wall_seconds':time.monotonic()-started,'loaded_sources':loaded_sources()})
        return 0
    except Exception:
        save('error',{'valid':False,'traceback':traceback.format_exc()}); return 1
