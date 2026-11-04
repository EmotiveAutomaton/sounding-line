"""Week 4 R1/R2 source passes; complete populations and private provenance.

DESIGN CHECK: LESSONS 2-5 reread 2026-11-02. NULL/ALTERNATIVE: these are
source instruments, not effect gates. All three historical failures must recur
in their old implementations before R1 admission. Unicode lifetime fixtures
have exact known answers. R2 keeps failed replays with reasons, never patches
documents. Codepoints and UTF-16 units are reported separately. Smaller route:
whole-writer sample only after measured costing; full censuses remain separate.
"""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import time
from runners.stage9.coauthor import replay,units
from runners.stage9.common import digest
from runners.drive.timeline import rebuild
from .timing_events import source_sessions
from .timing_census import read,filehash
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .week3_insertion_provenance_h1 import fixture as old_fixture
from . import week3_outcome_blocks_inputs as original
from . import week3_outcome_blocks_recovery as first_repair
from . import week3_outcome_blocks_support_recovery as second_repair
from .week4_shared_spans_h1 import spans

TAGS=('typed','accepted','accepted_edited','prompt','api_unknown')

def cases():
    events,_=old_fixture('plain')
    events[1]['currentSuggestions'][0].update(original='\na\U0001f600b',trimmed='\na\U0001f600b')
    events[3]['textDelta']={'ops':[{'retain':2},{'insert':'a\U0001f600b\n'}]}
    return [('canonical_offer',events,original.spans,'actual inserted span differs from unique canonical choice'),
            ('missing_comparator',old_fixture('plain')[0],first_repair.spans,'accepted menu has no unchosen comparator'),
            ('reused_origin',old_fixture('repeated')[0],second_repair.spans,'accepted origin reused')]

def historical_checks():
    results=[]
    for name,events,old,error in cases():
        canonical=replay(events);timeline=rebuild(events,[])
        try: old(events,timeline,canonical)
        except ValueError as exc:
            if str(exc)!=error: raise ValueError('Historical case failed for the wrong reason: '+name) from exc
        else: raise ValueError('Historical failure not reproduced: '+name)
        result=spans(events,timeline,canonical)
        if len({r['origin'] for r in result})!=len(result):raise ValueError('Physical identities repeat')
        if name=='canonical_offer' and (result[0]['text']!='\na\U0001f600b' or result[0]['original_codepoints']!=4):raise ValueError('Semantic append differs')
        if name=='missing_comparator' and (result[0]['comparator_supported'] or not result[0]['canonical']):raise ValueError('Missing comparator silently replaced')
        if name=='reused_origin' and (len(result)!=2 or any(r['canonical'] for r in result)):raise ValueError('Repeated excluded choices changed eligibility')
        results.append(dict(case=name,legacy_error=error,new_passed=True,physical_insertions=len(result)))
    for kind,n in [('plain',3),('edited',2),('deleted',0)]:
        events,timeline=old_fixture(kind);result=spans(events,timeline,replay(events))
        if result[0]['retained_codepoints']!=n:raise ValueError('Known original-codepoint survival differs')
    return results

def census(events,canonical,prepared_rows=()):
    if not canonical['reconstructed'] or canonical['errors']:
        return dict(exact=False,reason='canonical source reconstruction failed',errors=canonical['errors'])
    try: timeline=rebuild(events,prepared_rows)
    except ValueError as exc: return dict(exact=False,reason=str(exc))
    if timeline['final_document']!=canonical['final_document']:
        return dict(exact=False,reason='timeline/canonical final-document mismatch')
    text=''.join(s['text'] for s in timeline['final_spans'])
    if text!=timeline['final_document']: raise ValueError('Provenance does not cover final document')
    counts=Counter({k:0 for k in TAGS});utf16=counts.copy()
    for span in timeline['final_spans']:
        if span['origin'] not in TAGS:raise ValueError('Unknown provenance tag')
        counts[span['origin']]+=len(span['text']);utf16[span['origin']]+=len(units(span['text']))
    accepted=spans(events,timeline,canonical)
    total=sum(r['original_codepoints'] for r in accepted)
    surviving=sum(r['retained_codepoints'] for r in accepted)
    if surviving!=counts['accepted']+counts['accepted_edited']:raise ValueError('Independent accepted survival differs')
    return dict(exact=True,character_counts=dict(counts),utf16_counts=dict(utf16),
        accepted_original_codepoints=total,accepted_surviving_codepoints=surviving,
        accepted_survival_share=surviving/total if total else None,timeline=timeline,
        validation_scope='Independent implementations replay the same raw delta log; no independent saved final-document oracle is asserted.')

