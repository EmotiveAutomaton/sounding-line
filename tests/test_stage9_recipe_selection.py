import copy
import pytest
from runners.stage9.recipe_selection import choose
from runners.stage9.training_jobs import FITS


def rows():
    return [{'family':family,'recipe':recipe,'seed':seed,'status':'COMPLETE',
             'score':(-.1 if seed==9001 else -10.) if recipe=='both_mixed' else -1.,
             'development_sha256':family+'-common-development'} for family,recipe,seed in FITS]


def test_all_seeds_determine_winner_and_ties_are_order_invariant():
    cells=rows();result=choose(cells,'scientific')
    for group in result['families'].values():
        assert group['selected_recipe']=='both_expert'  # lexical tie among complete -1 recipes
        assert group['selected_seeds']==[9001,9002,9003]
        assert group['recipes']['both_mixed']['mean_development_log_score']<-6.
    assert choose(list(reversed(cells)),'scientific')==result
    assert result['assigned_fits']==24 and result['scientific_admission'] is False


def test_failed_seed_stays_visible_and_cannot_win_on_survivors():
    cells=rows()
    for row in cells:
        if row['recipe']=='both_mixed':
            row['score']=0.
            if row['seed']==9003:row['status']='FAILED';del row['score']
    result=choose(cells,'scientific')
    for group in result['families'].values():
        assert not group['recipes']['both_mixed']['complete_seed_set']
        assert len(group['recipes']['both_mixed']['seeds'])==3
        assert group['selected_recipe']!='both_mixed'
    for row in cells:
        if row['family']=='qwen':row['status']='NOT_RUN'
    assert choose(cells,'scientific')['families']['qwen']['selected'] is False
    assert choose(cells,'scientific')['families']['smollm']['selected'] is True


def test_missing_seed_mismatched_development_and_unfinished_grid_refuse():
    cells=rows()
    with pytest.raises(ValueError,match='every assigned'):choose(cells[:-1],'scientific')
    cells[0]['development_sha256']='different'
    with pytest.raises(ValueError,match='different validation'):choose(cells,'scientific')
    cells[0]['status']='RUNNING'
    with pytest.raises(ValueError,match='unfinished'):choose(cells,'scientific')
