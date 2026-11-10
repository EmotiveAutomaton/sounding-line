import numpy as np
from runners.drive.cards import week5_go3_analysis as a,week5_go_revisions as s


def reference_distance(left,right):
    row=list(range(len(left)+1))
    for i,b in enumerate(right,1):
        new=[i]
        for j,c in enumerate(left,1):new.append(min(new[-1]+1,row[j]+1,row[j-1]+(c!=b)))
        row=new
    return row[-1]


def test_bit_vector_matches_independent_exact_distance():
    rng=np.random.default_rng(12)
    for _ in range(200):
        x=rng.integers(0,6,rng.integers(0,60)).tolist();y=rng.integers(0,6,rng.integers(0,60)).tolist()
        assert a.levenshtein(x,y)==reference_distance(x,y)


def test_fast_feature_vector_exactly_matches_frozen_definition():
    for left,right in [('a b c','a b d'),('Line one.\nLink https://example.org','Line one. Link https://example.org/x'),('','added text'),('remove everything','')]:
        assert a.features(left,right)==s.diff_features(left,right)