def source_stream(inputs,card):
    source=read(inputs['source_inputs']);root=Path(source['repo_root'])
    prepared={r['session']:r for r in read(source['prepared_sessions'])}
    if card=='R1':
        for row,timeline,meta in source_sessions(source,'raw_roster'):
            raw=root/meta['path'];events=[json.loads(s) for s in raw.read_text(encoding='utf8').splitlines() if s.strip()]
            canonical=replay(events)
            yield row['session'],dict(meta,writer=row['writer']),events,canonical,timeline,prepared[row['session']]['rows']
    else:
        foundation=read(source['foundation_plan']);complete=read(source['foundation_complete'])
        if complete['plan_sha256']!=filehash(source['foundation_plan']):raise ValueError('Foundation authentication failed')
        for key in ('raw_roster','prepared_sessions'):
            if foundation['pins'][Path(source[key]).relative_to(root).as_posix()]!=filehash(source[key]):raise ValueError('Metadata changed')
        roster=read(source['raw_roster'])
        if len(roster)!=1445 or len({r['session'] for r in roster})!=1445:raise ValueError('Complete archive roster differs')
        for meta in sorted(roster,key=lambda r:r['session']):
            raw=(root/meta['path']).resolve();raw.relative_to(root)
            if filehash(raw)!=meta['source_sha256']:raise ValueError('Raw source changed')
            events=[json.loads(s) for s in raw.read_text(encoding='utf8').splitlines() if s.strip()]
            yield meta['session'],meta,events,replay(events),None,prepared.get(meta['session'],{}).get('rows',[])

def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    card=config['card'];mode=config['mode']
    if card not in ('R1','R2') or mode not in ('constructed','timing','full'):raise ValueError('Fixed record pass required')
    expected=7 if mode=='constructed' else (140 if card=='R1' else 145) if mode=='timing' else 1399 if card=='R1' else 1445
    if config!=dict(card=card,mode=mode,expected_sessions=expected):raise ValueError('Frozen population differs')
    checks=historical_checks()
    if mode=='constructed':
        if inputs:raise ValueError('No human input in constructed pass')
        def fixtures():
            for kind in ('plain','newline','rewrite','repeated','unmatched','edited','deleted'):
                e,t=old_fixture(kind)
                yield kind,dict(writer='constructed',domain='constructed'),e,replay(e),t,[]
        stream=fixtures()
    else:
        if set(inputs)!={'source_inputs'}:raise ValueError('Frozen source binding required')
        stream=source_stream(inputs,card)
    started=time.process_time();index=[];groups=defaultdict(Counter);writer_groups=defaultdict(Counter);failures=[]
    total_inserted=total_surviving=0
    for sid,meta,events,canonical,timeline,prepared_rows in stream:
        value=spans(events,timeline,canonical) if card=='R1' else census(events,canonical,prepared_rows)
        payload=dict(session=sid,writer=meta['writer'],genre=meta['domain'],source_sha256=meta.get('source_sha256'),record=value)
        target=output/'sessions'/(hashlib.sha256(sid.encode()).hexdigest()+'.json.gz')
        if verification:
            if gzread(target)!=payload:raise ValueError('Independent full source replay differs')
        else:gzip_equal(target,payload)
        index.append(dict(session=sid,file=target.relative_to(output).as_posix(),sha256=filehash(target)))
        if card=='R2':
            if not value['exact']:failures.append(dict(session=sid,reason=value['reason']))
            else:
                groups[meta['domain']].update(value['character_counts']);writer_groups[meta['writer']].update(value['character_counts'])
                total_inserted+=value['accepted_original_codepoints'];total_surviving+=value['accepted_surviving_codepoints']
        progress(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=len(index),total=expected))
        if mode=='timing' and len(index)==expected:break
    if len(index)!=expected:raise ValueError('Whole population not completed')
    summary=dict(card=card,sessions=expected,mode=mode,historical_cases=checks,scientific_admission=False,
        source_bindings={k:filehash(v) for k,v in inputs.items()})
    if card=='R2':
        def shares(c):
            n=sum(c.values());return dict(characters=n,counts=dict(c),shares={k:c[k]/n if n else None for k in TAGS})
        summary.update(exact_replays=expected-len(failures),excluded_replays=len(failures),
            by_genre={g:shares(c) for g,c in sorted(groups.items())},
            accepted_original_codepoints=total_inserted,accepted_surviving_codepoints=total_surviving,
            accepted_survival_share=total_surviving/total_inserted if total_inserted else None,
            denominator_scope='All 1445 archived sessions; failed replays listed, never patched. Character counts are Unicode codepoints.',
            replay_scope='Two implementations of the same raw log, not an independent saved final-document oracle.')
        private=dict(failures=failures,by_writer={w:shares(c) for w,c in sorted(writer_groups.items())})
        if verification:
            if read(output/'PRIVATE_CENSUS.json')!=private:raise ValueError('Complete census differs')
        else:write_equal(output/'PRIVATE_CENSUS.json',private)
    if verification:
        if read(output/'SUMMARY.json')!=summary or read(output/'INDEX.json')!=index:raise ValueError('Final source aggregation differs')
        return dict(verified=True,full_source_replay=True,scientific_admission=False)
    write_equal(output/'SUMMARY.json',summary);write_equal(output/'INDEX.json',index)
    write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started,sessions=expected))
    return dict(status='complete',scientific_admission=False)

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
