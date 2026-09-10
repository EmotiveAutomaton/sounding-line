from copy import deepcopy
import pytest
from runners.stage9.arxivedits import canonical_edits,correspondence,visible


def pair():
    return {'sentence-1':'A old name .','sentence-2':'A new name .','sentence-1-level':1,'sentence-2-level':2,
            'edits-combination-0':{'0':{'type':'Substitute','intention':'Content',
              'sentence-1-token-indices':[1,2],'sentence-2-token-indices':[1,2]}},
            'edits-combination-1':{'alternative':{'intention':None}},'edits-combination-2':{}}


def test_half_open_canonical_span_not_alternative():
    p=pair();rows=canonical_edits(p)
    assert len(rows)==1 and rows[0]['before']=='old' and rows[0]['artifact']=='new'
    p['edits-combination-0']['0']['sentence-2-token-indices']=[1,99]
    with pytest.raises(ValueError,match='outside'):canonical_edits(p)


def test_complete_absent_side_and_projection_no_labels():
    p=pair();p['edits-combination-0']['0'].update(type='Deletion',**{'sentence-2-token-indices':None})
    row=canonical_edits(p)[0];assert row['artifact']==''
    changed=deepcopy(row);changed['label']='Format';changed['source_span_1']=[0,1]
    assert visible(row,'artifact')==visible(changed,'artifact')=={'text':''}
    assert visible(row,'pair')=={'text':'','before':'old'}
    p['edits-combination-0']['0']['sentence-2-token-indices']=[1,2]
    with pytest.raises(ValueError,match='absent side'):canonical_edits(p)


def test_both_licenses_and_unique_version_correspondence():
    p=pair();license='http://creativecommons.org/licenses/by/4.0/'
    paper={'license':{'1':license,'2':license},'1':{'x':'A old name.'},'2':{'y':'A new name.'}}
    assert correspondence(p,paper)['exclusion'] is None
    paper['2']['z']='A new name .'
    assert correspondence(p,paper)['exclusion']=='unverified_unique_version_sentence'
    paper['license']['2']='http://arxiv.org/licenses/nonexclusive-distrib/1.0/'
    assert correspondence(p,paper)['exclusion']=='outside_explicit_license_selection'
