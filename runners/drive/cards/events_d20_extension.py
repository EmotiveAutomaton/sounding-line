"""D20 registered uptake reliability and October18 repeated/paired controls.

This is a new descriptive extension of the completed raw dismissed/produced-word
comparison. It changes neither the original/recovery code nor their outcomes.
The lexical Pearson odd/even-session reliability is the fixed primary;
embedding reliability is secondary. No causal exposure inference is licensed.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import time
import numpy as np
from . import events_d20_sources as source
from . import events_d20_stats as stats
from . import menus_d20 as original
from . import menus_d20_recovery as storage
from .menus_io import read,write,sha256,input_hashes,assert_equal,canonical

CONFIG = original.CONFIG | dict(threads=1,permutations=200,identity_permutations=200,checkpoint_draws=25)


class Yielded(Exception):
    pass


def config_check(config):
    if set(config)!=set(CONFIG) or config['seed']!=20261018 or config['threads']!=1:
        raise ValueError('D20 extension configuration/seed/threads differs')
    if config['permutations']<200 or config['identity_permutations']<200 or config['bootstrap']<2:
        raise ValueError('D20 requires at least200 repeated controls and bootstrap support')
    for key in ('minimum_writers','maximum_undefined_fraction','batch_size'):
        if config[key]!=CONFIG[key]:raise ValueError('D20 original scientific configuration changed')
    if config['checkpoint_draws']<1:raise ValueError('invalid checkpoint size')


def saved_json(path,value,checking):
    if path.exists():assert_equal(read(path),value)
    elif checking:raise ValueError('missing D20 extension output')
    else:write(path,value)


def boundary(output,checking):
    if not checking and (output/'YIELD_REQUEST.json').exists():raise Yielded()


def assert_comparisons(current,expected):
    assert_equal(current['writers'],expected['writers']); assert_equal(current['exclusions'],expected['exclusions'])
    if len(current['rows'])!=len(expected['rows']):raise ValueError('D20 primary support changed')
    for a,b in zip(current['rows'],expected['rows']):
        assert_equal({k:a[k] for k in ('key','writer','session','half')},{k:b[k] for k in ('key','writer','session','half')})
        if not np.allclose([a['observed']], [b['observed']],rtol=0,atol=1e-12):raise ValueError('D20 original overlap changed')
        if not np.allclose(a['donor_sum'],b['donor_sum'],rtol=0,atol=1e-11):raise ValueError('D20 original donor expectation changed')
        assert_equal(a['donor_sessions'],b['donor_sessions'])


def stored_kernel(output,name,value,binding,checking):
    meta,arrays=value; path=output/'kernels'/(name+'.npz'); mp=path.with_suffix('.json')
    if path.exists():
        receipt=read(mp)
        if sha256(path)!=receipt['sha256']:raise ValueError('changed D20 kernel checkpoint')
        assert_equal(receipt['binding'],binding);assert_equal(receipt['meta'],meta)
        with np.load(path,allow_pickle=False) as stored:
            if set(stored.files)!=set(arrays):raise ValueError('D20 kernel fields differ')
            for key,a in arrays.items():
                if not np.array_equal(stored[key],a):raise ValueError('D20 kernel fresh source replay differs')
    else:
        if checking:raise ValueError('missing D20 kernel checkpoint')
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:np.savez_compressed(stream,**arrays)
        write(mp,dict(binding=binding,meta=meta,sha256=sha256(path)))
    return value


def assemble(output,inputs,binding,checking,started):
    ctx=source.context(inputs); rows=[]; counts=Counter(); sessions=sorted(ctx['data']['sessions'])
    for i,sid in enumerate(sessions):
        lean,support=source.session(ctx,sid);value=dict(binding=binding,rows=lean,support=support)
        path=output/'sources'/(sid+'.json.gz')
        if path.exists():
            raw,_=storage.sealed_bytes(path);assert_equal(json.loads(raw),value)
        else:
            if checking:raise ValueError('missing D20 source checkpoint')
            receipt=storage.compressed(path,(canonical(value)+'\n').encode('utf8'));write(path.with_suffix('.seal.json'),receipt)
        rows.extend(lean);counts.update(support)
        if not checking and i+1>=math.ceil(.1*len(sessions)) and not (output/'FIRST_TENTH.json').exists():
            elapsed=time.perf_counter()-started
            write(output/'FIRST_TENTH.json',dict(phase='authenticated source extraction',completed_sessions=i+1,
                total_sessions=len(sessions),elapsed_seconds=elapsed,projected_extraction_seconds=elapsed*len(sessions)/(i+1),
                projected_cpu_seconds=2*elapsed*len(sessions)/(i+1)+600,
                forecast_basis='two full source passes plus600seconds statistics allowance; includes fresh verification'))
        boundary(output,checking)
    assert_equal(dict(counts),ctx['summary']['counts'])
    if len({r['key'] for r in rows})!=len(rows):raise ValueError('duplicate D20 menu keys')
    groups=defaultdict(list)
    for r in rows:groups[(r['prompt'],r['progress_decile'])].append(r)
    writers=sorted({r['writer'] for r in rows});kernels={c:[] for c in stats.CHANNELS}
    for i,(_,group) in enumerate(sorted(groups.items())):
        for channel in stats.CHANNELS:
            kernels[channel].append(stored_kernel(output,f'{i:05d}-{channel}',stats.kernel(group,writers,channel),binding,checking))
            boundary(output,checking)
    comparisons={};designs={};points={};maps={}
    for channel in stats.CHANNELS:
        comparison,excluded=stats.comparisons(kernels[channel],writers)
        current=dict(rows=comparison,writers=writers,exclusions=excluded)
        assert_comparisons(current,ctx['comparisons'][channel+'_observed'])
        saved_json(output/(channel+'-COMPARISONS.json'),current,checking)
        design=stats.Design(comparison,writers);point,means,halves=design.values(np.ones(len(writers)))
        oldpoint=ctx['summary']['arms'][channel+'_observed']['primary']['effect']
        if point is None or not np.isclose(point,oldpoint,rtol=0,atol=1e-12):raise ValueError('D20 original primary point changed')
        corr=design.correlation(halves,np.ones(len(writers)),minimum=binding['config']['minimum_writers'])
        identity=stats.identity_maps(len(design.eligible),binding['config']['seed'],binding['config']['identity_permutations'])
        paired=stats.identity_values(design,halves,np.ones(len(writers)),identity,binding['config']['minimum_writers'])
        saved_json(output/(channel+'-IDENTITY.json'),dict(eligible_writers=[writers[j] for j in design.eligible],maps=identity.tolist()),checking)
        points[channel]=dict(mean=point,reliability=corr,paired=paired,eligible_writers=len(design.eligible),
                             writers=len(writers),unsupported_half_writers=len(writers)-len(design.eligible),
                             menus=len(comparison),exclusions=excluded)
        comparisons[channel]=current;designs[channel]=design;maps[channel]=identity
    return ctx,kernels,designs,points,maps,counts


def checkpoint_draws(output,label,count,step,compute,binding,checking):
    values=[]
    for start in range(0,count,step):
        path=output/'draws'/f'{label}-{start:05d}.json'
        if path.exists() and not checking:
            receipt=read(path.with_suffix('.seal.json'))
            if sha256(path)!=receipt['sha256']:raise ValueError('changed D20 draw checkpoint')
            saved=read(path);assert_equal(saved['binding'],binding);assert_equal(saved['start'],start)
            if len(saved['values'])!=min(step,count-start):raise ValueError('incomplete D20 draw checkpoint')
            current=saved['values']
        else:
            current=[compute(i) for i in range(start,min(count,start+step))]
            saved_json(path,dict(binding=binding,start=start,values=current),checking)
            if path.with_suffix('.seal.json').exists():
                if read(path.with_suffix('.seal.json'))['sha256']!=sha256(path):raise ValueError('changed D20 draw checkpoint')
            elif checking:raise ValueError('missing D20 draw seal')
            else:write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))
        values.extend(current);boundary(output,checking)
    return values


def run(output,inputs,config,checking=False):
    output=Path(output);started=time.perf_counter();config_check(config)
    if not checking:output.mkdir(parents=True,exist_ok=True)
    binding=dict(inputs=input_hashes(inputs),config=config)
    if len(binding['inputs'])!=len(inputs):raise ValueError('all D20 extension inputs must be explicit files')
    saved_json(output/'BINDING.json',binding,checking)
    ctx,kernels,designs,points,maps,counts=assemble(output,inputs,binding,checking,started)
    groups=stats.outcome_groups(kernels['lexical'])
    assert_equal(groups,stats.outcome_groups(kernels['embedding']))
    shuffle_support=dict(groups=len(groups),singleton_groups=sum(len(g)==1 for g in groups),
        total_windows=sum(map(len,groups)),potentially_movable_windows=sum(len(g) for g in groups if len(g)>1))
    signatures={r['key']:r['outcome_signature'] for meta,_ in kernels['lexical'] for r in meta['targets']}
    shuffle_support.update(groups_with_distinct_outcomes=sum(len({signatures[k] for k in g})>1 for g in groups),
        windows_in_groups_with_distinct_outcomes=sum(len(g) for g in groups if len({signatures[k] for k in g})>1))
    def permute(i):
        mapping=stats.permutation(groups,config['seed'],i); result={}
        for channel in stats.CHANNELS:
            rows,excluded=stats.comparisons(kernels[channel],designs[channel].writers,mapping)
            assert_equal([r['key'] for r in rows],[r['key'] for r in designs[channel].rows])
            design=stats.Design(rows,designs[channel].writers);point,_,halves=design.values(np.ones(design.n))
            result[channel]=dict(mean=point,reliability=design.correlation(halves,np.ones(design.n),config['minimum_writers']))
        return dict(statistics=result,moved_windows=sum(k!=v for k,v in mapping.items()),
                    changed_outcome_windows=sum(signatures[k]!=signatures[v] for k,v in mapping.items()))
    permutations=checkpoint_draws(output,'outcome',config['permutations'],config['checkpoint_draws'],permute,binding,checking)
    rng=np.random.default_rng(config['seed']);n=len(next(iter(designs.values())).writers)
    indices=rng.integers(n,size=(config['bootstrap'],n))
    def boot(i):
        weights=np.bincount(indices[i],minlength=n);result={}
        for channel,design in designs.items():
            point,_,halves=design.values(weights)
            result[channel]=dict(mean=point,reliability=design.correlation(halves,weights),
                paired=stats.identity_values(design,halves,weights,maps[channel]))
        return result
    draws=checkpoint_draws(output,'bootstrap',config['bootstrap'],config['checkpoint_draws'],boot,binding,checking)
    arms={}
    for channel in stats.CHANNELS:
        point=points[channel]
        reliability=stats.intervals.interval(point['reliability'],[d[channel]['reliability'] for d in draws],config)
        paired=stats.intervals.interval(point['paired']['difference'],[d[channel]['paired']['difference'] for d in draws],config)
        controls={key:stats.null_report(point[key],[d['statistics'][channel][key] for d in permutations]) for key in ('mean','reliability')}
        arms[channel]=dict(primary=reliability,original_mean_unchanged=point['mean'],support=point,
            outcome_permutation=controls,identity=dict(own_minus_fake=paired,fake_mean=point['paired']['fake_mean'],
                undefined_point_permutations=point['paired']['undefined'],permutations=config['identity_permutations'],
                fixed_graph=True,bootstrap_undefined_permutation_counts=[d[channel]['paired']['undefined'] for d in draws]))
    files={p.relative_to(output).as_posix():sha256(p) for p in sorted(output.rglob('*')) if p.is_file()
           and p.name not in ('SUMMARY.json','YIELD_REQUEST.json','ELAPSED.json')}
    report=dict(card='D20-uptake-reliability',descriptive=True,scientific_admission=False,state=arms['lexical']['primary']['state'],
        primary=arms['lexical']['primary'],arms=arms,counts=dict(counts),shuffle_support=shuffle_support,
        config=config,input_hashes=binding['inputs'],artifact_hashes=files,
        estimand='Original Pearson correlation of odd/even chronological-session uptake means; lexical primary, embedding secondary. Original donor expectation and writer/session/menu weighting unchanged.',
        outcome_policy='200+ seeded within-writer, prompt and progress-decile permutations of complete next50-word windows. Same targets and donor graph, singleton groups fixed; no redraw. Controls report original mean uptake and reliability separately.',
        identity_policy='200+ fixed permutations of whole even-half identities among the original two-half-supported writers. Own-minus-mean-fake on exactly the same odd-half rows and even-half gallery. Bootstrap resamples real writer nodes taking both arms together and reweights donor roles; all counterparts must remain supported. Conditional on this fixed graph/support.',
        uncertainty='Original2000 writer-node bootstrap (target and donor roles), percentile95% intervals. Approximate two-sided normal p is descriptive; predicted-direction permutation p is separate. Unsupported draws retained; original5% bootstrap ceiling, no p from a reduced permutation set.',
        limitations='Association, not observed reading/exposure or causal influence. Saved MiniLM vectors authenticated, not neurally recomputed. Reliability and paired identity diagnostic do not establish latent goals, preferences or needs.')
    saved_json(output/'SUMMARY.json',report,checking)
    if not checking and not (output/'ELAPSED.json').exists():write(output/'ELAPSED.json',dict(execute_seconds=time.perf_counter()-started))
    return report


def execute(output,inputs,config):
    if (Path(output)/'SUMMARY.json').exists():
        verify(output,inputs,config);return read(Path(output)/'SUMMARY.json')
    try:return run(output,inputs,config)
    except Yielded:return dict(status='yielded',checkpoints_preserved=True)


def verify(output,inputs,config):
    report=run(output,inputs,config,checking=True)
    return dict(verified=True,primary_recomputed=report['primary'],state=report['state'],
                source_windows_replayed=True,original_comparisons_unchanged=True,all_draws_recomputed=True,
                neural_embeddings_recomputed=False)
