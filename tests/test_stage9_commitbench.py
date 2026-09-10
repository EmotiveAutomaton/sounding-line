from copy import deepcopy
import pytest
from runners.stage9.commitbench import parse_diff,components,visible,validate_page,PIN

DIFF='diff --git a/f.py b/f.py\n--- a/f.py\n+++ b/f.py\n@@ -1,2 +1,2 @@\n context\n-old\n+new\n'


def test_hunk_known_answer_and_truncation():
    p=parse_diff(DIFF);assert p['added']==['new'] and p['removed']==['old'] and p['context']==['context']
    with pytest.raises(ValueError,match='incomplete'):parse_diff(DIFF.rsplit('+new',1)[0])
    with pytest.raises(ValueError):parse_diff(DIFF+'+extra\n')
    assert parse_diff(DIFF+'\\ No newline at end of file\n')['added']==['new']


def test_insertion_deletion_and_multifile():
    text='diff --git a/f b/f\n--- /dev/null\n+++ b/f\n@@ -0,0 +1 @@\n+one\n'
    assert parse_diff(text)['hunks'][0]['old_count']==0
    assert len(parse_diff(text+DIFF)['hunks'])==2


def test_duplicate_component_transitivity_and_private_fields():
    rows=[{'project':'a','hash':'x','diff':'one'},{'project':'b','hash':'x','diff':'two'},
          {'project':'c','hash':'y','diff':'two'},{'project':'d','hash':'z','diff':'other'}]
    g=components(rows);assert g['a']==g['b']==g['c'] and g['c']!=g['d']
    candidates=['alpha','beta','gamma','delta'];r={'diff':DIFF,'message':'secret','project':'hidden','hash':'truth'}
    assert visible(r,candidates)==visible(r|{'message':'changed','project':'other'},candidates)
    assert set(visible(r,candidates))=={'diff','candidate_descriptions'}


def test_complete_endpoint_row_and_revision_contract():
    row={'hash':'h','diff':DIFF,'message':'stated','project':'repo','split':'train','diff_languages':'py'}
    data={'partial':False,'num_rows_total':1000,'rows':[{'row_idx':i,'row':row,'truncated_cells':[]} for i in range(100)]}
    assert len(validate_page(data,{'X-Revision':PIN},0,1000))==100
    bad=deepcopy(data);bad['rows'][2]['truncated_cells']=['diff']
    with pytest.raises(ValueError,match='truncated'):validate_page(bad,{'X-Revision':PIN},0,1000)
    with pytest.raises(ValueError,match='snapshot'):validate_page(data,{'X-Revision':'wrong'},0,1000)
    data['rows'].pop()
    with pytest.raises(ValueError,match='range'):validate_page(data,{'X-Revision':PIN},0,1000)
