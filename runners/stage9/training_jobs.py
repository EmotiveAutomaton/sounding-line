"""Scientific factorial dispatch, callable only through an identified queue cell.

DESIGN CHECK: C05/C07/X01; LESSONS sections 3--5. NULL: incomplete or changed fitting inputs refuse. ALTERNATIVE: the full declared optimizer and validation reconcile. A fit is not admission. All 24 declared fits retain
their three full epochs and validation, including failed seeds. Training inputs
must match the fixed source pool, target budget and common development targets.
Collection uses only the actual seed-9001 scientific original-expert checkpoint.
The explicit discarded rehearsal executes this same fitting path with a complete
64-example epoch and validation. Its fixed source, seed and output namespace cannot
become a scientific factorial fit.
"""
import argparse
import os
from pathlib import Path

from runners.stage9.common import REPO, ROOT, closure, digest, file_hash, freeze, read
from runners.stage9.matching import audit, mixture_keys, target_positions
from runners.stage9.recipes import parameter_partition
from runners.stage9.train import BASES

# Manually enumerated factorial. The scheduler does not derive studies from prose.
FITS = (
    ('qwen','original_expert',9001), ('smollm','original_expert',9001),
    ('qwen','original_expert',9002), ('qwen','original_expert',9003),
    ('smollm','original_expert',9002), ('smollm','original_expert',9003),
    ('qwen','both_expert',9001), ('qwen','both_expert',9002), ('qwen','both_expert',9003),
    ('smollm','both_expert',9001), ('smollm','both_expert',9002), ('smollm','both_expert',9003),
    ('qwen','original_mixed',9001), ('qwen','original_mixed',9002), ('qwen','original_mixed',9003),
    ('smollm','original_mixed',9001), ('smollm','original_mixed',9002), ('smollm','original_mixed',9003),
    ('qwen','both_mixed',9001), ('qwen','both_mixed',9002), ('qwen','both_mixed',9003),
    ('smollm','both_mixed',9001), ('smollm','both_mixed',9002), ('smollm','both_mixed',9003),
)
RECIPES = {'original_expert','both_expert','original_mixed','both_mixed'}


def cell_identity():
    value = os.environ.get('S9_CELL_IDENTITY','')
    if len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('scientific dispatch requires the source-checked queue cell identity')
    return value


def training_root(family, recipe, seed):
    if (family,recipe,seed) not in FITS:
        raise ValueError('fit is not in the manually declared factorial')
    return ROOT/'private/scientific-training'/family/recipe/str(seed)


def validate_corpus(corpus, reference, pool, recipe):
    if recipe not in RECIPES or corpus['split']!='training' or reference['split']!='training':
        raise ValueError('only declared scientific training corpora may be fitted')
    rows=corpus['examples']; original=reference['examples']; sources=pool['candidate_examples']
    if len(rows)!=1600 or len(original)!=1600 or len(sources)!=1600:
        raise ValueError('factorial requires 1600 examples per cell')
    keys=[r['key'] for r in rows]
    if len(set(keys))!=1600 or keys!=[r['key'] for r in sources] or keys!=[r['key'] for r in original]:
        raise ValueError('example identities or order differ from the paired source pool')
    if any(parameter_partition(w)!='training' for w in pool['private_worlds'].values()):
        raise ValueError('held-out parameter combination entered training')
    for row,source in zip(rows,sources):
        if row['lineages']!=source['lineages']:
            raise ValueError('example has different earlier/current source exposure')
        if len(row['input_ids'])>2048 or len(row['input_ids'])!=len(row['labels']):
            raise ValueError('input exceeds the frozen matched-recipe envelope')
        if any(y!=-100 and y!=x for x,y in zip(row['input_ids'],row['labels'])) or not target_positions(row):
            raise ValueError('invalid causal target labels')
    comparison=audit({'original_expert':original,recipe:rows},pool['private_worlds'].keys())
    if corpus['validation']!=reference['validation'] or corpus['validation_choices']!=reference['validation_choices']:
        raise ValueError('factorial must share exact development examples and targets')
    choices=corpus['validation_choices']
    if len(choices)!=96 or len({c['key'] for c in choices})!=96:
        raise ValueError('complete 96-world validation is required for every fit')
    if any(c['key'] in pool['private_worlds'] or c['parameter_partition']!='development'
           or c['truth'] not in c['options'] or 'stop' not in c['options'] for c in choices):
        raise ValueError('validation split, target or STOP support is invalid')
    if recipe=='original_expert':
        if any(r['input_ids']!=s['input_ids'] or r['labels']!=s['input_ids'] for r,s in zip(rows,sources)):
            raise ValueError('original capped expert replay changed')
    if recipe.endswith('_mixed'):
        selected=mixture_keys(sources)
        if corpus['identity']['matching']['assigned_sources']!=800:
            raise ValueError('mixed assignment count differs')
        for row,source in zip(rows,sources):
            if row['key'] not in selected:
                # Broader expert rows can include disclosed correct supplements;
                # comparison to that paired expert cell is performed by run_fit.
                continue
            if row['kind']=='learner_visited':
                if row['actual_learner_states']<1 or not row['spans']:
                    raise ValueError('assigned learner row has no actual state')
                for span in row['spans']:
                    start,end=span['context']
                    if not 0<=start<end<=len(row['labels']) or any(y!=-100 for y in row['labels'][start:end]):
                        raise ValueError('learner context became a scientific target')
            elif row['kind']!='assigned_learner_unrealized':
                raise ValueError('missing disposition for assigned learner source')
    return comparison


