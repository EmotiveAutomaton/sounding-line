import pytest
from runners.stage9.scholawrite import boundary, location, validate, visible


def row(t,before,after):
    return {'project':1,'author':1,'timestamp':t,'before text':before,'after text':after,
            'label':'Text Production','high-level':'IMPLEMENTATION'}


def test_actual_continuity_and_time_define_boundary():
    a=row(100,'a','ab');b=row(200,'ab','abc')
    assert boundary(a,b) is None
    assert boundary(a,b|{'timestamp':100})=='ambiguous or reversed timestamp'
    assert boundary(a,b|{'timestamp':2000000})=='over thirty-minute gap'
    assert boundary(a,b|{'before text':'different'})=='discontinuous visible editor text'
    assert boundary(a,b|{'author':2})=='different project or source-scoped author'
    assert boundary(a,None)=='end of released author stream'
    assert boundary(a,b|{'timestamp_count':2})=='edge incident to ambiguous timestamp block'
    assert boundary(a|{'timestamp_count':2},b)=='edge incident to ambiguous timestamp block'


def test_no_default_category_or_hidden_next_edit_in_evidence():
    validate(row(100,'a','ab'))
    with pytest.raises(ValueError):validate(row(100,'a','ab')|{'high-level':'PLANNING'})
    with pytest.raises(ValueError):validate(row(100,'a','ab')|{'label':'unknown'})
    record={'usable':True,'before':'a','after':'b','category':'IMPLEMENTATION','location':'last_quarter',
            'next_category':'REVISION','next_location':'first_quarter','author':'secret'}
    texts={'a':'before','b':'current'}
    evidence=visible(record,texts,'record')
    assert evidence==visible(record|{'next_category':'PLANNING','next_location':'no_change'},texts,'record')
    assert set(evidence)=={'document','previous_document','previous_category','previous_location'}
    assert visible(record,texts,'artifact')=={'document':'current'}


def test_location_is_first_difference_in_visible_fragment():
    assert location('abcdefgh','abcdefgh')=='no_change'
    assert location('abcdefgh','Xbcdefgh')=='first_quarter'
    assert location('abcdefgh','abXdefgh')=='second_quarter'
    assert location('abcdefgh','abcdXfgh')=='third_quarter'
    assert location('abcdefgh','abcdefg')=='last_quarter'
    assert location('','a')=='first_quarter'
