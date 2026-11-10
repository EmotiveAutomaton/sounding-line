import numpy as np
from runners.drive.cards.week5_at_shared import analyze
from runners.drive.cards.week5_at_grid import grid


def test_shared_reader_identical_population_has_exact_zero_gain():
    rng=np.random.default_rng(3);rows=[]
    for w in range(12):
        for i in range(20):
            p=float(rng.normal());r={k:float(rng.normal()) for k in ('length','log_frequency','sentence_start','after_punctuation','on_screen','session_surprisal')}
            rows.append(dict(r,writer=str(w),population_surprisal=p,genre_population_surprisal=p,log_pause=p+rng.normal()))
    result=analyze(rows,20)
    assert result['primary']['effect']==0 and result['primary']['state']=='against'


def test_grid_preserves_every_family_and_conditional_branch():
    cards=grid(['creative','argumentative']);ids={r['card'] for r in cards}
    assert {'AT1','AT2.e','AT3','AT4','AT4.engine','AT1.s','LA1','LA1.i'}<=ids
    assert len([r for r in cards if r['card'].startswith('AT2.') and 'context_length' in r['config']])==6
    assert all(r['ready_only_after_owner_design_fixture_review'] for r in cards)
