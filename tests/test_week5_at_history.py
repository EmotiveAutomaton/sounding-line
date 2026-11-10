"""AT1 metadata-only donor budget and leakage controls."""
import pytest
from runners.drive.cards.week5_at_history import equal_budget_history


def bank():
    return {w:[dict(writer=w,session=w+str(j),timestamp=j*10,end_at=j*10+1,
                    genre='creative',prompt='old',training_sequences=[['a','b','c']*(j+1)])
               for j in range(5)] for w in ('own','a','b','c','d','e')}


def test_pooled_donors_match_exact_token_budget_and_count():
    b=bank();target=dict(writer='own',timestamp=32,prompt='current')
    history=equal_budget_history(b,target,['a','b','c','d','e'],'creative')
    assert history[-1]==sum(3*(j+1) for j in range(4))


def test_future_prompt_and_wrong_genre_are_not_borrowed():
    b=bank();target=dict(writer='own',timestamp=12,prompt='old')
    assert equal_budget_history(b,target,['a'],'creative') is None
    target['prompt']='new'
    assert equal_budget_history(b,target,['a'],'argumentative') is None
    assert equal_budget_history(b,target,['a'],'creative')[-1]==9


def test_recipient_and_duplicate_donors_refused():
    b=bank();target=dict(writer='own',timestamp=32,prompt='current')
    with pytest.raises(ValueError):equal_budget_history(b,target,['own'],'creative')
    with pytest.raises(ValueError):equal_budget_history(b,target,['a','a'],'creative')
