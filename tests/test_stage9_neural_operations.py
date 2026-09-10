from pathlib import Path
import pytest
from runners.stage9 import neural_operations as operations
from runners.stage9.common import closure,digest,write
from runners.stage9.train import BASES


def local_root(tmp_path,monkeypatch):
    monkeypatch.setattr(operations,'ROOT',tmp_path)
    def inside(path,root=tmp_path):
        path=Path(path).resolve()
        if not path.is_relative_to(root):raise ValueError('outside fixture stage')
        return path
    monkeypatch.setattr(operations,'inside',inside)


def test_scientific_operation_refuses_discarded_fit_before_adapter_loading(tmp_path,monkeypatch):
    local_root(tmp_path,monkeypatch)
    fit=tmp_path/'private/training-handler-pilots/v2/qwen/fit'
    identity={'family':'qwen','base':BASES['qwen'],'split':'pilot','seed':997901,'epochs':1,'corpus_sha256':'a'*64}
    write(fit/'IDENTITY.json',identity)
    write(fit/'COMPLETE.json',{'identity_sha256':digest(identity),'curve':[{'updates':8}]})
    write(fit/'SCIENTIFIC_INPUT.json',{'recipe':'both_mixed','seed':997901})
    with pytest.raises(ValueError,match='complete declared factorial'):
        operations.training_package(fit,'qwen','scientific')


def test_scientific_operation_refuses_subsetting_and_changed_case_outputs(tmp_path,monkeypatch):
    local_root(tmp_path,monkeypatch)
    cases=tmp_path/'cases';write(cases/'CASES.json',[])
    receipt={'accepted':True,'construction_only':True,'role':'discovery','outputs':closure([cases/'CASES.json'])}
    write(cases/'COMPLETE.json',receipt)
    with pytest.raises(ValueError,match='cannot subset'):
        operations.case_inputs(cases,'scientific',2)
    write(cases/'CASES.json',[{'changed':True}])
    with pytest.raises(ValueError,match='outputs changed'):
        operations.case_inputs(cases,'scientific',0)


def test_unknown_scope_or_operation_refuses_before_writing(tmp_path,monkeypatch):
    local_root(tmp_path,monkeypatch);monkeypatch.setenv('S9_CELL_IDENTITY','a'*64)
    output=tmp_path/'scientific';training=tmp_path/'missing-fit'
    with pytest.raises(ValueError,match='undeclared neural operation'):
        operations.run(output,operation='invented',family='qwen',training=training,cases=tmp_path,scope='scientific')
    assert not output.exists()


def test_full_discarded_fit_is_pinned_and_cannot_be_replaced(tmp_path,monkeypatch):
    local_root(tmp_path,monkeypatch)
    fit=tmp_path/'pilot/qwen-run2'
    identity={'family':'qwen','base':BASES['qwen'],'split':'pilot','seed':99002,'epochs':3}
    write(fit/'IDENTITY.json',identity)
    write(fit/'COMPLETE.json',{'identity_sha256':digest(identity),'curve':[{'updates':i,'n':80} for i in (200,400,600)]})
    with pytest.raises(ValueError,match='fitting profile differs'):
        operations.training_package(fit,'qwen','pilot')
