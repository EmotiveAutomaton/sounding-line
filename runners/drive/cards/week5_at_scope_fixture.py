"""Native complete-source projection fixture; no synthetic completion receipts."""
from pathlib import Path
from . import week5_at_scope as at, week5_la_scope as la
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal


def run(output, inputs, config, verifying=False):
    if inputs or config: raise ValueError('Fixture takes no human inputs')
    root = Path(output); source = root / 'constructed-source'; data = source / 'output'
    index = []; meta = {}; acts = []; laughs = []
    for i in range(20):
        rows = [dict(row_key=f'{i:04d}:{j}', writer=f'w{i}', session=f's{i}',
                     genre='creative' if i < 12 else 'argumentative', final_prefix='',
                     at_typing_prefix='', at_typing_frozen20=i % 5 == 0) for j in range(4)]
        name=f'sessions/session-{i:04d}.json.gz'; gzip_equal(data/name, dict(rows=rows, binding='constructed'))
        index.append(dict(file=name, sha256=filehash(data/name), words=4))
        meta[f'm{i}'] = dict(corpus='AMI' if i < 12 else 'ICSI', speakers={})
        acts.append(dict(meeting=f'm{i}', id=f'act{i}')); laughs.append(dict(meeting=f'm{i}', id=f'laugh{i}'))
    write_equal(data/'INDEX.json', index)
    for name, value in [('METADATA.json.gz', meta), ('ACTS.json.gz', acts), ('LAUGHS.json.gz', laughs)]:
        gzip_equal(data/name, value)
    # Bypass only the external completion gate, explicitly fixture-only; do not
    # fabricate native COMPLETE markers. Real runtime supplies this gate.
    old_at, old_la, old_hash_at, old_hash_la = at.authenticate, la.authenticate, at.filehash, la.filehash
    at.authenticate=la.authenticate=lambda path: source
    def digest(path):
        return 'constructed-source-binding' if Path(path).name == 'COMPLETE.json' else filehash(path)
    at.filehash=la.filehash=digest
    try:
        (at.verify if verifying else at.execute)(root/'AT-sample', {'source_root':str(source)}, {'writers':10})
        (at.verify if verifying else at.execute)(root/'AT-full', {'source_root':str(source)}, {'typing_population':'full'})
        (la.verify if verifying else la.execute)(root/'LA-sample', {'source_root':str(source)}, {'meetings':10})
    finally:
        at.authenticate, la.authenticate, at.filehash, la.filehash=old_at, old_la, old_hash_at, old_hash_la
    batches=read(root/'AT-full/BATCHES.json')
    if sum(b['words'] for b in batches if b['context']=='at_typing') != 80:
        raise ValueError('Full typing union lost support')
    original20=[b for b in batches if b['context']=='at_typing' and int(b['file'].split('-')[1])%5==0]
    if sum(b['words'] for b in original20) != 16: raise ValueError('First-20 support changed')
    if len(gzread(root/'LA-sample/ACTS.json.gz')) != 10: raise ValueError('Meeting projection failed')
    receipt=dict(fixture_only=True, no_fake_completion=True, whole_writer_scope=True,
                 whole_meeting_scope=True, full_typing_union=True, original20_reusable=True)
    if verifying:
        if read(root/'FIXTURE.json') != receipt: raise ValueError('Scope fixture differs')
        return dict(verified=True, complete_projection_replay=True)
    write_equal(root/'FIXTURE.json', receipt); return dict(status='complete', fixture_only=True)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)


if __name__ == '__main__':
    import argparse, json
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--verify', action='store_true');a=p.parse_args()
    print(json.dumps((verify if a.verify else execute)(a.output, {}, {})))