def execute_fit(path,output,family,seed,*,epochs,expected_examples):
    """One fitting and completion-check path for the real and rehearsal sizes."""
    from runners.stage9.train import train
    corpus=read(path)
    if len(corpus['examples'])!=expected_examples:raise ValueError('declared fitting count differs')
    fit=train(path,output,family,seed=seed,epochs=epochs,batch_size=4,accumulation=2,
              lr=2e-4,max_length=2048,checkpoint_every=25,loss_mode='streamed')
    if fit.get('checkpointed'):
        raise RuntimeError('bounded checkpoint completed; fitting cell remains unfinished')
    fitted=read(output/'IDENTITY.json')
    updates=(expected_examples+7)//8
    if (fit['identity_sha256']!=digest(fitted) or fitted['corpus_sha256']!=file_hash(path)
        or fitted['epochs']!=epochs or fitted['batch']!=4 or fitted['accumulation']!=2
        or len(fit['curve'])!=epochs or [c['updates'] for c in fit['curve']]!=[updates*(i+1) for i in range(epochs)]
        or fit['exposure']['supervised_tokens']!=sum(len(target_positions(r)) for r in corpus['examples'])
        or closure([output/fit['selected_checkpoint']])['sha256']!=fit['selected_checkpoint_sha256']):
        raise ValueError('complete fitting execution did not reconcile')
    return fit


def rehearsal_input(family):
    """A previously audited discarded mixed corpus, with its exposure rechecked."""
    from runners.stage9.matching import replay_row
    base=ROOT/'private/pilot-dose-v3'/family
    path=base/'mixed.json';corpus=read(path)
    original=read(base/'training-v1/IDENTITY.json');complete=read(base/'training-v1/COMPLETE.json')
    pool=read((ROOT/'private/pilot-dose/qwen' if family=='qwen' else base)/'POOL.json')
    if (family not in BASES or corpus['split']!='pilot' or original['split']!='pilot' or original['family']!=family
        or original['base']!=BASES[family]
        or original['corpus_sha256']!=file_hash(path) or complete['identity_sha256']!=digest(original)
        or len(corpus['examples'])!=64 or len(pool['examples'])!=64):
        raise ValueError('discarded rehearsal input differs from its audited pilot')
    sources=pool['examples'];rows=corpus['examples']
    if [r['key'] for r in rows]!=[s['key'] for s in sources]:raise ValueError('pilot source allocation changed')
    for row,source in zip(rows,sources):
        if row['lineages']!=source['lineages'] or len(row['input_ids'])>2048 or len(row['input_ids'])!=len(row['labels']):
            raise ValueError('pilot input/source exposure changed')
        if any(y!=-100 and y!=x for x,y in zip(row['input_ids'],row['labels'])) or not target_positions(row):
            raise ValueError('pilot targets invalid')
        for span in row.get('spans',[]):
            start,end=span['context']
            if not 0<=start<end<=len(row['labels']) or any(y!=-100 for y in row['labels'][start:end]):
                raise ValueError('pilot learner context became target or its span is invalid')
    comparison=audit({'expert':[replay_row(s) for s in sources],'mixed':rows},pool['worlds'].keys())
    if len(corpus['validation'])!=40 or len(corpus['validation_choices'])!=80:
        raise ValueError('bounded rehearsal must execute complete validation')
    return path,comparison


