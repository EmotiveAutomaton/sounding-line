"""Ordered BT slider diaries, using the established three forms and native replay."""
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

from . import week6_bt_forms_v1 as forms
from . import week6_br_v1 as br
from .batch_runtime import filehash, freeze, read

# Member, event item, outcomes in the commissioned tie order, scale floor, release pin.
SPECS = {
    '0055': ('family_conflict', ('sad', 'anxious', 'angry'), 1,
             'c3b3db921eca4a01b9ed05f9eefe3e3e36fa157219b6fc9d3a7f0667abb37d4e'),
    '0023': ('dealt_stress', ('felt_overwhelm',), 0,
             'c3bb60a810c91cb44ade5ed95800a184276fe454ed14652c1d961dcb3fbf7979'),
}

def prepare(frame, member, replay):
    event, feelings, floor, _ = SPECS[member]
    if frame.id.isna().any() or frame.day.isna().any() or (frame.day % 1 != 0).any():
        raise ValueError('Missing identity or invalid study day')
    ratings = frame[[event, *feelings]]
    if ((~ratings.isin(range(floor, 101))) & ratings.notna()).any().any():
        raise ValueError('Rating outside the published scale')
    grade = frame[event].to_numpy(float) - floor
    data, grades, half, gap = forms.project(frame, {event: grade}, feelings)
    return forms.prepare(data, grades, half, gap, replay)

def fixture(member):
    event, feelings, floor, _ = SPECS[member]
    frame = pd.DataFrame({'id': np.repeat(np.arange(16), 60),
                          'day': np.tile(np.repeat(np.arange(1, 11), 6), 16)})
    grade = np.tile([0, 0, 1, 3, 2, 0], 160)
    frame[event] = grade + floor
    for key in feelings:
        frame[key] = 10 + grade * (1 + frame.id % 4)
    frame.loc[frame.id == 0, event] = np.nan
    frame.loc[(frame.id == 1) & (frame.day <= 4), event] = floor
    original = prepare(frame, member, False)
    replay = prepare(frame, member, True)
    for name, panels in original.items():
        for form, sides in panels.items():
            for a, b in zip(sides, replay[name][form]):
                np.testing.assert_allclose(a['b'], b['b'], atol=1e-10)
                assert np.isnan(a['b'][0])
            if form == 'PST5':
                assert np.isnan(sides[0]['b'][1])
            if form == 'PST4':
                np.testing.assert_allclose(sides[0]['b'][3] / sides[0]['b'][2], 4/3)
    frame.loc[0, event] = floor - 1
    try:
        prepare(frame, member, False)
    except ValueError:
        return
    raise AssertionError('Out-of-range code accepted')

def run(member, replay, dest):
    event, feelings, floor, pin = SPECS[member]
    cfg = read(Path('.agent-state/data_collection_root.json'))
    root = Path(cfg['root'])
    if not cfg['repair_hold'] or root.drive.lower() != 'c:' or root.name != br.ROOT_NAME:
        raise ValueError('Temporary root changed')
    if filehash(root/'DRT1_MANIFEST.json') != br.MANIFEST:
        raise ValueError('Temporary root manifest changed')
    directory = root / 'incoming' / ('openesm-' + member)
    manifest = directory / 'MANIFEST.json'
    if filehash(manifest) != pin:
        raise ValueError('Release manifest changed')
    entry, = read(manifest)['files']
    source = directory / entry['file']
    if source.parent != directory or filehash(source) != entry['sha256']:
        raise ValueError('Diary source changed')
    frame = pd.read_csv(source, sep='\t', usecols=['id','day',event,*feelings], dtype={'id': str})
    # BR splits on recorded days. An undated prompt cannot enter either side.
    dated = frame.dropna(subset=['day']).copy()
    panels = prepare(dated, member, replay)
    support = {}
    for name, variants in panels.items():
        support[name] = {}
        for form, (a, b) in variants.items():
            ok = np.isfinite(a['b']) & np.isfinite(b['b'])
            prompts = sum(np.sum(s['n0'][ok] + s['n1'][ok]) for s in (a,b))
            support[name][form] = dict(people=int(ok.sum()), paired_prompts=int(prompts))
    if replay:
        assert support == read(dest/'SUPPORT.json')
    else:
        freeze(dest/'SUPPORT.json', support)
    def guard():
        if (dest/'STOP_REQUEST.json').exists():
            raise RuntimeError('Stop requested')
    rows = forms.score(panels, member, guard)
    result = dict(member=member, people=frame.id.nunique(), reports=len(frame), rows=rows, support=support,
                  undated_prompts=len(frame)-len(dated), people_with_dates=dated.id.nunique())
    if replay:
        br.verify_metric_tree(read(dest/'ORIGINAL.json'), result)
    freeze(dest/('AUDIT.json' if replay else 'ORIGINAL.json'), result)

if __name__ == '__main__':
    member = sys.argv[1]
    if len(sys.argv) == 2:
        for phase in ('fixture', 'execute', 'verify'):
            subprocess.run([sys.executable, '-B', '-m', __spec__.name, member, phase], check=True)
    elif sys.argv[2:] == ['fixture']:
        fixture(member)
    elif sys.argv[2:] in (['execute'], ['verify']):
        run(member, sys.argv[2] == 'verify', Path(os.environ['PST8_RESULT']).parent)
    else:
        raise SystemExit('Unknown operation')
