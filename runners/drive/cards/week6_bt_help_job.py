"""Helping occurrence in the first Pronizius diary burst."""
import os
from pathlib import Path
import sys
import subprocess

import numpy as np
import pandas as pd

from . import week6_bt_forms_v1 as forms
from . import week6_br_v1 as br
from .batch_runtime import filehash, freeze, read

FEELINGS = ('valence_mood', 'calmness_mood', 'energy_mood', 'stressed')
PIN = '1515dc16833cec14170b5868ce40a0b6cd347b6df2aaf9074923c686fa11ce12'

def occurrence(frame, replay):
    x = frame.helping_binary
    if (x.notna() & ~x.isin([0, 1])).any():
        raise ValueError('Unknown occurrence code')
    ratings = frame[list(FEELINGS)]
    if ((ratings < 0) | (ratings > 100)).any().any():
        raise ValueError('Rating outside source anchors')
    if frame.id.isna().any() or frame.day.isna().any() or (frame.day % 1 != 0).any():
        raise ValueError('Missing identity or invalid day')
    data, _, half, thirds = forms.project(frame, {'helping': x.to_numpy(float)}, FEELINGS)
    return {form: forms.ladder.half_panel(data, split, replay)[0]
            for form, split in [('PST1',half),('PST5',thirds)]}

def fixture():
    frame = pd.DataFrame({'id': np.repeat(np.arange(8), 60),
                          'day': np.tile(np.repeat(np.arange(10),6),8)})
    frame['helping_binary'] = np.tile([0,1,1,0,0,1],80)
    for feeling in FEELINGS:
        frame[feeling] = 40 + frame.helping_binary * (1+frame.id) / 2
    frame['helping_effort'] = np.where(frame.helping_binary == 1, 0., np.nan)
    frame.loc[frame.id == 0, 'helping_binary'] = np.nan
    frame.loc[frame.id == 2, 'helping_effort'] = np.nan
    frame.loc[(frame.id == 3) & (frame.day <= 3), 'helping_binary'] = 0
    original, replay = occurrence(frame, False), occurrence(frame, True)
    for form, values in original.items():
        for name, parts in values.items():
            for a,b in zip(parts,replay[form][name]):
                np.testing.assert_allclose(a['b'],b['b'],atol=1e-10)
                assert np.isnan(a['b'][0]) and a['b'][2]>0
            if form == 'PST5':
                assert np.isnan(parts[0]['b'][3])

def run(replay):
    dest = Path(os.environ['PST8_RESULT']).parent
    cfg = read(Path('.agent-state/data_collection_root.json'))
    root = Path(cfg['root'])
    if not cfg['repair_hold'] or root.drive.lower() != 'c:' or root.name != br.ROOT_NAME or filehash(root/'DRT1_MANIFEST.json') != br.MANIFEST:
        raise ValueError('Temporary root identity changed')
    member = root/'incoming/openesm-0049'
    manifest = member/'MANIFEST.json'
    assert filehash(manifest) == PIN
    tsv = member/'0049_pronizius_ts.tsv'
    entry, = [entry for entry in read(manifest)['files'] if entry['file']==tsv.name]
    assert filehash(tsv)==entry['sha256']
    frame = pd.read_csv(tsv, sep='\t', usecols=['id','day','helping_binary',*FEELINGS], dtype={'id':str})
    panels = occurrence(frame.dropna(subset=['day']).copy(),replay)
    rows, support = {}, {}
    for form, bank in panels.items():
        for name, (a,b) in bank.items():
            valid=np.isfinite(a['b']) & np.isfinite(b['b'])
            support.setdefault(name,{})[form] = dict(people=int(valid.sum()),
                paired_prompts=int(sum(np.sum(s['n0'][valid]+s['n1'][valid]) for s in (a,b))))
    if replay:
        assert read(dest/'SUPPORT.json')==support
    else:
        freeze(dest/'SUPPORT.json',support)
    def guard():
        if (dest/'STOP_REQUEST.json').exists():
            raise RuntimeError('Stop requested')
    for form,index in [('PST1',0),('PST5',2)]:
        for j,feeling in enumerate(FEELINGS):
            name='helping/'+feeling
            rows.setdefault(name,{})[form]=forms.fit(panels[form][name],'n1',[20261121,49,index,j],guard)
    result=dict(member='0049',people=frame.id.nunique(),reports=len(frame),rows=rows,support=support)
    if replay:
        br.verify_metric_tree(read(dest/'ORIGINAL.json'),result)
    freeze(dest/('AUDIT.json' if replay else 'ORIGINAL.json'),result)

if __name__=='__main__':
    if not sys.argv[1:]:
        for phase in ('fixture','execute','verify'):
            subprocess.run([sys.executable,'-B','-m',__spec__.name,phase],check=True)
    elif sys.argv[1:]==['fixture']:
        fixture()
    elif sys.argv[1:] in (['execute'],['verify']):
        run(sys.argv[1]=='verify')
    else:
        raise SystemExit('Unknown operation')
