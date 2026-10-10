"""H04/C01 exact source/missingness ruler with indistinguishable endpoints.

DESIGN CHECK: LESSONS 2-5; CONTROLS 1,6. NULL: absent observations falsely
exclude viable histories; equal endpoints license no unique provenance. ALTERNATIVE:
explicit witnessed facts select compatible histories, with rejected and ignored
opportunities distinguishable only when observed. No learned human-goal result.
"""
from collections import Counter
from .common import freeze,digest
from .factorized import controls

def compatible(target,observed):return all(target[k]==v for k,v in observed.items())

def run(card,out,raw,tick):
    cases=controls();results=[]
    # Counterfactual history bank varies witnessed handling and exposes which
    # record fields, rather than text volume, resolve those alternatives.
    for i,c in enumerate(cases):
        true=dict(handling=c['target']['handling'],facts=c['target']['facts'])
        bank=[true,dict(handling='ignore' if true['handling']!='ignore' else 'dismiss',facts=true['facts'])]
        views=dict(full=true,handling_hidden={'facts':true['facts']},all_hidden={})
        for view,obs in views.items():
            ids=[j for j,h in enumerate(bank) if compatible(h,obs)]
            if 0 not in ids:raise ValueError('withholding removed true account')
            results.append(dict(key=c['key'],view=view,compatible=ids,truth=0,unrepresented_mass='unknown outside this supplied bank',entropy_bits=0 if len(ids)==1 else 1,
                scope='constructed supplied histories; source omission is not evidence of absence'))
        tick(dict(cases=i+1,total=len(cases)))
    if any(len(r['compatible'])!=2 for r in results if r['view']=='all_hidden'):raise ValueError('missingness collapsed to absence')
    freeze(out/'CONTROLS.json',cases);freeze(out/'PREDICTIONS.json',results)
    freeze(out/'SUMMARY.json',dict(cases=len(cases),views=3,checks_passed=True,scope='exact bank compatibility and missingness instrument; not a human reconstruction performance estimate'))
    freeze(out/'ADMISSION.json',dict(admitted=True,exact_compatibility=True,unknown_is_not_absent=True,human_inference=False))
