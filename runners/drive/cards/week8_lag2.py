"""Replay the frozen 0057 computation in a new campaign directory.

DESIGN CHECK: LESSONS §§3–5. Every selected cell, clock, exclusion and both
gap readings must reproduce. One mismatch withholds the whole contribution.
"""
from pathlib import Path
import sys

from . import week7_gear, week8_gear as gear
from runners.stage14.common import read, freeze, filehash

PREV = gear.REPO/'.agent-state/drive-20261115/week7-phase1'
OLD = week7_gear.ROOT/'LAG-next-prompt-0057-20261123'
SHEET = gear.REPO/'results/phase_2_4_stage_15/WEEK7/LAG_0057_COST_STOP.json'
UNIT = 'LAG2-0057-independent-replay'


def former():
    if str(PREV) not in sys.path:
        sys.path.insert(0,str(PREV))
    import lag_units
    return lag_units


def design(unit):
    if unit != UNIT:
        raise ValueError('Only the commissioned 0057 replay is allowed')
    filing=read(SHEET)
    assert filing['full_write_through'] and filing['terminal']==filehash(OLD/'FAILED.json')
    review=read(OLD/'LOCAL_REVIEW.json')
    expected=review['pins'].copy()
    prior=OLD/'execute_INTERNAL.json'
    cells=sorted((OLD/'execute_cells').glob('*.json'))
    replays=sorted((OLD/'verify_cells').glob('*.json'))
    registered=read(prior)
    ordered=registered['selection']
    if len(cells)!=len(ordered) or len(cells)!=649 or len(replays)!=28:
        raise ValueError('Checkpoint census differs')
    for i,p in enumerate(cells):
        row=read(p)
        if row['key']!=ordered[i] or row['result']!=registered['cells'][ordered[i]]:
            raise ValueError('First-pass checkpoint differs')
    for p in replays:
        if filehash(p)!=filehash(OLD/'execute_cells'/p.name):
            raise ValueError('Preserved earlier replay differs')
    return dict(source='openesm-0057',peak=1.4,cap=59_000,operations=['verify'],expected=expected,
                inputs=[*map(Path,expected),SHEET,prior,OLD/'FAILED.json',OLD/'LOCAL_REVIEW.json',
                        gear.REPO/'docs/design/stage-15/week8/LAG2.md',*cells,*replays])


def fixture():
    return former().fixture()


def run(unit,d,mode):
    if unit!=UNIT or mode!='verify':
        raise ValueError('Invalid replay target')
    freeze(d/'verify_INTERNAL.json',former().run('0057',d,'verify'))


def check(unit,d):
    first=filehash(OLD/'execute_INTERNAL.json')
    replay=filehash(d/'verify_INTERNAL.json')
    if unit!=UNIT or replay!=first:
        raise ValueError('Complete independent replay differs from original')
    for p in (OLD/'execute_cells').glob('*.json'):
        if filehash(p)!=filehash(d/'verify_cells'/p.name):
            raise ValueError('Individual replay differs from original')
    return dict(first_pass_sha256=first,independent_replay_sha256=replay,cells=649)
