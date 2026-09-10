"""Evaluate the full frozen generation cohort, retaining all attempted calls.

DESIGN CHECK: C02/C05/C07/X06/X11; LESSONS 3--5. NULL: an invalid call,
illegal action, incomplete cohort or below-reference score prevents broad passage.
ALTERNATIVE: executable full logs at or above the frozen reference meet the same
finite-battery criterion. Strict syntax and stopping remain separate measurements.
No original Stage 8 result is changed, and package admission additionally needs
the actual source, apparatus and operation-specific scientific gate evidence.
"""
from collections import Counter
from runners.stage9.common import digest
from runners.stage9.competence import rate
from runners.stage9.generation_evaluator import original_broad_comparator,score_attempt


def summarize(worlds,predictions,reference_scores,*,population,scope):
    if population not in ('original','expanded','historical_replay') or scope not in ('pilot','scientific'):
        raise ValueError('undeclared full-generation analysis')
    count=2 if scope=='pilot' else (40 if population=='historical_replay' else 96)
    if len(worlds)!=count or len(predictions)!=count or len(reference_scores)!=count:
        raise ValueError('full assigned generation and separate reference cohorts required')
    if len({w['lid'] for w in worlds})!=count:
        raise ValueError('duplicate generation source units')
    attempts=[score_attempt(w,p,max_lines=28) for w,p in zip(worlds,predictions)]
    comparison=original_broad_comparator(attempts,reference_scores,count)
    comparison['criterion_pass']=comparison.pop('historical_broad_pass')
    comparison['scope']=('historical no-change constructor under the Stage 9 parameter split; original criterion retained, '
        'not retrospective Stage 8 admission' if population=='original' else
        'expanded two-law-family population; own independent frozen reference, not the original-distribution gate')
    if population=='historical_replay':
        comparison['scope']='exposed original forty-world Stage 8 battery and its same-world reference; new package replay, no retrospective Stage 8 admission'
    rates={key:rate(sum(bool(a[key]) for a in attempts),count)
        for key in ('valid_execution','legacy_feasible','strict_feasible','stopped')}
    domains={}
    for domain in sorted({w['domain'] for w in worlds}):
        rows=[a for w,a in zip(worlds,attempts) if w['domain']==domain]
        domains[domain]={key:rate(sum(bool(a[key]) for a in rows),len(rows)) for key in rates}
    return {'population':population,'scope':scope,'expected_attempts':count,'attempts':attempts,
        'prediction_sha256':digest(predictions),'source_lineages':[w['lid'] for w in worlds],
        'domains':domains,'rates':rates,'comparison':comparison,'reference_scores':reference_scores,
        'all_predictions_frozen_before_scoring':True,'scientific_admission':False,
        'admission_limit':'operation criterion alone cannot supply missing apparatus, package, selection or source checks'}
