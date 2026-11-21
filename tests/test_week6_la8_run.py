import numpy as np
import pytest

from runners.drive.cards.week6_la8_run_v1 import fit_meetings, meeting_block
from runners.drive.cards.week6_la78_models_v1 import talk_crossproducts


def test_only_single_targets_and_complete_observed_windows_contribute():
    def intervals(s, *pairs):
        return [dict(speaker=s,start=a,end=b) for a,b in pairs]
    acts = intervals("b",(10,11),(80,81),(140,142),(180,182)) + intervals("c",(180,182))
    laughs = [dict(speaker=s,start=t,end=t+.2,label="vocal")
              for s,t in (("a",10),("a",80),("b",81),("a",140),("a",180))]
    words = intervals("b",(74,81),(142,148)) + intervals("c",(82,84),(143,148))
    meta = dict(corpus="ICSI",scenario=False,duration=240,
                speakers={s:{"role":None} for s in ("a","b","c")})
    block, counts = meeting_block(acts,laughs,words,meta,"elapsed")
    assert counts["single"]==3
    assert counts["joined"]==1 and counts["unjoined"]==1 and counts["truncated"]==1
    assert block[2]==2


def test_known_effect_and_undefined_split_halves():
    rng=np.random.default_rng(83)
    blocks=[]
    for _ in range(4):
        rows=[]
        for i in range(24):
            phase, before = rng.uniform(.05,.8,2)
            joined = bool(i%2)
            after = .2+.2*before+.1*phase-.035*(not joined)
            rows.append(dict(phase=phase,before=before,joined=joined,after=after))
        blocks.append(talk_crossproducts(rows))
    result=fit_meetings(blocks)
    assert result["effect_points"]==pytest.approx(-3.5)
    assert result["interval"]==pytest.approx([-3.5,-3.5])
    assert result["status"]=="registered bar met" and result["undefined_draws"]==0
    assert fit_meetings([talk_crossproducts([])])["status"]=="could not say"
