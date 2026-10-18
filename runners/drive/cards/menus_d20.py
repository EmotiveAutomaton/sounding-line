"""D20 dismissed-menu uptake beyond same-prompt/progress donor menus.

DESIGN CHECK: LESSONS 3-5 read October18. Under independent menu/continuation
pairing, observed minus the exact donor-randomization expectation is zero;
planted overlap is positive and anti-overlap negative. Donors exclude the entire
recipient session, including sampled copies. Bootstrap refits donor weights
after resampling writer nodes. Empty donor strata/short tails are explicit
exclusions, not zeros. Lexical primary versus cosine secondary was owner-approved
before corpus outcomes. No posthoc choice between channels is permitted.
"""
from collections import Counter,defaultdict
from pathlib import Path
import math
import re
import time
import numpy as np
from . import states_v2 as states
from . import menus_d20_sources as source
from . import menus_d12 as intervals
from .events_p5 import Encoder
from .menus_io import read,write,sha256,input_hashes,assert_equal

CONFIG=dict(seed=20261018,bootstrap=2000,minimum_writers=4,maximum_undefined_fraction=.05,threads=2,batch_size=16)
# Fixed transparent function-word proxy, not a claim of part-of-speech annotation.
FUNCTION_WORDS=frozenset('a an the and or but if as of to in on at by for with from into over under is are was were be been being do does did have has had can could shall should will would may might must this that these those i me my mine we us our ours you your yours he him his she her hers it its they them their theirs not no nor so than then when where why how all any each every some such both either neither who whom whose which what there here'.split())
WORD=re.compile(r"[^\W_]+(?:['’][^\W_]+)*",re.UNICODE)


def content_words(text):
    return frozenset(m.group().casefold() for m in WORD.finditer(text) if m.group().casefold() not in FUNCTION_WORDS)


def lexical(options,window):
    values=[len(words & window)/len(words) for words in options if words]
    return float(np.mean(values)) if values else None


def prepared(rows):
    return [dict(r,content_options=[content_words(s) for s in r['options']],
                 content_window=content_words(r['window']) if r['window'] is not None else None,
                 mean_vector=np.mean(r['option_vectors'],axis=0) if r['option_vectors'] else None) for r in rows]


def comparisons(rows,channel,seed=None):
    """Exact expected overlap under uniform donor session, menu, then option."""
    rows=prepared(rows);strata=defaultdict(list)
    for row in rows:strata[(row['prompt'],row['progress_decile'])].append(row)
    targets=[r for r in rows if r['handling']=='dismiss' and r['window'] is not None]
    if seed is not None:
        grouped=defaultdict(list);rng=np.random.default_rng(seed)
        for r in targets:grouped[(r['prompt'],r['progress_decile'])].append(r)
        changed=[]
        for _,group in sorted(grouped.items()):
            for r,j in zip(group,rng.permutation(len(group))):
                donor=group[int(j)]
                changed.append(r|dict(content_window=donor['content_window'],window_vector=donor['window_vector']))
        targets=changed
    writers=sorted({r['writer'] for r in rows});lookup={w:i for i,w in enumerate(writers)}
    result=[];excluded=Counter()
    for row in sorted(targets,key=lambda r:r['key']):
        def overlap(candidate):
            if channel=='lexical':return lexical(candidate['content_options'],row['content_window'])
            return float(np.dot(candidate['mean_vector'],row['window_vector'])) if candidate['mean_vector'] is not None else None
        own=overlap(row)
        if own is None:excluded['no supported offered option']+=1;continue
        sessions=defaultdict(list);owners={}
        for donor in strata[(row['prompt'],row['progress_decile'])]:
            if donor['session']==row['session']:continue
            value=overlap(donor)
            if value is not None:
                sessions[donor['session']].append(value);owners[donor['session']]=donor['writer']
        if not sessions:excluded['no other-session donor in prompt/progress stratum']+=1;continue
        sums=np.zeros(len(writers));counts=np.zeros(len(writers))
        for sid,values in sorted(sessions.items()):
            j=lookup[owners[sid]];sums[j]+=float(np.mean(values));counts[j]+=1
        result.append(dict(key=row['key'],writer=row['writer'],session=row['session'],half=row['half'],
                           observed=own,donor_sum=sums.tolist(),donor_sessions=counts.tolist()))
    return result,writers,dict(excluded)


