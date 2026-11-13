"""R2 plan mapping: preserve retained controls; no source-selection decision."""
from copy import deepcopy
from .week5_ch_grid import grid as original_grid

WITHDRAWN=('CH2.year-2017','CH2.year-2026','CH6.year-2017','CH6.year-2026')


def grid():
    result=deepcopy(original_grid())
    for cell in result['cells']:
        cell['original_module']=cell['module']
        cell['module']='runners.drive.cards.week5_ch_analysis_bounded'
        cell['source_months']=['2017-04','2017-05','2017-06']
        cell['state']='withdrawn' if cell['id'] in WITHDRAWN else 'dependency-gated'
        if cell['state']=='withdrawn':
            cell['withdrawal']='R2: component fit of the withdrawn 2017-versus-2026 comparison; no standalone replacement'
        if cell['config'].get('measure') in ('entropy','entropy_fixed100'):
            cell['policy_entropy_calibration_month']='2017-04'
            cell['policy_entropy_outcome_months']=['2017-05','2017-06']
        cell['owner_admitted']=False
        cell['remaining_gates']=['Complete exact registered inputs and native qualification',
            'Whole-family charges and measured execute/replay cost','Committed-design and owner admission',
            'Declared support fallback and conditional-branch decision only after complete parent result']
    result.update(original_registered_rows=44,retained_rows=40,withdrawn_component_rows=4,
        withdrawn_comparisons=2,no_launcher=True,
        disclaimer='Configurations, draw counts, ceilings and branch controls are unchanged for every retained row.')
    return result
