"""Authenticate replayed ATL2 checkpoints after the registered CPU or drain stop."""
import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.stage14.common import filehash, freeze, read

AUDIT = 'ATLAS_COVERAGE.json'


def checkpoint_receipt(directory, sequence):
    progress = read(directory/'ATLAS_PROGRESS.json') if (directory/'ATLAS_PROGRESS.json').exists() else {'verified':0,'planned':len(sequence)}
    folder = directory/'verified_cells'
    files = sorted(folder.glob('*.json'))
    n = len(files)
    # Each cell is atomically saved after its two independent fits agree.
    # A forced exit can fall between that save and its progress update.
    if (progress['planned']!=len(sequence) or progress['verified'] not in (n,n-1)
            or n>len(sequence) or [p.name for p in files]!=[f'{i:04}.json' for i in range(n)]):
        raise ValueError('Checkpoint names or progress disagree with the frozen order')
    checksums = {}
    for file, key in zip(files,sequence):
        digest = filehash(file)
        cell = read(file)
        if file.is_symlink() or (cell['event'],cell['feeling'],cell['scope'])!=key or filehash(file)!=digest:
            raise ValueError('Changed or out-of-order atlas checkpoint')
        checksums[file.name] = digest
    return dict(checksums=checksums,planned=dict(Counter(k[2] for k in sequence)),
                reached=dict(Counter(k[2] for k in sequence[:n])))


def capture(directory):
    from runners.drive.cards import week8_atl2 as atlas
    from tools.week8_sealed import STATE
    failed = directory/'FAILED.json'
    if (directory!=atlas.gear.ROOT/atlas.UNIT or not failed.is_file()
            or any((directory/p).exists() for p in ('COMPLETE.json','ATLAS_COMPLETE.json'))):
        raise ValueError('Require the terminal of the registered unfinished atlas')
    term = read(failed)
    if (term.get('card'),term.get('unit'),term.get('reason'))!=('ATL2',atlas.UNIT,'Row allowance or campaign drain'):
        raise ValueError('Only the registered allowance or campaign drain permits coverage filing')
    reservation = directory/'RESERVATION.json'
    res = read(reservation)
    review = STATE/'reviews'/(atlas.UNIT+'.json')
    pins = res['pins']
    for path in [review,Path(atlas.__file__),atlas.PUBLIC,atlas.REG/'pooled.csv',atlas.REG/'items.csv',
                 atlas.INTERNAL/'verify_INTERNAL.json',atlas.INTERNAL/'COMPLETE.json']:
        if pins.get(str(path))!=filehash(path):
            raise ValueError('Frozen roster, runner or review differs from admission')
    usage = read(directory/'EXECUTE_JOB_USAGE.json')
    cost = read(directory/'COST.json')
    charged = cost['charged_cpu_seconds']
    if (res['card']!='ATL2' or res['reserved_cpu_seconds']!=20000
            or cost['reservation_sha256']!=filehash(reservation)
            or charged!=usage['cpu_seconds'] or not usage['includes_all_descendants_and_exited_processes']):
        raise ValueError('Unreconciled terminal cost')
    if charged+12<res['reserved_cpu_seconds'] and datetime.fromisoformat(term['at'])<atlas.gear.DRAIN:
        raise ValueError('Neither the CPU stop margin nor the campaign drain was reached')
    public, member, _ = atlas.frozen_roster()
    sequence = []
    for i,key in enumerate(public):
        if i<len(member):
            sequence.append(member[i])
        sequence.append(key)
    audit = checkpoint_receipt(directory,sequence)
    audit.update(terminal_sha256=filehash(failed),review_sha256=filehash(review),
                 reservation_sha256=filehash(reservation),cost_sha256=filehash(directory/'COST.json'),
                 charged_cpu_seconds=charged,scope='completed replayed cells in frozen order')
    freeze(directory/AUDIT,audit)
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    a=capture(parser.parse_args().directory.resolve())
    print('Replayed cells by scope:',a['reached'],'of',a['planned'])
