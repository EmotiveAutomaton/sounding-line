"""Actual pinned local POS model gate on constructed grammar only.

DESIGN CHECK: LESSONS4-5, 2026-10-25. Mock annotations cannot demonstrate an
installed tagger. Actual CPU inference, known simple counts, repeatability and
fresh-process reconstruction must all pass before corpus WC4 input preparation.
No observed-corpus claim, external transfer, training or GPU execution occurs.
"""
from pathlib import Path

from .week3_stability_inputs import LocalTagger
from .timing_census import read,filehash
from .timing_p6 import write_equal

CONFIG=dict(card='WC4-tagger-smoke',mode='constructed',seed=20261026)
CASES=[('Blue dogs run quickly.',dict(sentence_length=4.,lexical_density=1.,punctuation_rate=.2,artifact_words=4,artifact_sentences=1)),
       ('The cat is here.',dict(sentence_length=4.,lexical_density=.5,punctuation_rate=.2,artifact_words=4,artifact_sentences=1))]


def run(output,inputs,config,verification=False):
    if config!=CONFIG or set(inputs)!={'model_manifest'}:raise ValueError('frozen actual WC4 tagger smoke required')
    tagger=LocalTagger(inputs['model_manifest']);rows=[]
    for text,expected in CASES:
        first=tagger(text);second=tagger(text)
        if first!=expected or second!=expected:raise ValueError('WC4 actual tagger known-answer/repeat gate failed')
        rows.append(dict(text=text,expected=expected,observed=first))
    result=dict(card='WC4-tagger-smoke',constructed=True,scientific_admission=False,model_manifest_sha256=filehash(inputs['model_manifest']),rows=rows)
    path=Path(output)/'TAGGER_SMOKE.json'
    if verification:
        if read(path)!=result:raise ValueError('WC4 actual model fresh replay differs')
        return dict(verified=True,constructed=True,scientific_admission=False)
    write_equal(path,result);return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
