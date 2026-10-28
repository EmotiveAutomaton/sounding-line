"""FIC1 complete-session features, retaining pooled sufficient records.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-27. Under null and alternative,
complete predecessor seals, exact cohort/halves, production counts and document
provenance must agree. A mismatch refuses the instrument, not the hypothesis.
Known answers check denominators including out-of-dictionary tokens, Unicode,
later-deleted production, absent timing, and mixed final text. No fitting,
identification, length-curve score, statistical control or AUTH request runs.
"""
from collections import Counter
import math
from pathlib import Path
from statistics import median
import unicodedata

from runners.stage14.common import read, filehash, freeze, atomic, digest
from . import week3_fic1_inputs as source
from .timing_pmap_source import completed
from .timing_p6 import gzread, gzip_equal
from .timing_text import tokens, WORD

CONFIG = dict(card='FIC1-features', schema=1, mode='full', source_sessions=1399,
              selected_sessions=990, writers=24, dictionary='original_full_PMAP')
CONSTRUCTED = dict(CONFIG, mode='constructed', source_sessions=13, selected_sessions=12, writers=3)
IDENTITY = ('session','writer','prompt','timestamp')
SUFFICIENT = ('word_counts','punctuation_counts','within_intervals','onset_intervals',
              'bigram_intervals','tc_timing_mode')


def counts(production):
    return (dict(sorted(Counter(r['token'] for r in production if r['is_word']).items())),
            dict(sorted(Counter(r['token'] for r in production if not r['is_word'] and
                 all(unicodedata.category(c).startswith('P') for c in r['token'])).items())))


def style(words, punctuation, dictionary):
    total = sum(words.values())+sum(punctuation.values())
    return ([words.get(k,0)/total if total else None for k in dictionary['words']]+
            [punctuation.get(k,0)/total if total else None for k in dictionary['punctuation']])


def rhythm(row, dictionary):
    seq = [row['within_intervals'],row['onset_intervals']]+[
        row['bigram_intervals'].get(k,[]) for k in dictionary['character_bigrams']]
    return [float(median(v)) if v and row['tc_timing_mode']!='invalid' else None for v in seq]


def prepare(units, profiles, pmap_rows, dictionary, config):
    if config not in (CONFIG,CONSTRUCTED): raise ValueError('frozen feature configuration required')
    uu=source.unique(units); pp=source.unique(pmap_rows)
    if (len(pp)!=config['source_sessions'] or len(uu)!=config['selected_sessions'] or
        not uu.keys()<=pp.keys() or len({u['writer'] for u in units})!=config['writers']):
        raise ValueError('fixed complete population differs')
    for key in ('words','punctuation','character_bigrams'):
        values=dictionary[key]
        if not isinstance(values,list) or len(values)!=len(set(values)) or any(not isinstance(x,str) or not x for x in values):
            raise ValueError('invalid fixed dictionary')
    groups={}; seen=[]
    for group in profiles:
        key=(group['writer'],group['genre'],group['half'])
        if key in groups or type(group['half']) is not int or group['half'] not in (0,1):
            raise ValueError('duplicate or invalid profile')
        groups[key]=group
        members=sorted([u for u in units if (u['writer'],u['genre'],u['half'])==key],key=lambda u:(u['timestamp'],u['session']))
        if not members or group['sessions']!=[u['session'] for u in members]: raise ValueError('profile membership differs')
        for name in ('matched_typed_words','full_typed_words','final_characters'):
            if group[name]!=sum(u[name] for u in members): raise ValueError('profile count differs')
        seen.extend(group['sessions'])
    expected={(w,g,h) for w in {u['writer'] for u in units} for g in source.GENRES for h in (0,1)}
    if set(groups)!=expected or len(seen)!=len(uu) or set(seen)!=set(uu): raise ValueError('incomplete profile partition')
    for w in {u['writer'] for u in units}:
        for g in source.GENRES:
            if {uu[s]['prompt'] for s in groups[w,g,0]['sessions']} & {uu[s]['prompt'] for s in groups[w,g,1]['sessions']}:
                raise ValueError('prompt halves overlap')
    rows=[]
    for sid,u in sorted(uu.items()):
        p=pp[sid]
        if any(p[k]!=u[k] for k in IDENTITY): raise ValueError('source identity differs')
        production=u['typed_production']
        source.validate_words(production)
        wc,pc=counts(production)
        if (wc!=p['word_counts'] or pc!=p['punctuation_counts'] or
            sum(wc.values())!=u['full_typed_words'] or p['typed_words']!=u['full_typed_words']):
            raise ValueError('full production counts differ from PMAP')
        timing=[p['within_intervals'],p['onset_intervals'],*p['bigram_intervals'].values()]
        if (not isinstance(p['tc_timing_mode'],str) or not p['tc_timing_mode'] or
            any(not isinstance(v,list) or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in v) for v in timing)):
            raise ValueError('invalid timing values')
        document=u['final_document']; accepted=source.document_check(document)
        if accepted!=u['final_accepted_characters'] or len(document['text'])!=u['final_characters']:
            raise ValueError('final provenance counts differ')
        final_tokens=tokens(document['text'])
        final_production=[dict(token=t,is_word=bool(WORD.fullmatch(t))) for t in final_tokens]
        fw,fp=counts(final_production)
        rows.append(dict(**{k:u[k] for k in (*IDENTITY,'genre','half','pair')},
            typed_words=u['full_typed_words'],matched_typed_words=u['matched_typed_words'],
            final_words=sum(fw.values()),final_characters=u['final_characters'],
            final_accepted_characters=accepted,
            accepted_share=accepted/u['final_characters'] if u['final_characters'] else None,
            features=dict(style=style(wc,pc,dictionary),rhythm=rhythm(p,dictionary),
                          final_style=style(fw,fp,dictionary)),
            production={k:p[k] for k in SUFFICIENT},
            final_counts=dict(word_counts=fw,punctuation_counts=fp)))
    return rows,sorted(profiles,key=lambda g:(g['writer'],g['genre'],g['half']))