def estimates(rows,writers,multiplicity):
    if not len(rows):return None,{},{}
    counts=np.asarray([r['donor_sessions'] for r in rows]);sums=np.asarray([r['donor_sum'] for r in rows])
    denominator=counts@multiplicity
    lookup={w:i for i,w in enumerate(writers)};by_session=defaultdict(list)
    for i,r in enumerate(rows):
        if multiplicity[lookup[r['writer']]]<=0:continue
        if denominator[i]<=0:return None,{},{}
        by_session[(r['writer'],r['half'],r['session'])].append(r['observed']-float(sums[i]@multiplicity)/denominator[i])
    by_writer=defaultdict(list);halves=defaultdict(list)
    for (writer,half,_),values in sorted(by_session.items()):
        by_writer[writer].append(float(np.mean(values)));halves[(writer,half)].append(float(np.mean(values)))
    means={w:float(np.mean(v)) for w,v in sorted(by_writer.items())}
    hs={w:[float(np.mean(halves[w,k])) if halves[w,k] else None for k in (0,1)] for w in means}
    total=sum(multiplicity[lookup[w]] for w in means)
    point=sum(means[w]*multiplicity[lookup[w]] for w in means)/total if total else None
    return point,means,hs


def summarize(rows,writers,config,reliability=False):
    count=len(writers);point,means,halves=estimates(rows,writers,np.ones(count))
    if len(means)<config['minimum_writers']:point=None
    rng=np.random.default_rng(config['seed']);draws=[];reliability_draws=[]
    eligible=sorted(w for w,pair in halves.items() if all(v is not None for v in pair))
    corr=intervals.correlation([halves[w][0] for w in eligible],[halves[w][1] for w in eligible]) if reliability and len(eligible)>=config['minimum_writers'] else None
    for _ in range(config['bootstrap']):
        index=rng.integers(count,size=count);weights=np.bincount(index,minlength=count)
        value,_,hs=estimates(rows,writers,weights);draws.append(value)
        if reliability:
            selected=[writers[i] for i in index if writers[i] in hs and all(v is not None for v in hs[writers[i]])]
            reliability_draws.append(intervals.correlation([hs[w][0] for w in selected],[hs[w][1] for w in selected]) if len(set(selected))>=3 else None)
    return dict(primary=intervals.interval(point,draws,config),writers=len(means),menus=len(rows),
                per_writer=means,split_half_reliability=intervals.interval(corr,reliability_draws,config) if reliability else None)


