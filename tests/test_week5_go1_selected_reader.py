import json
import pytest
from runners.drive.cards import week5_go1_pipeline_v2 as go
from runners.drive.cards.week5_at_scoring_v4 import NUMERICAL_SPEC
from runners.drive.cards.week5_at_scoring import digest


def selection(tmp_path):
    model={'model':'constructed','revision':'fixed','files':{}}
    manifest=tmp_path/'manifest.json';go.core.write(manifest,model)
    root=tmp_path/'selection'
    go.core.write(root/'output/RESULT.json',{'card':'AT2','selected_model':'constructed','selection_admissible':True})
    go.core.write(root/'output/READER_BINDING.json',{'model':model['model'],'revision':model['revision'],
        'manifest_sha256':digest(model),'numerical_spec':NUMERICAL_SPEC})
    reseal(root)
    return {'model_manifest':str(manifest),'at2_selection':str(root)}


def reseal(root):
    go.core.write(root/'COMPLETE.json',{'status':'COMPLETE','fresh_process_verified':True,
        'outputs':{p.relative_to(root).as_posix():go.core.sha(p) for p in (root/'output').glob('*.json')}})


def test_exact_selected_binding(tmp_path):
    inputs=selection(tmp_path);binding=go.reader_binding(inputs)
    assert binding['selected_reader']['numerical_spec']==NUMERICAL_SPEC
    assert binding['selection_complete_sha256']==go.core.sha(tmp_path/'selection/COMPLETE.json')


@pytest.mark.parametrize('defect',['revision','precision','screening','inadmissible','unsealed','tamper'])
def test_refuses_changed_selection(tmp_path,defect):
    inputs=selection(tmp_path);root=tmp_path/'selection'
    path=root/'output/READER_BINDING.json';result=root/'output/RESULT.json'
    data=json.loads(path.read_text());r=json.loads(result.read_text())
    if defect=='revision':data['revision']='different'
    if defect=='precision':data['numerical_spec']={}
    if defect=='screening':r['screening_only']=True
    if defect=='inadmissible':r['selection_admissible']=False
    if defect=='tamper':data['added']='unsealed'
    go.core.write(path,data);go.core.write(result,r)
    if defect!='tamper':reseal(root)
    if defect=='unsealed':
        done=json.loads((root/'COMPLETE.json').read_text());del done['outputs']['output/READER_BINDING.json']
        go.core.write(root/'COMPLETE.json',done)
    with pytest.raises(ValueError):go.reader_binding(inputs)
