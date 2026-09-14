"""Versioned reserved-reading interface repair; original attempts remain immutable.

DESIGN CHECK: Stage10 scoped repair authority; LESSONS sections 3-5 reread.
NULL and ALTERNATIVE retain every option, original evidence and 256+512 budget.
Only the unscored explanation becomes empty, leaving room for the full vector.
Truncation and malformed support still fail the original literal admission.
Old admissions fail the new source binding. No target answer or scorer changes.
"""
import argparse
from contextlib import contextmanager
import copy
import json
from pathlib import Path
from unittest.mock import patch

from . import ollama, reading_effort
from .contracts import canonical
from .revision_bank import sha

OriginalReaders = reading_effort.Readers


def compact_request(original, *args, **kwargs):
    request = copy.deepcopy(original(*args, **kwargs))
    request['format']['properties']['explanation'] = {'type': 'string', 'const': ''}
    body = json.loads(request['messages'][1]['content'])
    body['response_schema'] = request['format']
    request['messages'][1]['content'] = canonical(body)
    request['messages'][0]['content'] = request['messages'][0]['content'].replace(
        'Keep the explanation to at most 40 words; do not deliberate in that field.',
        'Set explanation to the empty string; spend the response on the complete probability vector.')
    cap = request['options']['num_ctx']
    if sum(len(m['content'].encode('utf-8')) for m in request['messages']) + request['options']['num_predict'] + 512 > cap:
        raise ValueError('compact public prompt exceeds the original context bound')
    return request


class Readers(OriginalReaders):
    def __init__(self, prepared):
        super().__init__(prepared)
        self.sources['runners/stage10/reading_effort_compact.py'] = sha(Path(__file__))


@contextmanager
def profile():
    original = ollama.request_for
    with patch.object(reading_effort, 'Readers', Readers), patch.object(
            ollama, 'request_for', lambda *a, **k: compact_request(original, *a, **k)):
        yield


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['pilot', 'development', 'fit', 'evaluation'])
    parser.add_argument('--output', type=Path, required=True)
    for name in ['prepared', 'admission', 'development', 'policy']:
        parser.add_argument('--' + name, type=Path)
    args = parser.parse_args()
    try:
        with profile():
            if args.action == 'fit':
                reading_effort.fit(args.prepared, args.development, args.admission, args.output)
            else:
                reading_effort.predict(args.prepared, args.output, args.action, args.admission, args.policy)
    except Exception as exc:
        if not (args.output / 'FAILED.json').exists():
            ollama.write_new(args.output / 'FAILED.json', {'at': ollama.now(), 'error': repr(exc)})
        raise


if __name__ == '__main__':
    main()
