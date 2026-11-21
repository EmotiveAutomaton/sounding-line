"""BR qualification against the curator's deposited, hash-pinned synthetic worlds."""
import csv
import io
import json
import os
from pathlib import Path
import sys

import numpy as np
from runners.drive.cards import week6_br_forms_v1 as forms
from runners.drive.cards import week6_person_slopes_v1 as op

DIRECTORY = (Path(__file__).resolve().parents[1] /
             '.agent-state/drive-20261115/person-rows-20261121/intake/afternoon')


def test_missing_grades_and_support():
    r = np.array([[0,0,1,3,np.nan],[0,0,2,2,3],[0,0,1,2,3]],float)
    y = 2 + 3*r
    y[1,-1] = np.nan
    actual = forms.graded_stats(r,y)
    np.testing.assert_allclose(actual['b'], [3,np.nan,3], equal_nan=True)
    np.testing.assert_allclose(actual['sxx'][0], np.sum((r[0,:4]-1)**2))


def test_gap_uses_elapsed_days():
    early,late=forms.gap_masks(np.array([2,3,6,8,9,11]),2,11)
    assert early.tolist()==[True,True,False,False,False,False]
    assert late.tolist()==[False,False,False,False,True,True]


def test_all_registered_worlds(tmp_path):
    sys.path.insert(0,str(DIRECTORY))
    try:
        import pf_addendum as pf
    finally:
        sys.path.pop(0)
    specs=(('graded',pf.G_WORLDS),('gap',pf.GAP_WORLDS))
    tables=(DIRECTORY/'pf_addendum.txt').read_text().split('\n\n')[:2]
    results=[]
    for section,(form,worlds) in enumerate(specs):
        expected={(r['size'],r['world']):r for r in csv.DictReader(
            io.StringIO('\n'.join(line for line in tables[section].splitlines() if not line.startswith('#'))),delimiter='\t')}
        for si,(size,n,h) in enumerate(pf.SIZES):
            dates=np.arange(2*h)
            halves=(dates<h,dates>=h)
            for wi,world in enumerate(worlds):
                totals=np.zeros(2)
                name=world if section==0 else world[0]
                for rep in range(100):
                    rng=np.random.default_rng([pf.SEED,101+section,si,wi,rep])
                    if section==0:
                        r,y,_=pf.graded_world(rng,n,h,world)
                        x=(r>0).astype(float)
                    elif len(world)==1:
                        x,y,_=pf.chk_make(rng,n,2*h,name,pf.PPD[size])
                    else:
                        x,y,_=pf.simulate(rng,n,h,*world[1:])
                    for j in range(2):
                        graded=section==0 and j==1
                        masks=forms.gap_masks(dates,0,2*h-1) if section==1 and j else halves
                        stats=[forms.graded_stats(r[:,m],y[:,m]) if graded else op.half_stats(x[:,m],y[:,m]) for m in masks]
                        good=np.logical_and.reduce([(s['n1']>=2)&(s['n0']>=2)&np.isfinite(s['b']) for s in stats])
                        a,b=[{k:v[good] for k,v in s.items()} for s in stats]
                        key='sxx' if graded else 'n1'
                        w=np.minimum(a[key],b[key])
                        W=op.boot_counts(rng,len(w),300)*w
                        cov=[(a['L'],b['L'])]
                        if op.wpearson(w,a['S'],b['S'])>=.3: cov.append((a['S'],b['S']))
                        adj=op.adjust(W,(a['b'],b['b']),cov)[1]
                        totals[j]+=np.percentile(adj,2.5)>0
                labels=('BIN_bar','GRD_bar') if section==0 else ('halves_bar','thirds_bar')
                reference=[float(expected[size,name][k]) for k in labels]
                observed=totals/100
                results.append(dict(size=size,world=name,form=form,actual=observed.tolist(),expected=reference))
                if 'LATTICE_THREAD_WITNESS' in os.environ:
                    (Path(os.environ['LATTICE_THREAD_WITNESS']).parent/'BR_FIXTURE_CELLS.json').write_text(json.dumps(results))
                assert np.max(np.abs(observed-reference)) <= .10000000001

