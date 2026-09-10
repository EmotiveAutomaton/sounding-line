"""Actual entry acquisition across the fixed familiarity/expectedness cross.

DESIGN CHECK: T02/S02/X01/X02/X05/X06/X08/X11; LESSONS 3--5, CONTROLS 6--7.
NULL: changing evaluator truths cannot change an actual reader input or rescue a
failed forecast. ALTERNATIVE: entry rules can differ in cost and future usefulness
under familiar versus unfamiliar exposure. Every condition pays for three previews;
only saved selected purchases are revealed, and budgets are zero, one and three.
The current-only program and all fitted surface rivals remain available. Identity
probabilities are retained as diagnostics; the already separate recognition analysis
and its strong surface rivals are not replaced by this entry comparison.
"""
from pathlib import Path
from .common import digest
from .familiarity_entry_cases import construct
from .familiarity_cases import CONDITIONS
from .selection_jobs import forecast_case

FIXED_BUDGETS=(0,1,3)


def forecast_unit(case,package,purpose_groups,directory,*,resume_only=False):
    del purpose_groups
    cf=construct(case,case['role'])
    if cf!=case['familiarity_entry']:raise ValueError('familiarity entry source or future changed')
    directory=Path(directory);conditions={};costs={}
    source_hash=digest(cf['source_templates'])
    for condition in CONDITIONS:
        observed=cf['conditions'][condition]
        selected={**observed,'source_template_sha256':source_hash}
        row=forecast_case(case,selected,package,directory/digest(condition)[:12],resume_only=resume_only,
                          operation='select_familiar_observation',fixed_budgets=FIXED_BUDGETS)
        conditions[condition]=row
        for cost in row['costs']:costs[cost['capsule']]={**cost,'condition':condition}
    return {'unit':case['unit'],'role':case['role'],'conditions':conditions,'costs':list(costs.values()),
        'domain':case['private_factors']['domain'],'purpose':case['private_factors']['purpose'],
        'case_sha256':digest(case),'source_template_sha256':source_hash,
        'scope':'matched familiar/unfamiliar and conditional expectedness; entry future quality and cost separately'}
