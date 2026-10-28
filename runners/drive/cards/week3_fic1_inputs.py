"""FIC1 complete typed-production and final-document inputs; no identification.

DESIGN CHECK: LESSONS 2-5 reread for this source preparation, 2026-10-27.
Under both null and alternative, exact source identities, original GEN1 cohort,
prompt halves and untrimmed typed occurrences must agree. Missing, duplicate,
changed or crossed-half records refuse completion rather than selecting a new
population. Known-answer fixtures retain an upstream-only session, restored
typed words, Unicode, deleted production and mixed final-document provenance.
No feature fitting, identification statistic, AUTH payload or new control runs.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from runners.stage14.common import read, filehash, freeze, atomic, digest
from .week_genre_inputs import validate_words, GENRES
from .week_genre_inputs_recovery import load as word_source
from .timing_pmap_source import completed
from .timing_p6 import gzread

CONFIG = dict(card='FIC1-inputs', schema=1, mode='full', source_sessions=1399,
              selected_sessions=990, writers=24)
CONSTRUCTED = dict(CONFIG, mode='constructed', source_sessions=13,
                   selected_sessions=12, writers=3)
WORD_FIELDS = ('index','token','is_word','ordinal','completed_ordinal','seconds')
IDENTITY = ('session','writer','prompt')


def unique(rows, key='session'):
    indexed = {r[key]: r for r in rows}
    if not rows or len(indexed) != len(rows):
        raise ValueError('empty or duplicate source identity')
    return indexed


def document_check(row):
    text = row['text']
    if not isinstance(text,str) or hashlib.sha256(text.encode('utf8')).hexdigest()!=row['textSha256']:
        raise ValueError('final document text hash differs')
    cursor=0; accepted=0
    for span in row['provenance']:
        if (type(span['start']) is not int or type(span['end']) is not int or
            span['start']!=cursor or not cursor<span['end']<=len(text) or
            span['source'] not in ('prompt','accepted','typed')):
            raise ValueError('final provenance does not partition the exact text')
        if span['source']=='accepted': accepted+=span['end']-span['start']
        cursor=span['end']
    if cursor!=len(text): raise ValueError('final provenance coverage incomplete')
    return accepted


def prepare(words, documents, matches, config):
    if config not in (CONFIG,CONSTRUCTED): raise ValueError('frozen FIC1 source policy required')
    ww=unique(words); dd=unique([dict(r,session=r['keys']['session']) for r in documents]); mm=unique(matches)
    if len(ww)!=config['source_sessions'] or ww.keys()!=dd.keys() or not mm.keys()<=ww.keys():
        raise ValueError('complete predecessor populations must agree and cover every selected session')
    if len(mm)!=config['selected_sessions'] or len({m['writer'] for m in matches})!=config['writers']:
        raise ValueError('original GEN1 cohort differs')
    accepted={}
    for sid,w in ww.items():
        if any(not isinstance(w[k],str) or not w[k] for k in IDENTITY) or w['genre'] not in GENRES:
            raise ValueError('invalid source identity or genre')
        if any(w[k]!=dd[sid]['keys'][k] for k in IDENTITY): raise ValueError('document identity differs')
        validate_words(w['words'])
        accepted[sid]=document_check(dd[sid])
    units=[]; groups=defaultdict(list)
    for sid,m in sorted(mm.items()):
        w=ww[sid]; d=dd[sid]
        if any(m[k]!=w[k] for k in (*IDENTITY,'genre','timestamp')):
            raise ValueError('matched source identity or chronology differs')
        actual=validate_words(w['words']); quota=m['typed_words']
        if (type(m['half']) is not int or m['half'] not in (0,1) or type(quota) is not int or
            not 0<quota<=len(actual) or len(actual)!=m['original_typed_words'] or
            len(w['words'])!=m['original_token_count']):
            raise ValueError('matched source count or split differs')
        selected=actual[:quota]
        stop=len(w['words']) if quota==len(actual) else selected[-1]['index']+1
        if (m['word_indices']!=[x['index'] for x in selected] or
            m['token_stop_exclusive']!=stop or m['boundary_completed_ordinal']!=selected[-1]['completed_ordinal']):
            raise ValueError('original matching prefix differs')
        row=dict(**{k:m[k] for k in (*IDENTITY,'genre','timestamp','half','pair')},
            matched_typed_words=quota,full_typed_words=len(actual),
            typed_production=[{k:r[k] for k in WORD_FIELDS} for r in w['words']],
            final_document=dict(text=d['text'],textSha256=d['textSha256'],provenance=d['provenance']),
            final_accepted_characters=accepted[sid],final_characters=len(d['text']))
        units.append(row); groups[(row['writer'],row['genre'],row['half'])].append(row)
    writers=sorted({r['writer'] for r in units})
    if set(groups)!={(w,g,h) for w in writers for g in GENRES for h in (0,1)}:
        raise ValueError('missing original genre by prompt-half cell')
    profiles=[]
    for w in writers:
        for g in GENRES:
            if {r['prompt'] for r in groups[w,g,0]} & {r['prompt'] for r in groups[w,g,1]}:
                raise ValueError('original prompt halves overlap')
            for h in (0,1):
                rows=sorted(groups[w,g,h],key=lambda r:(r['timestamp'],r['session']))
                profiles.append(dict(writer=w,genre=g,half=h,sessions=[r['session'] for r in rows],
                    matched_typed_words=sum(r['matched_typed_words'] for r in rows),
                    full_typed_words=sum(r['full_typed_words'] for r in rows),
                    final_characters=sum(r['final_characters'] for r in rows)))
    summary=dict(card='FIC1-inputs',constructed=config['mode']=='constructed',source_sessions=len(ww),
        selected_sessions=len(units),writers=len(writers),genre_half_profiles=len(profiles),
        matched_typed_words=sum(r['matched_typed_words'] for r in units),
        full_typed_words=sum(r['full_typed_words'] for r in units),
        restored_typed_words=sum(r['full_typed_words']-r['matched_typed_words'] for r in units),
        unchanged_cohort_and_prompt_halves=True,all_selected_occurrences_retained=True,
        final_documents_mixed_provenance=True,source_only_unselected_sessions=len(ww.keys()-mm.keys()),
        features_computed=False,identification_computed=False,auth_requests_prepared=False,scientific_admission=False,
        scope='Original GEN1 sessions and prompt halves; complete produced typed occurrences including later deletions, plus mixed-provenance final documents. Production tokens are not an exact whitespace-preserving prose reconstruction.')
    return units,profiles,summary,sorted(ww.keys()-mm.keys())


def load(inputs,config):
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}: raise ValueError('explicit constructed source required')
        f=read(inputs['fixture'])
        return f['words'],f['documents'],f['matches'],{str(Path(inputs['fixture']).resolve()):filehash(inputs['fixture'])}
    if config!=CONFIG or set(inputs)!={'pmap_completion','genre_completion','document_completion'}:
        raise ValueError('complete frozen source bindings required')
    words,bindings,population=word_source(dict(pmap_completion=inputs['pmap_completion']))
    if population['primary_sessions']!=config['source_sessions']: raise ValueError('complete primary changed')
    genre=Path(inputs['genre_completion']).resolve(); docs=Path(inputs['document_completion']).resolve()
    for terminal,module in [(genre,'runners.drive.cards.week_genre_inputs_recovery'),(docs,'runners.drive.cards.engine_input_full')]:
        plan=terminal.parent/'PLAN.json'; completed(terminal,plan)
        if read(plan)['module']!=module: raise ValueError('unexpected predecessor producer')
        bindings[str(terminal)]=filehash(terminal); bindings[str(plan)]=filehash(plan)
    matchpath=genre.parent/'output/MATCHES.json.gz'; supportpath=genre.parent/'output/SUPPORT.json'
    docpath=docs.parent/'output/DOCUMENTS.jsonl'
    for terminal,path in [(genre,matchpath),(genre,supportpath),(docs,docpath)]:
        completed(terminal,path); bindings[str(path)]=filehash(path)
    support=read(supportpath)
    if support['mode']!='primary' or not support['primary_population_supported']:
        raise ValueError('original primary cohort required')
    with docpath.open(encoding='utf8') as stream: documents=[json.loads(line) for line in stream]
    return words,documents,gzread(matchpath),bindings


def run(output,inputs,config,verification=False):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    words,documents,matches,bindings=load(inputs,config)
    units,profiles,summary,unselected=prepare(words,documents,matches,config)
    index=[]
    def retain(path,value):
        if verification:
            if read(path)!=value: raise ValueError('complete FIC1 input replay differs: '+path.name)
        else: freeze(path,value)
    retain(output/'BINDING.json',dict(config=config,inputs=bindings))
    for i,unit in enumerate(units):
        rel='sessions/'+digest(unit['session'])+'.json'; path=output/rel
        retain(path,unit); index.append(dict(session=unit['session'],file=rel,sha256=filehash(path)))
        if (i+1)%50==0: atomic(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=i+1,total=len(units)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists(): raise InterruptedError('yield at complete source session')
    retain(output/'SESSION_INDEX.json',index); retain(output/'PROFILES.json',profiles)
    retain(output/'UNSELECTED_SESSIONS.json',unselected); retain(output/'SUMMARY.json',summary)
    if verification: return dict(verified=True,complete_input_replay=True,all_sessions_recomputed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
