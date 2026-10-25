"""CA3 independent choice-fit/statement-target census, before value outcomes.

DESIGN CHECK: LESSONS 3-5. The person's choice direction uses only comparisons
without explanations, not all comparisons with the explanation text removed.
Every fixed CA1 person remains in the support census. Missing fit/target support
is unresolved, never silently excluded or assigned a population substitute.
No model labels, reader fit, value prototype, AUC or permutation is computed.
"""
from collections import Counter, defaultdict
from pathlib import Path

from runners.stage14.common import digest, filehash, freeze, read
from .week3_alignment_features import source as alignment_source
from .timing_pmap_source import completed

INPUTS = {'prepared_summary','prepared_complete','values_input_summary','values_input_complete'}


def partition(rows, people, items, joins):
    identities = {}; grouped = defaultdict(list)
    for index,row in enumerate(rows):
        ident = (row['writer'], row['conversation'], row['turn'])
        if ident in identities: raise ValueError('duplicate comparison identity')
        identities[ident] = index; grouped[row['writer']].append(index)
    if set(grouped) != set(people): raise ValueError('fixed CA1 population differs')
    by = {r['item_id']:r['text'] for r in items}
    if len(by) != len(items) or set(by) != set(joins): raise ValueError('complete unique VAL input/join required')
    targets = {}; people_targets = defaultdict(list)
    for item_id,links in joins.items():
        if digest({'VAL-text':by[item_id]}) != item_id: raise ValueError('VAL semantic input changed')
        for link in links:
            if link['kind'] != 'choice-explanation': continue
            ident = (link['writer'], link['conversation'], link['turn'])
            if ident not in identities: raise ValueError('VAL target outside fixed CA1 comparisons')
            index = identities[ident]; row = rows[index]
            if row['explanation'] != by[item_id] or not row['explanation'].strip(): raise ValueError('statement target text differs')
            if link['prompt'] != row['prompt'] or link['half'] != row['half']: raise ValueError('statement target context differs')
            if index in targets: raise ValueError('duplicate comparison target')
            targets[index] = item_id; people_targets[row['writer']].append(index)
    result = []
    for writer in sorted(people):
        original = grouped[writer]
        countries = {rows[i]['country'] for i in original}
        if len(countries) != 1: raise ValueError('writer country changed')
        train = [i for i in original if not rows[i]['explanation'].strip()]
        target = sorted(people_targets[writer])
        if set(train) & set(target): raise ValueError('explained comparison leaked into reader fit')
        reasons = []
        if not train: reasons.append('no-comparisons-without-explanations')
        if not target: reasons.append('no-sampled-explanation-targets')
        result.append(dict(writer=writer,country=next(iter(countries)),fit_indices=train,
            targets=[dict(comparison_index=i,item_id=targets[i]) for i in target],
            original_comparisons=len(original), excluded_explained_comparisons=len(original)-len(train),
            support='pending-value-labels-and-model-fit' if not reasons else 'unsupported-inputs',
            unsupported_reasons=reasons))
    return result


def calculate(inputs, config):
    if set(inputs) != INPUTS or config != {}: raise ValueError('exact CA3 source inputs required')
    _,_,rows,splits = alignment_source(inputs)
    summary_path = Path(inputs['values_input_summary']).resolve()
    completed(inputs['values_input_complete'],summary_path)
    summary = read(summary_path); base = summary_path.parent
    if summary.get('card') != 'VAL-inputs' or summary.get('state') != 'private_inputs_ready': raise ValueError('completed VAL source preparation required')
    for name,h in summary['output_hashes'].items():
        if filehash(base/name) != h: raise ValueError('VAL prepared payload changed')
    population = read(base/'PRIVATE_POPULATION.json')
    if {r['writer'] for r in population['choice']} != set(splits['writer_splits']): raise ValueError('VAL/CA1 population changed')
    result = partition(rows, splits['writer_splits'],read(base/'ITEMS.json'),read(base/'PRIVATE_JOIN.json'))
    if sum(len(r['targets']) for r in result) != summary['sampled_explanations']: raise ValueError('full sampled target coverage differs')
    summary = dict(card='CA3-inputs',state='source_support_census',input_hashes={k:filehash(v) for k,v in inputs.items()},
        fixed_annotators=len(result), original_comparisons=len(rows),
        fit_comparisons_without_explanations=sum(len(r['fit_indices']) for r in result),
        heldout_explanation_targets=sum(len(r['targets']) for r in result),
        people_with_input_support=sum(not r['unsupported_reasons'] for r in result),
        unsupported_reason_counts=dict(sorted(Counter(reason for r in result for reason in r['unsupported_reasons']).items())),
        full_population_input_supported=all(not r['unsupported_reasons'] for r in result),
        definition='All unexplained comparisons fit directions; all explained comparisons excluded from those fits; sampled explanations are targets',
        remaining=['complete calibrated VAL labels','complete candidate features','known-answer and empirical controls','reader refits, leave-person-out prototypes and AUC'],
        scientific_admission=False)
    return result,summary


def execute(output,inputs,config):
    output=Path(output);rows,summary=calculate(inputs,config)
    freeze(output/'PRIVATE_REFIT_TARGETS.json',rows)
    summary['output_hashes']={'PRIVATE_REFIT_TARGETS.json':filehash(output/'PRIVATE_REFIT_TARGETS.json')}
    freeze(output/'SUMMARY.json',summary);return summary


def verify(output,inputs,config):
    output=Path(output);rows,summary=calculate(inputs,config)
    if read(output/'PRIVATE_REFIT_TARGETS.json') != rows: raise ValueError('fresh CA3 partition differs')
    summary['output_hashes']={'PRIVATE_REFIT_TARGETS.json':filehash(output/'PRIVATE_REFIT_TARGETS.json')}
    if read(output/'SUMMARY.json') != summary: raise ValueError('fresh CA3 summary differs')
    return dict(verified=True,full_fit_target_separation_replayed=True)
