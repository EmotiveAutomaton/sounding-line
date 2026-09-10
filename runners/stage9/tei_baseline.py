"""Local genetic-edition offered-replacement baseline, strictly qualitative.

DESIGN CHECK: H04 development/readiness only, one famous work. NULL: no textual
preference returns equal probabilities; ALTERNATIVE: literal copying is preferred by
the copied-text rival. No intent, global chronology or population claim is licensed.
"""
import math
from pathlib import Path
import time

from runners.stage9.common import ROOT, Units, closure, digest, freeze, read, write
from runners.stage9.runtime import execute
from runners.stage9.scoring import log_score


def run(prepared, output):
    prepared, output = Path(prepared), Path(output)
    tasks = read(prepared / 'tasks.json')
    identity = {'preparation': digest(read(prepared / 'IDENTITY.json')), 'tasks': digest(tasks),
                'source': closure([Path(__file__), Path(__file__).with_name('features.py'), Path(__file__).with_name('runtime.py'), Path(__file__).with_name('reader.py')]),
                'operation': 'fixed copied-text similarity vs equal offered probabilities; one-work qualitative diagnostic'}
    units = Units(output, identity)
    if (output / 'COMPLETE.json').exists():
        return read(output / 'COMPLETE.json')
    started = time.monotonic()
    for case in tasks:
        key = {'case': case['key']}
        if units.get(key) is not None:
            continue
        task = {'operation': 'copy_baseline', 'copy_source': case['case']['local_before']}
        path = output / 'predictions' / (digest(key) + '.json')
        if path.exists():
            result = read(path)
        else:
            result = execute(case['evidence'], task)
            freeze(path, result)
        if not result['accepted']:
            raise ValueError('copied-text capsule failed: ' + str(result.get('error')))
        # Ground truth is consumed only after the reader result is frozen above.
        probabilities = result['prediction']['probs']
        score = log_score(probabilities, case['truth'])
        neutral = -math.log(len(case['evidence']['options']))
        maximum = max(probabilities.values())
        ties = sorted(k for k, v in probabilities.items() if v == maximum)
        units.put(key, {'case': case['key'], 'copied_text_log_score': score, 'uniform_log_score': neutral,
                        'difference': score - neutral, 'correct_unique_argmax': ties == [case['truth']],
                        'tied_maximum': len(ties) > 1, 'independent_unit': case['unit']})
    rows = [units.get({'case': r['key']}) for r in tasks]
    result = {'identity_sha256': digest(identity), 'completed': True, 'cases': len(rows),
              'independent_works': len({r['independent_unit'] for r in rows}),
              'descriptive_mean_log_score_difference': math.fsum(r['difference'] for r in rows) / len(rows),
              'unique_argmax_matches': sum(r['correct_unique_argmax'] for r in rows),
              'ties': sum(r['tied_maximum'] for r in rows), 'wall_seconds': time.monotonic() - started,
              'ordinary_predictive_baseline_executed': True, 'published_predictive_result_reproduction': False,
              'claim_ceiling': 'qualitative local offered-replacement diagnostic in one famous work; no population CI, intent inference or global chronology'}
    freeze(output / 'COMPLETE.json', result)
    write(ROOT / 'intake/SGA_BASELINE.json', result)
    return result


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('prepared', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.prepared, args.output), sort_keys=True))
