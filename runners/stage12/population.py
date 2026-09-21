"""Stage 12 descriptive population, independent of historical narrow allocation.

DESIGN CHECK: LESSONS 2-5; CONTROLS source separation. NULL: old exposure stays
exposed and unavailable histories stay unavailable. ALTERNATIVE: broader source
coverage may improve precision, without creating untouched confirmation. Writer
and prompt components are allocated from identity alone before labels are read;
all within-session earlier events are eligible history, never later events.
"""
from collections import Counter, defaultdict
from .common import REPO, SEED, read, freeze, digest, filehash


def allocation(keys, train, development, namespace):
    ordered=sorted(set(keys),key=lambda k:digest([SEED,namespace,k]))
    if len(ordered)<=train+development:
        raise ValueError('insufficient source components for declared partitions')
    return {k:'train' if i<train else 'development' if i<train+development else 'evaluation'
            for i,k in enumerate(ordered)}


def build(out,card,pulse,raw):
    from runners.stage9.coauthor_cases import components,session_rows
    from runners.stage9.coauthor import DECISIONS
    from runners.stage9.split_guard import Separation,disjoint_factors
    prepared=REPO/'results/phase_2_4_stage_9/private/prepared/coauthor-v2'
    cross=Separation.verified(REPO/'results/phase_2_4_stage_9/private/prepared/cross-source-v2')
    ledger=read(prepared/'LEDGER.json');people=components(cross,'coauthor');prompts=components(cross,'coauthor_prompts')
    usable=[r for r in ledger if r.get('usable')]
    wa=allocation([people['coauthor:'+r['writer']] for r in usable],8,8,'primary-writer')
    pa=allocation([prompts['coauthor_prompts:'+r['prompt']] for r in usable],4,4,'primary-prompt')
    freeze(out/'ALLOCATION.json',dict(writer=wa,prompt=pa,seed=SEED,
        scope='new descriptive split; every source has historical exposure; no untouched confirmation'))
    population={k:[] for k in ('train','development','evaluation')};excluded=[];sources={}
    for item in sorted(ledger,key=lambda r:r['key']):
        if not item.get('usable'):
            excluded.append(dict(session=item['key'],reason=item.get('reason','source unusable')));continue
        unit=people['coauthor:'+item['writer']];stimulus=prompts['coauthor_prompts:'+item['prompt']];lane=wa[unit]
        if pa[stimulus]!=lane:
            excluded.append(dict(session=item['key'],reason='crossed writer/prompt allocation mismatch'));continue
        path=prepared/'sessions'/(item['key']+'.json');session=read(path)
        if any(session[k]!=item[k] for k in ('key','writer','prompt','domain','split','usable','source_checks')):
            raise ValueError('source session differs from original verified ledger')
        rows,invalid=session_rows(session);sources[item['key']]=filehash(path)
        excluded.extend(dict(session=item['key'],**r) for r in invalid)
        population[lane].extend(dict(r,unit=unit,stimulus=stimulus,source_group='coauthor:'+r['writer'],
            historical_split=item['split'],exposure='historically parsed; earlier selection may be exposed') for r in rows)
        pulse(phase='population-source-replay',sessions=len(sources))
    for a,b in [('train','development'),('train','evaluation'),('development','evaluation')]:
        disjoint_factors(population[a],population[b],('unit','stimulus'))
        keep,_=cross.filter_fit({r['source_group'] for r in population[a]},{r['source_group'] for r in population[b]})
        if set(keep)!={r['source_group'] for r in population[a]}:raise ValueError('source dependency crosses new split')
    if any(not r for r in population.values()):raise ValueError('empty required partition')
    metadata=dict(classes=dict(coauthor=list(DECISIONS)),source_sessions=sources,
        counts={k:dict(records=len(rows),writers=len({r['writer'] for r in rows}),
            writer_components=len({r['unit'] for r in rows}),prompt_components=len({r['stimulus'] for r in rows}),
            sessions=len({r['session'] for r in rows}),classes=dict(Counter(r['truth'] for r in rows))) for k,rows in population.items()},
        exposure='descriptive expanded source support; not an independent replication of untouched people',
        source_checks='canonical source projections, ledger identities and cross-source dependencies verified',exclusions=excluded)
    freeze(out/'POPULATION.json',population);freeze(out/'SOURCE_METADATA.json',metadata)
    freeze(out/'CENSUS.json',[dict(key=r['key'],lane=k,writer=r['writer'],session=r['session'],prompt=r['prompt'],
        prior_exposure=r['exposure']) for k,rows in population.items() for r in rows])
    return dict(status='complete',kind='infrastructure',counts=metadata['counts'],
        exclusions=dict(Counter(r['reason'] for r in excluded)),fresh_confirmatory_components=0,
        controls=dict(canonical_source_replayed=True,identity_only_allocation=True,crossed_components_disjoint=True),
        files={n:filehash(out/n) for n in ('ALLOCATION.json','POPULATION.json','SOURCE_METADATA.json','CENSUS.json')})


def previous(row,population,limit=4):
    return sorted((r for r in population if r['session']==row['session'] and r['ordinal']<row['ordinal']),
                  key=lambda r:r['ordinal'])[-limit:]


def matched_donor(row,own_history,bank,population):
    """Match domain, available history length and text length, never outcomes."""
    options=[]
    for donor in bank:
        if donor['unit']==row['unit'] or donor['stimulus']==row['stimulus']:continue
        hist=previous(donor,population)
        if len(hist)<len(own_history):continue
        hist=hist[-len(own_history):] if own_history else []
        if not hist:continue
        cost=(donor['domain']!=row['domain'],
              abs(sum(len(str(r['views']['artifact'])) for r in hist)-sum(len(str(r['views']['artifact'])) for r in own_history)),
              digest([SEED,'history-donor',row['key'],donor['key']]))
        options.append((cost,donor,hist))
    if not options:raise ValueError('no component-separated donor with matched history count')
    _,donor,hist=min(options,key=lambda r:r[0])
    return donor,hist