def analyze(rows,config,reliability=False):
    arms={};comparisons_saved={}
    for channel in ('lexical','embedding'):
        for arm,seed in (('observed',None),('outcome_control',config['seed']+1)):
            comparison,writers,excluded=comparisons(rows,channel,seed)
            label=channel+'_'+arm;comparisons_saved[label]=dict(rows=comparison,writers=writers,exclusions=excluded)
            arms[label]=summarize(comparison,writers,config,reliability=reliability and arm=='observed')|dict(exclusions=excluded)
    return arms,comparisons_saved


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/'BINDING.json').exists():assert_equal(read(output/'BINDING.json'),binding)
    else:write(output/'BINDING.json',binding)
    if (output/'SUMMARY.json').exists():verify(output,inputs,config);return read(output/'SUMMARY.json')
    data=source.load(inputs);rows=[];counts=Counter();hashes={};encoder=None;total=len(data['sessions'])
    for i,sid in enumerate(sorted(data['sessions'])):
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',saved_sessions=i)
        path=output/'sessions'/(sid+'.json')
        if path.exists():
            if sha256(path)!=read(path.with_suffix('.seal.json'))['sha256']:raise ValueError('changed session checkpoint')
            saved=read(path);assert_equal(saved['binding'],binding)
        else:
            batch,support,pins=source.session_rows(data,sid)
            targets=[r for r in batch if r['handling']=='dismiss' and r['window'] is not None]
            if targets:
                if encoder is None:encoder=Encoder(inputs['content_model'],config['threads'],config['batch_size'])
                vectors,visibility=encoder.encode([r['window'] for r in targets])
                for r,v,scope in zip(targets,vectors,visibility):r.update(window_vector=v.tolist(),visibility=scope)
            saved=dict(binding=binding,rows=batch,support=support,source_pins=pins)
            write(path,saved);write(path.with_suffix('.seal.json'),dict(sha256=sha256(path)))
        rows.extend(saved['rows']);counts.update(saved['support']);hashes[path.relative_to(output).as_posix()]=sha256(path)
        if i+1>=math.ceil(.1*total) and not (output/'FIRST_TENTH.json').exists():
            elapsed=time.perf_counter()-started;write(output/'FIRST_TENTH.json',dict(completed_sessions=i+1,total_sessions=total,
                elapsed_seconds=elapsed,projected_seconds=elapsed*total/(i+1)))
    if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',saved_sessions=total)
    arms,comparisons_saved=analyze(rows,config)
    write(output/'COMPARISONS.json',comparisons_saved)
    primary=arms['lexical_observed']['primary']
    report=dict(card='D20',descriptive=True,scientific_admission=False,primary=primary,state=primary['state'],arms=arms,
        input_hashes=binding['inputs'],config=config,session_hashes=hashes,counts=dict(counts),comparisons_hash=sha256(output/'COMPARISONS.json'),
        estimand='Equal writers, equal sessions within writer, equal dismissed menus within session. Lexical suggestion-content-word recall primary; MiniLM cosine secondary. Next50 completed newly typed words, including later revisions.',
        baseline='Exact permutation expectation: uniform other session with same prompt and completed-typed-word progress decile, then uniform menu and supported option. Recipient session excluded in full. Bootstrap resamples writers and recomputes donor weights.',
        uncertainty='Writer-node bootstrap of target and donor roles together; lexical primary and embedding secondary fixed before outcomes.',
        extension='Separate split-half reliability only if lexical primary positive or marginal; not computed by this primary runner.')
    write(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);report=read(output/'SUMMARY.json');binding=dict(inputs=input_hashes(inputs),config=config)
    assert_equal(report['input_hashes'],binding['inputs']);assert_equal(report['config'],config);data=source.load(inputs);rows=[]
    for sid in sorted(data['sessions']):
        path=output/'sessions'/(sid+'.json')
        if sha256(path)!=report['session_hashes'][path.relative_to(output).as_posix()]:raise ValueError('changed session output')
        saved=read(path);expected,support,pins=source.session_rows(data,sid)
        actual=[{k:v for k,v in r.items() if k not in ('window_vector','visibility')} for r in saved['rows']]
        assert_equal(actual,expected);assert_equal(support,saved['support']);assert_equal(pins,saved['source_pins'])
        for r in saved['rows']:
            if r['handling']=='dismiss' and r['window'] is not None:
                v=np.asarray(r['window_vector']);
                if v.shape!=(384,) or not np.isfinite(v).all() or not np.isclose(np.linalg.norm(v),1,atol=1e-5):raise ValueError('invalid saved window vector')
        rows.extend(saved['rows'])
    arms,comparisons_saved=analyze(rows,config)
    if sha256(output/'COMPARISONS.json')!=report['comparisons_hash']:raise ValueError('changed comparisons')
    assert_equal(comparisons_saved,read(output/'COMPARISONS.json'));assert_equal(arms,report['arms']);assert_equal(report['primary'],arms['lexical_observed']['primary'])
    return dict(verified=True,primary_recomputed=report['primary'],state=report['state'],source_windows_replayed=True)
