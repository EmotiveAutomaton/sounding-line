from runners.stage9.commitbench_baseline import menu,pair_features,normalize

DIFF='diff --git a/f.py b/f.py\n--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-old_name()\n+new_name()\n'


def test_menu_preserves_real_messages_and_other_repositories():
    rows=[{'diff':DIFF,'message':m,'key':str(i),'unit':str(i),'languages':['py']} for i,m in enumerate(
        ['rename old name','change output text','remove unused import','add test case','update package version'])]
    m=menu(rows[0],rows);assert len(m['candidate_keys'])==4 and len(set(m['candidate_keys']))==4
    assert m['evidence']['candidate_descriptions'][int(m['truth'])]==rows[0]['message']
    assert menu(rows[0],[r|{'unit':'0'} for r in rows]) is None


def test_planted_overlap_and_content_based_order():
    good=pair_features(DIFF,'rename old name to new name');bad=pair_features(DIFF,'add import logging module')
    assert good['change_overlap']>bad['change_overlap']
    p=normalize([4*good['change_overlap'],4*bad['change_overlap'],0,0])
    assert max(p,key=p.get)=='0' and min(p.values())>0 and abs(sum(p.values())-1)<1e-9
    assert normalize([0,0,0,0])=={'0':.25,'1':.25,'2':.25,'3':.25}
