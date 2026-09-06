"""Run deterministic readout repair fixtures and independent precision probes.

DESIGN CHECK (2026-09-06)
lessons read: LESSONS sections 3,4,5; CONTROLS sections 5,6.
NULL: equal likelihoods stay uniform; ALTERNATIVE: known maxima survive all positions.
gates: exact fixture comparisons within 1e-12; any missing/invalid input must refuse.
bands: all assertions pass or exit nonzero. Precision probes are descriptive only;
they cannot validate historical GPU padding/batching behavior or amend X05's threshold.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[1];out=a.out.resolve()
    if any(out.is_relative_to(root/f'results/phase_2_4_stage_{s}') for s in (7,8)):raise ValueError('closed output root')
    p=subprocess.run([sys.executable,'-B','-m','pytest','-q','tests/test_readout_repair.py'],cwd=root,text=True,capture_output=True)
    print(p.stdout);print(p.stderr,file=sys.stderr)
    if p.returncode:return p.returncode
    import numpy as np
    precision=[]
    # Frozen analytic score vectors; no historical outcome or threshold sets these inputs.
    for n in (6,21,65):
        x=-np.arange(n,dtype=np.float64)/7-20
        def normalized(y):
            z=np.exp(y-y.max());return z/z.sum()
        exact=normalized(x)
        for dtype in (np.float16,np.float32,np.float64):
            v=normalized(x.astype(dtype));tv=float(np.abs(v.astype(np.float64)-exact).sum()/2)
            precision.append({'n':n,'dtype':np.dtype(dtype).name,'tv_from_float64':tv,'sum_residual':float(abs(v.astype(np.float64).sum()-1))})
    result={'version':'readout-repair-fixtures-20260906.1','valid':True,'pytest_returncode':p.returncode,'fixtures':'all-position maxima, permutations, >24 candidates, ties, normalization, missing and invalid components, identity and semantics mismatches','precision':precision,'scope':'deterministic apparatus only; no scientific rescore, model calls or spend','x05_limit':'independent arithmetic precision only, not empirical calibration of the historical GPU batching tolerance; original and amended judgments stay separate','sources':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('runners/readout_repair.py','tests/test_readout_repair.py','tools/check_readout_repair.py')}}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
