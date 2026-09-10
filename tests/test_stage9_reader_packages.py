import pytest
from runners.stage9 import reader_packages as packages
from runners.stage9 import neural_operations as operations
from runners.stage9.common import write


def test_base_reference_has_no_adapter_and_no_inherited_admission():
    adapter,sha,identity=packages.reference_package('qwen','base')
    assert adapter is None and sha=='base-no-adapter' and len(identity)==64
    with pytest.raises(ValueError):packages.reference_package('qwen','other')


def test_original_archive_hash_and_source_identity_are_both_checked(tmp_path,monkeypatch):
    monkeypatch.setattr(packages,'REPO',tmp_path)
    base=packages.BASES['qwen'];p=tmp_path/'results/phase_2_4_stage_8/adapters/fm_qwen/frozen'
    write(p/'adapter_config.json',{'base_model_name_or_path':base['model']})
    (p/'adapter_model.safetensors').write_bytes(b'fixture-only-weights')
    expected=packages.legacy_hash(p);monkeypatch.setattr(packages,'ARCHIVES',{'qwen':('fm_qwen',expected)})
    row={'path':str(p),'pilot':False,'seed':8001,'epoch':2,'base':base['model'],'revision':base['revision'],'sha':expected}
    write(tmp_path/'results/phase_2_4_stage_8/ADAPTERS.json',{'fm_qwen':row})
    assert packages.reference_package('qwen','archive')[0]==p
    (p/'adapter_model.safetensors').write_bytes(b'changed-weights')
    with pytest.raises(ValueError,match='preserved Stage 8'):packages.reference_package('qwen','archive')


def test_reference_cannot_silently_load_a_fitted_checkpoint(tmp_path,monkeypatch):
    monkeypatch.setenv('S9_CELL_IDENTITY','b'*64)
    with pytest.raises(ValueError,match='cannot also name'):
        operations.run(operations.ROOT/'private/neural-operation-pilots/not-created',operation='offered',
            family='qwen',training=tmp_path,cases=tmp_path,scope='pilot',limit=2,package_kind='base')