def run_fit(family,recipe,seed,produce,rehearsal_root=None):
    if rehearsal_root is not None:
        identity=cell_identity();root=Path(rehearsal_root).resolve()
        if (not root.is_relative_to(ROOT/'private/training-handler-pilots') or
            root==ROOT/'private/training-handler-pilots' or recipe!='both_mixed' or seed!=997901):
            raise ValueError('explicit fixed discarded training rehearsal namespace, recipe and seed required')
        path,comparison=rehearsal_input(family);output=root/'fit'
        freeze(root/'PILOT_INPUT.json',{'cell_identity':identity,'family':family,'recipe':recipe,'seed':seed,
            'corpus_sha256':file_hash(path),'comparison':comparison,'epochs':1,'examples':64,
            'scope':'discarded actual fitting-handler execution; cannot enter scientific fitting or admission'})
        fit=execute_fit(path,output,family,seed,epochs=1,expected_examples=64)
        freeze(produce,{'cell_identity':identity,'family':family,'recipe':recipe,'seed':seed,'operation':'fit',
            'scope':'discarded-rehearsal','examples':64,'epochs':1,'updates':8,'complete_validation':True,
            'training_complete_sha256':file_hash(output/'COMPLETE.json'),
            'selected_checkpoint_sha256':fit['selected_checkpoint_sha256'],'training_root':str(output.relative_to(REPO)),
            'active_seconds':fit['active_seconds'],'admission':'ineligible discarded pilot'})
        return
    identity=cell_identity();output=training_root(family,recipe,seed)
    base=ROOT/'private/scientific-recipes'/family
    path=base/(recipe+'.json');corpus=read(path);reference=read(base/'original_expert.json')
    coverage=recipe.split('_')[0]
    pool_path=ROOT/'private/training-pools'/family/(coverage+'.json');pool=read(pool_path)
    comparison=validate_corpus(corpus,reference,pool,recipe)
    if recipe.endswith('_mixed'):
        paired=read(base/(coverage+'_expert.json'))
        selected=mixture_keys(pool['candidate_examples'])
        if any(r!=e for r,e in zip(corpus['examples'],paired['examples']) if r['key'] not in selected):
            raise ValueError('fixed expert half changed during learner packing')
        collection=ROOT/'private/scientific-collection'/family/coverage
        if corpus['identity']['collection_complete_sha256']!=file_hash(collection/'COMPLETE.json'):
            raise ValueError('mixed corpus collection completion changed')
    input_receipt={'cell_identity':identity,'family':family,'recipe':recipe,'seed':seed,
        'corpus_sha256':file_hash(path),'pool_sha256':file_hash(pool_path),'comparison':comparison,
        'optimizer_contract':{'epochs':3,'batch':4,'accumulation':2,'lr':.0002,'maximum_tokens':2048,
                              'loss_computation':'streamed','projection_chunk_tokens':64}}
    freeze(output/'SCIENTIFIC_INPUT.json',input_receipt)
    # The same maximum is allowed in every cell. Prepared original replay arrays
    # retain their exact historical 1024-token cap; no extra original tokens enter.
    fit=execute_fit(path,output,family,seed,epochs=3,expected_examples=1600)
    freeze(produce,{'cell_identity':identity,'family':family,'recipe':recipe,'seed':seed,
        'training_complete_sha256':file_hash(output/'COMPLETE.json'),'training_root':str(output.relative_to(REPO)),
        'input_sha256':digest(input_receipt),'selected_checkpoint_sha256':fit['selected_checkpoint_sha256'],
        'active_seconds':fit['active_seconds'],'full_validation_retained':True,'admission':'not evaluated'})


