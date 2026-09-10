import itertools
import random

from runners.stage9.text_overlap import Overlaps, words


def exhaustive(texts):
    result = set()
    for (ga, a), (gb, b) in itertools.combinations(texts, 2):
        a, b = words(a), words(b)
        if min(len(a), len(b)) < 100:
            continue
        sa = {tuple(a[i:i+5]) for i in range(len(a)-4)}
        sb = {tuple(b[i:i+5]) for i in range(len(b)-4)}
        n = len(sa & sb)
        if 20*n >= 17*len(sa | sb) or 20*n >= 19*min(len(sa),len(sb)):
            result.add(tuple(sorted((ga,gb))))
    return result


def test_complete_index_matches_exhaustive_for_containment_near_and_unrelated():
    rng = random.Random(1906)
    texts = []
    for family in range(8):
        base = [f'f{family}w{i}' for i in range(220)]
        for variant in range(5):
            seq = list(base)
            for at in rng.sample(range(len(seq)), variant*3):
                seq[at] = f'edit{at}'
            if variant == 4:
                seq = [f'prefix{i}' for i in range(400)] + base + [f'suffix{i}' for i in range(1000)]
            texts.append((f'{family}:{variant}', ' '.join(seq)))
    audit = Overlaps()
    for g,t in texts: audit.add(g,t)
    result = audit.run()
    assert {tuple(e['groups']) for e in result['long_overlap_edges']} == exhaustive(texts)
    assert len(result['long_overlap_edges']) > 0


def test_short_collision_is_not_a_long_source_link_and_duplicates_do_not_add_units():
    audit = Overlaps()
    audit.add('a','A shared phrase')
    audit.add('a','a SHARED phrase')
    audit.add('b','a shared phrase','shared_stimulus')
    result = audit.run()
    assert result['input_text_occurrences'] == 3
    assert result['unique_texts_within_groups'] == 2
    assert result['long_overlap_edges'] == []
    assert len(result['exact_collision_buckets']) == 1


def test_long_low_diversity_text_and_roles_are_not_dropped():
    audit = Overlaps()
    for g in ('a','b'):
        audit.add(g,'word '*150,'shared_stimulus')
        audit.add(g,'word '*150,'artifact')
    result = audit.run()
    assert len(result['long_overlap_edges']) == 1
    assert result['long_overlap_edges'][0]['containment'] == 1
    assert result['long_overlap_edges'][0]['witnesses'][0]['roles'] == ['artifact','shared_stimulus']
