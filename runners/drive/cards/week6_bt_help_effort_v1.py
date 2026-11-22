"""Conditional effort binding for the 0049 graded form."""
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

from . import week6_br_v1 as br
from . import week6_bt_forms_v1 as forms
from .week6_bt_help_job import FEELINGS, PIN
from .batch_runtime import read, freeze, filehash

def effort_grade(frame, include_nonhelp):
    occurrence = frame['helping_binary']
    effort = frame['helping_effort']
    if (occurrence.notna() & ~occurrence.isin([0,1])).any():
        raise ValueError('Unknown helping response')
    if ((effort < 0) | (effort > 100)).any():
        raise ValueError('Effort outside the item limits')
    values = effort.where(occurrence.eq(1))
    if include_nonhelp:
        values = values.mask(occurrence.eq(0), 0)
    return values.to_numpy(float)

def panels(frame, *, include_nonhelp, replay):
    grade = effort_grade(frame, include_nonhelp)
    data, _, half, _ = forms.project(frame, {'helping':grade}, FEELINGS)
    return {name:br.graded_halves(data,grade,outcome,half,replay)
            for name,(_,outcome) in data['slopes'].items()}

def fixture():
    frame=pd.DataFrame({'helping_binary':[0,1,1,1,np.nan],
                        'helping_effort':[np.nan,0,43,np.nan,np.nan]})
    np.testing.assert_allclose(effort_grade(frame,False),[np.nan,0,43,np.nan,np.nan],equal_nan=True)
    np.testing.assert_allclose(effort_grade(frame,True),[0,0,43,np.nan,np.nan],equal_nan=True)
    frame=pd.DataFrame({'id':np.repeat(np.arange(8),60),
                        'day':np.tile(np.repeat(np.arange(10),6),8),
                        'helping_binary':np.tile([0,1,1,1,1,1],80),
                        'helping_effort':np.tile([np.nan,0,0,10,20,30],80)})
    for key in FEELINGS:
        frame[key]=25+frame.helping_effort.fillna(0)*(frame.id%3+1)/3
    for mode in (False,True):
        first=panels(frame,include_nonhelp=mode,replay=False)
        second=panels(frame,include_nonhelp=mode,replay=True)
        for key,sides in first.items():
            for side,check in zip(sides,second[key]):
                np.testing.assert_allclose(side['b'],check['b'],atol=1e-10)
                np.testing.assert_allclose(side['b'][2]/side['b'][1],1.5)
                assert side['n0'][0]==(15 if mode else 10)

def run(replay):
    dest = Path(os.environ['PST8_RESULT']).parent
    plan = read(dest/'PLAN.json')
    mode = plan['effort_population']
    if mode not in ('helping episodes only','confirmed non-help counts as zero'):
        raise ValueError('Missing or unknown approved effort population')
    pointer = read(Path('.agent-state/data_collection_root.json'))
    root = Path(pointer['root'])
    if not pointer['repair_hold'] or root.drive.lower()!='c:' or root.name!=br.ROOT_NAME or filehash(root/'DRT1_MANIFEST.json')!=br.MANIFEST:
        raise ValueError('Temporary root changed')
    directory = root/'incoming/openesm-0049'
    manifest = directory/'MANIFEST.json'
    assert filehash(manifest)==PIN
    source = directory/'0049_pronizius_ts.tsv'
    entry, = [v for v in read(manifest)['files'] if v['file']==source.name]
    assert filehash(source)==entry['sha256']
    frame = pd.read_csv(source,sep='\t',usecols=['id','day','helping_binary','helping_effort',*FEELINGS],dtype={'id':str})
    dated = frame.dropna(subset=['day']).copy()
    if dated.id.isna().any() or (dated.day%1!=0).any() or ((dated[list(FEELINGS)]<0)|(dated[list(FEELINGS)]>100)).any().any():
        raise ValueError('Invalid identity, day or mood rating')
    bank = panels(dated,include_nonhelp=mode=='confirmed non-help counts as zero',replay=replay)
    support = {}
    for key,(a,b) in bank.items():
        ok = np.isfinite(a['b']) & np.isfinite(b['b'])
        support[key] = dict(people=int(ok.sum()),paired_prompts=int(sum(np.sum(side['n0'][ok]+side['n1'][ok]) for side in (a,b))))
    if replay:
        assert support==read(dest/'SUPPORT.json')
    else:
        freeze(dest/'SUPPORT.json',support)
    def guard():
        if (dest/'STOP_REQUEST.json').exists():
            raise RuntimeError('Stop requested')
    rows = {('helping/'+k):forms.fit(bank['helping/'+k],'sxx',[20261121,49,1,j],guard) for j,k in enumerate(FEELINGS)}
    result = dict(rows=rows,support=support,effort_population=mode,people=frame.id.nunique(),reports=len(frame))
    if replay:
        br.verify_metric_tree(read(dest/'ORIGINAL.json'),result)
    freeze(dest/('AUDIT.json' if replay else 'ORIGINAL.json'),result)

if __name__=='__main__':
    if sys.argv[1:]==['native']:
        for phase in ('fixture','execute','verify'):
            subprocess.run([sys.executable,'-B','-m',__spec__.name,phase],check=True)
    elif sys.argv[1:] in ([],['fixture']):
        fixture()
    elif sys.argv[1:] in (['execute'],['verify']):
        run(sys.argv[1]=='verify')
    else:
        raise SystemExit('Unknown operation')