def load(inputs,config):
    if config==CONSTRUCTED:
        if set(inputs)!={'fixture'}: raise ValueError('explicit constructed fixture required')
        f=read(inputs['fixture'])
        return f['units'],f['profiles'],f['pmap_rows'],f['dictionary'],{str(Path(inputs['fixture']).resolve()):filehash(inputs['fixture'])}
    if config!=CONFIG or set(inputs)!={'source_completion','pmap_completion'}:
        raise ValueError('complete feature predecessors required')
    bindings={}
    def artifact(key,rel):
        terminal=Path(inputs[key]).resolve(); path=(terminal.parent/rel).resolve()
        completed(terminal,path); bindings[str(terminal)]=filehash(terminal);bindings[str(path)]=filehash(path)
        return gzread(path) if path.suffix=='.gz' else read(path)
    sp=artifact('source_completion','PLAN.json'); pp=artifact('pmap_completion','PLAN.json')
    if sp['module']!='runners.drive.cards.week3_fic1_inputs' or sp['config']!=source.CONFIG or pp['module']!='runners.drive.cards.timing_pmap_recovery':
        raise ValueError('unexpected feature predecessor')
    if Path(sp['inputs']['pmap_completion']).resolve()!=Path(inputs['pmap_completion']).resolve():
        raise ValueError('source and feature PMAP differ')
    summary=artifact('source_completion','output/SUMMARY.json')
    if not summary['unchanged_cohort_and_prompt_halves'] or not summary['all_selected_occurrences_retained']:
        raise ValueError('full source coverage not established')
    index=artifact('source_completion','output/SESSION_INDEX.json'); source.unique(index)
    units=[]
    for item in index:
        rel='output/'+item['file']; unit=artifact('source_completion',rel)
        path=Path(inputs['source_completion']).resolve().parent/rel
        if filehash(path)!=item['sha256'] or unit['session']!=item['session']: raise ValueError('source unit index differs')
        units.append(unit)
    profiles=artifact('source_completion','output/PROFILES.json')
    pc=read(inputs['pmap_completion'])
    pmap_rows=[artifact('pmap_completion',name) for name in sorted(pc['outputs'])
               if name.startswith('output/sessions/') and name.endswith('.json.gz')]
    dictionary=artifact('pmap_completion','output/STYLE_DICTIONARY.json')
    return units,profiles,pmap_rows,dictionary,bindings


def run(output,inputs,config,verification=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    units,profiles,pmap_rows,dictionary,bindings=load(inputs,config)
    rows,profiles=prepare(units,profiles,pmap_rows,dictionary,config)
    def retain(path,value):
        if verification:
            actual=gzread(path) if path.suffix=='.gz' else read(path)
            if actual!=value: raise ValueError('complete feature replay differs: '+path.name)
        elif path.suffix=='.gz': gzip_equal(path,value)
        else: freeze(path,value)
    retain(output/'BINDING.json',dict(config=config,inputs=bindings))
    index=[]
    for i,row in enumerate(rows):
        rel='sessions/'+digest(row['session'])+'.json.gz';path=output/rel
        retain(path,row);index.append(dict(session=row['session'],file=rel,sha256=filehash(path)))
        if (i+1)%50==0: atomic(output/'PROGRESS.json',dict(phase='verify' if verification else 'execute',done=i+1,total=len(rows)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists(): raise InterruptedError('yield at complete feature session')
    names=dict(style=['word:'+s for s in dictionary['words']]+['punct:'+s for s in dictionary['punctuation']],
               rhythm=['within_word','word_onset']+['bigram:'+s for s in dictionary['character_bigrams']])
    names['final_style']=names['style']
    summary=dict(card=CONFIG['card'],constructed=config['mode']=='constructed',source_sessions=len(pmap_rows),
        sessions=len(rows),writers=len({r['writer'] for r in rows}),profiles=len(profiles),
        typed_words=sum(r['typed_words'] for r in rows),final_words=sum(r['final_words'] for r in rows),
        full_production_counts_match=True,unchanged_cohort_and_prompt_halves=True,
        mixed_final_provenance_preserved=True,pooled_sufficient_records_retained=True,
        missing_rhythm_sessions=sum(all(v is None for v in r['features']['rhythm']) for r in rows),
        identification_computed=False,length_covariate_fitted=False,length_curve_computed=False,
        auth_requests_prepared=False,scientific_admission=False)
    for name,value in [('SESSION_INDEX.json',index),('PROFILES.json',profiles),('DICTIONARY.json',dictionary),
                       ('FEATURE_NAMES.json',names),('SUMMARY.json',summary)]: retain(output/name,value)
    if verification: return dict(verified=True,complete_input_replay=True,all_features_recomputed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
