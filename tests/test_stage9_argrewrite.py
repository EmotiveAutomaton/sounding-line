import copy
import pytest
from runners.stage9.argrewrite import indices, units_from_tables, visible, future_visible, padded_row


def row(i, text, revision, purpose, aligned=None):
    return {'Sentence Index': i, 'Sentence Content': text, 'Revision Index Level 0': revision,
            'Revision Purpose Level 0': purpose, 'Aligned Index': aligned}


def test_canonical_many_to_many_and_multilabel_exclusion():
    units, documents, counts = units_from_tables({
        'old': [row(1, 'one', 4, 'Evidence', '1,2'), row(2, 'two', 4, 'Evidence', '1,2'),
                row(3, 'mixed', '5,9', 'Evidence,Claims/Ideas', 3)],
        'new': [row(1, 'three', 4, 'Evidence', '1,2'), row(2, 'four', 4, 'Evidence', '1,2'),
                row(3, 'mixed revised', '5,9', 'Evidence,Claims/Ideas', 3)]})
    assert units[0]['old'] == 'one two' and units[0]['new'] == 'three four'
    assert units[0]['usable'] and units[0]['fine'] == 'evidence'
    assert not units[1]['usable'] and units[1]['exclusion'] == 'multi-purpose unit'
    assert units[1]['source_rows'][0]['revision_indices'] == [5,9]
    assert counts['compound_alignment_rows'] == 4
    assert documents['old'] == 'one two mixed'
    assert indices('3,4,7') == [3,4,7]
    with pytest.raises(ValueError): indices('1.2')


def test_future_projection_never_sees_future_text_or_target_location():
    essay = {'future_usable': True, 'drafts': {'1':'earlier','2':'current','3':'FUTURE SECRET'},
             'units': [{'cycle':'12','usable':True,'fine':'evidence'},
                       {'cycle':'23','usable':True,'fine':'claim','old':'secret target-selected span'}]}
    a = future_visible(essay,'artifact'); r = future_visible(essay,'record')
    changed = copy.deepcopy(essay);changed['drafts']['3']='CHANGED';changed['units'][1]['fine']='reasoning'
    assert future_visible(changed,'artifact') == a == {'text':'current'}
    assert future_visible(changed,'record') == r
    assert r['earlier_labels'] == ['evidence']
    assert visible({'usable':True,'old':'before','new':'after','fine':'claim'},'artifact') == {'text':'after'}
    with pytest.raises(ValueError):future_visible(essay | {'future_usable':False},'record')


def test_ragged_source_row_preserves_blank_declared_columns():
    header = list(row(1,'unchanged',None,None))
    parsed = padded_row(header,(1,'unchanged'))
    assert parsed == row(1,'unchanged',None,None)
    units, _, counts = units_from_tables({'old':[parsed], 'new':[parsed]})
    assert units == [] and counts['rows_without_revision_unit'] == 2


def test_source_add_delete_markers_remain_explicit():
    units, _, _ = units_from_tables({'old':[row(1,'removed',1,'Evidence','DELETE')],
                                     'new':[row(1,'added',2,'Claims/Ideas','ADD')]})
    assert units[0]['new'] == '' and units[1]['old'] == ''
    assert units[0]['source_rows'][0]['alignment_source'] == 'DELETE'
    assert units[1]['source_rows'][0]['aligned_indices'] == []
    with pytest.raises(ValueError):units_from_tables({'old':[row(1,'x',1,'Evidence','ADD')],'new':[]})
