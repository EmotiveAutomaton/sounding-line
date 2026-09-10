"""Reuse verified source construction for the other pinned tokenizer, without resampling.

DESIGN CHECK: C05. Identical source lineages and text, tokenizer-specific exposure counts.
This is still a candidate pool; no target matching or scientific fit is accepted here.
"""
import time

from runners.stage9.common import REPO, ROOT, closure, digest, file_hash, freeze, read
from runners.stage9.train import BASES


def main():
    from transformers import AutoTokenizer
    started = time.time()
    source = ROOT / 'private/training-pools/qwen'
    output = ROOT / 'private/training-pools/smollm'
    base = BASES['smollm']
    tok = AutoTokenizer.from_pretrained(base['model'], revision=base['revision'], local_files_only=True, trust_remote_code=False)
    receipts = {}
    for coverage in ('original', 'both'):
        path = source / (coverage + '.json')
        original = read(path)
        identity = {**original['identity'], 'base': base,
                    'retokenized_source_sha256': file_hash(path),
                    'retokenizer': closure([REPO / 'runners/stage9/retokenize_pool.py'])}
        for row in original['candidate_examples']:
            raw = tok(row['raw_record']['text'] + tok.eos_token, add_special_tokens=True).input_ids
            ids = raw[:1024] if coverage == 'original' else raw
            row.update(input_ids=ids, raw_tokens=len(raw), historical_tokens_discarded=len(raw)-len(ids))
        freeze(output / (coverage + '.json'), {**original, 'identity': identity})
        receipts[coverage] = {'identity_sha256': digest(identity), 'examples': len(original['candidate_examples']),
                              'supervised_tokens_available': sum(len(r['input_ids'])-1 for r in original['candidate_examples']),
                              'historical_tokens_discarded': sum(r['historical_tokens_discarded'] for r in original['candidate_examples']),
                              'source_sha256': file_hash(path), 'lineages': len(original['private_worlds'])}
    freeze(output / 'PREPARATION.json', {'family': 'smollm', 'paired_source': 'verified Qwen candidate-pool source texts',
                                        'arms': receipts, 'wall_seconds': time.time()-started,
                                        'scientific_training_accepted': False})


if __name__ == '__main__':
    main()