def run_collection(family,coverage,produce,rehearsal_root=None,pilot_training=None):
    from runners.stage9.scientific_collector import run
    identity=cell_identity()
    if rehearsal_root is not None:
        output=Path(rehearsal_root).resolve();training=Path(pilot_training).resolve()
    else:
        output=ROOT/'private/scientific-collection'/family/coverage;training=training_root(family,'original_expert',9001)
        if pilot_training is not None:raise ValueError('pilot training cannot enter scientific collection')
    result=run(family,coverage,training,output,rehearsal=rehearsal_root is not None)
    freeze(produce,{'cell_identity':identity,'family':family,'coverage':coverage,
        'operation':'collect','collection_complete_sha256':file_hash(output/'COMPLETE.json'),**result})


def run_packing(family,coverage,produce,rehearsal_root=None,pilot_training=None,pilot_collection=None):
    from runners.stage9.mixed_recipes import prepare
    identity=cell_identity()
    if rehearsal_root is not None:
        from runners.stage9.scientific_collector import collection_inputs
        from runners.stage9.matching import replay_row
        output=Path(rehearsal_root).resolve();collection=Path(pilot_collection).resolve()
        if not collection.is_relative_to(ROOT/'private/collection-handler-pilots'):
            raise ValueError('discarded packing requires its actual isolated collection')
        prepare(family,coverage,collection,rehearsal_root=output,training=pilot_training)
        corpus=read(output/(coverage+'_mixed.json'))
        _,_,pool,_=collection_inputs(family,coverage,pilot_training,rehearsal=True)
        comparison=audit({'expert':[replay_row(s) for s in pool['candidate_examples']],
                          'mixed':corpus['examples']},pool['private_worlds'].keys())
        if corpus['split']!='pilot':raise ValueError('discarded packing changed split')
        freeze(produce,{'cell_identity':identity,'family':family,'coverage':coverage,'operation':'pack',
            'scope':'discarded-rehearsal','corpus_sha256':file_hash(output/(coverage+'_mixed.json')),
            'comparison':comparison,'corpus_identity':corpus['identity'],'admission':'ineligible discarded pilot'})
        return
    if pilot_training is not None or pilot_collection is not None:
        raise ValueError('pilot paths cannot enter scientific packing')
    output=ROOT/'private/scientific-recipes'/family
    path=output/(coverage+'_mixed.json')
    # An existing corpus is still checked below; expensive preparation is not rerun.
    if not path.exists():
        prepare(family,coverage,ROOT/'private/scientific-collection'/family/coverage)
    corpus=read(path);reference=read(output/'original_expert.json')
    pool=read(ROOT/'private/training-pools'/family/(coverage+'.json'))
    comparison=validate_corpus(corpus,reference,pool,coverage+'_mixed')
    freeze(produce,{'cell_identity':identity,'family':family,'coverage':coverage,
        'corpus_sha256':file_hash(path),'comparison':comparison,'corpus_identity':corpus['identity']})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('operation',choices=['fit','collect','pack'])
    parser.add_argument('--family',required=True,choices=BASES)
    parser.add_argument('--recipe',choices=sorted(RECIPES))
    parser.add_argument('--coverage',choices=['original','both'])
    parser.add_argument('--seed',type=int)
    parser.add_argument('--rehearsal-root',type=Path)
    parser.add_argument('--pilot-training',type=Path)
    parser.add_argument('--pilot-collection',type=Path)
    parser.add_argument('--produces',type=Path,required=True)
    args=parser.parse_args();produce=args.produces.resolve()
    if not produce.is_relative_to(ROOT) or produce==ROOT:
        raise ValueError('scientific produce must remain inside the Stage 9 root')
    if args.operation=='fit':
        if args.pilot_training is not None or args.pilot_collection is not None:
            raise ValueError('fitting cannot consume collection pilot paths')
        run_fit(args.family,args.recipe,args.seed,produce,rehearsal_root=args.rehearsal_root)
    else:
        if args.coverage is None:raise ValueError('collection/packing requires explicit coverage')
        if args.rehearsal_root is not None and args.pilot_training is None:
            raise ValueError('discarded collection/packing requires its actual fitting path')
        if args.operation=='collect':
            if args.pilot_collection is not None:raise ValueError('collection cannot consume another collection')
            run_collection(args.family,args.coverage,produce,args.rehearsal_root,args.pilot_training)
        else:
            if args.rehearsal_root is not None and args.pilot_collection is None:
                raise ValueError('discarded packing requires its actual collection path')
            run_packing(args.family,args.coverage,produce,args.rehearsal_root,args.pilot_training,args.pilot_collection)


if __name__=='__main__':
    main()
