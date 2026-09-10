"""Discarded target-matched recipe preparation and short real training pilot.

DESIGN CHECK: C05/X08. Use the 64 completed actual learner-world records from each
family; construct the exact corresponding expert trajectories, then replace the
preassigned half with actual learner states. Same labels budget, count and sources.
NULL: insufficient actual teacher targets fails rather than copying model mistakes.
ALTERNATIVE: exact matching and one complete 8-update epoch at the new context cap.
These pilot worlds/weights can never enter scientific training or confirmation.
"""
import argparse
from pathlib import Path
import time

from runners.stage9.common import REPO, ROOT, closure, digest, freeze, read
from runners.stage9.matching import audit, learner_candidate, match_budget, mixture_keys, replay_row, target_positions
from runners.stage9.recipes import POP, sampled_world
from runners.stage9.train import BASES, train


def prepare(family):
    from transformers import AutoTokenizer
    started = time.time()
    root = ROOT / 'private/pilot-learner' / (family+'-v1')
    complete = read(root / 'COMPLETE.json')
    identity = read(root / 'IDENTITY.json')
    if complete['identity_sha256'] != digest(identity):
        raise ValueError('learner pilot identity differs')
    rows = [read(p)['row'] for p in sorted((root/'units').glob('*.json'))]
    if len(rows) != 64 or len({r['lineage'] for r in rows}) != 64:
        raise ValueError('full actual learner pilot required')
    base = BASES[family]
    tok = AutoTokenizer.from_pretrained(base['model'], revision=base['revision'], local_files_only=True, trust_remote_code=False)
    sources, collections = [], {r['lineage']: r for r in rows}
    for row in rows:
        world = sampled_world(row['lineage'], 'both')
        text = POP.world_log(world, False)
        ids = tok(text+tok.eos_token, add_special_tokens=True).input_ids[:1024]
        sources.append({'key': world['lid'], 'input_ids': ids, 'lineages': [world['lid']],
                        'raw_record': {'text': text, 'domain': world['domain'], 'n_earlier': 0}})
    selected = mixture_keys(sources)
    expert = [replay_row(r) for r in sources]
    candidates = [learner_candidate(tok, r, collections[r['key']]) if r['key'] in selected else replay_row(r) for r in sources]
    budget = sum(len(target_positions(r)) for r in expert)
    mixed = match_budget(candidates, budget, fixed_keys={r['key'] for r in sources}-selected)
    comparison = audit({'expert': expert, 'mixed': mixed})
    if not all(r['input_ids'] == s['input_ids'] and r['labels'] == s['input_ids'] for r, s in zip(expert, sources)):
        raise ValueError('expert replay changed')
    old = read(ROOT/'private/pilot'/(family+'-corpus.json'))
    corpus_identity = {'family': family, 'scope': 'discarded 64-source matched-context training pilot only',
                       'learner_identity': complete['identity_sha256'],
                       'sources': closure([REPO/'runners/stage9'/n for n in ('matched_pilot.py','matching.py','recipes.py','construction.py')]),
                       'matching': comparison, 'assignment': sorted(selected), 'context_cap': 2048,
                       'validation': 'already discarded replay-pilot validation; no new independent validation claim'}
    output = ROOT/'private/pilot-matched'/family
    for name, examples in [('expert', expert), ('mixed', mixed)]:
        freeze(output/(name+'.json'), {'split': 'pilot', 'identity': corpus_identity | {'cell': name},
                                       'examples': examples, 'validation': old['validation'],
                                       'validation_choices': old['validation_choices']})
    receipt = {'family': family, 'matching': comparison, 'wall_seconds': time.time()-started,
               'training_timing_complete': False, 'scientific_training_accepted': False}
    freeze(output/'PREPARATION.json', receipt)
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('operation', choices=['prepare', 'train'])
    p.add_argument('--family', required=True, choices=BASES)
    args = p.parse_args()
    if args.operation == 'prepare':
        print(prepare(args.family))
    else:
        root = ROOT/'private/pilot-matched'/args.family
        train(root/'mixed.json', root/'training-v1', args.family, seed=994901,
              epochs=1, max_length=2048, checkpoint_every=8)
