"""Known-answer transfer, zero-information controls and complete menu boundaries."""
from collections import Counter
import pytest
from runners.stage9.commit_features import predict,check,pair_features,project
from runners.stage9.commit_models import all_models,expanded


def question(key,word,unit=None):
    labels=['blue','green','yellow','red'];i=labels.index(word)
    return {'key':key,'unit':unit or key,'truth':str(i),'evidence':{
        'diff':f'diff --git a/common.py b/common.py\n--- a/common.py\n+++ b/common.py\n@@ -1 +1 @@\n-old = 1\n+{word} = 2\n',
        'candidate_descriptions':['Add '+k+' variable' for k in labels]}}


def test_learned_correspondence_and_surface_null():
    rows=[question(str(i),('blue','green','yellow','red')[i%4]) for i in range(64)]
    models=all_models(rows)
    own=question('unseen-repository','yellow')
    correct=predict(own['evidence'],models['all'])['2']
    assert correct>.8
    for name in ('surface','description_only','uniform','filename_overlap'):
        assert predict(own['evidence'],models[name])==pytest.approx({str(i):.25 for i in range(4)})
    # Equivalent candidate features cannot break ties by option position.
    none=question('none','blue')['evidence'];none['diff']=none['diff'].replace('+blue = 2','+unknown = 2')
    assert predict(none,models['all'])==pytest.approx({str(i):.25 for i in range(4)})


def test_repository_mass_and_permutation():
    rows=[question('one','blue','single')]+[question(str(i),'red','many') for i in range(5)]
    counts=Counter()
    for row in expanded(rows):counts[row['unit']]+=row['weight']
    assert counts['single']==pytest.approx(counts['many'])
    model={'method':'lexical_overlap'};e=rows[0]['evidence'];original=predict(e,model)
    reversed_e={**e,'candidate_descriptions':list(reversed(e['candidate_descriptions']))}
    assert predict(reversed_e,model)=={str(i):original[str(3-i)] for i in range(4)}
    with pytest.raises(ValueError):expanded(rows+[rows[0]])


def test_reader_boundary_and_wording_control():
    e=question('one','blue')['evidence']
    with pytest.raises(ValueError):check({**e,'truth':'0'})
    with pytest.raises(ValueError):check({**e,'candidate_descriptions':['same']*4})
    with pytest.raises(ValueError):check({**e,'diff':e['diff'].replace('@@ -1 +1 @@','@@ -2 +2,2 @@')})
    a=pair_features(e['diff'],'Add blue variable');b=pair_features(e['diff'].replace('+blue','+anything'),'Add blue variable')
    assert project(a,'description_only')==project(b,'description_only')
    with pytest.raises(ValueError):predict(e,{'method':'logistic_pair','features':'all','coefficients':{},'intercept':float('nan')})
