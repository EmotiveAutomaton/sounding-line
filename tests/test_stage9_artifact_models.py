import copy

import pytest

from runners.stage9.artifact_models import validate_choice,validate_library,validate_prepared
from runners.stage9.choice_fit import fit as fit_choice
from runners.stage9.program_fit import fit_library
from tests.test_stage9_choice_fit import visible
from tests.test_stage9_erased_inference import A,B


def training():
    return [{'unit':maker+str(i),'evidence':visible(),'target':target,'maker_group':maker,'purpose_group':'purpose'}
            for maker,target in [('one',A),('two',B)] for i in range(2)]


def test_actual_fitted_library_checks_inputs_and_rejects_changed_parameters():
    rows=training();units={r['unit'] for r in rows}
    library,audit=fit_library(rows,units,minimum_units=2)
    assert validate_library(library,audit,rows,units,minimum_units=2,expected_candidates=2)
    changed=copy.deepcopy(library);changed['candidates']['program0']['purpose']['write']+=1
    with pytest.raises(ValueError,match='parameter'):
        validate_library(changed,audit,rows,units,minimum_units=2,expected_candidates=2)
    with pytest.raises(ValueError,match='identity'):
        validate_library(library,audit,rows[:-1],units,minimum_units=2,expected_candidates=2)
    wrong=copy.deepcopy(library);wrong['shared_groups']['program0']='maker1'
    with pytest.raises(ValueError,match='hierarchy'):
        validate_library(wrong,audit,rows,units,minimum_units=2,expected_candidates=2)


def test_actual_population_fit_checks_input_hash_and_optimizer_receipt():
    rows=[{k:r[k] for k in ('unit','evidence','target')} for r in training()]
    model,audit=fit_choice(rows,l2=.01)
    assert validate_choice(model,audit,rows,.01)
    wrong=copy.deepcopy(audit);wrong['converged']=False
    with pytest.raises(ValueError,match='receipt'):
        validate_choice(model,wrong,rows,.01)
    with pytest.raises(ValueError,match='receipt'):
        validate_choice(model,audit,rows,.1)


def test_empty_or_tampered_preparation_never_skips_to_fitting():
    data={'units':[],'records':[],'receipt':{'records_sha256':'wrong','unit_ledger_sha256':'wrong',
         'band':930000000,'per_domain':1,'view':'artifact'}}
    with pytest.raises(ValueError,match='allocation'):
        validate_prepared(data,band=930000000,per_domain=1,view='artifact')
