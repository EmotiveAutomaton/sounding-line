"""WC4 source-only session properties, canonical choices and semantic retention.

DESIGN CHECK: LESSONS3-5, CONTROLS and Week3 WC4 read 2026-10-25. Every
canonical session remains in the census. Missing opportunities remain missing,
never zero. Real inputs require sealed WB1 and PMAP sources plus a hash-pinned
local CPU tagger. Constructed annotations cannot enter a corpus plan. A changed
model/source or false final document refuses the run under either hypothesis.
"""
from collections import Counter
import hashlib
import math
from pathlib import Path
import time
import unicodedata

import numpy as np

from . import week3_frames_io as io
from . import week3_outcome_blocks_recovery as spans_source
from .timing_census import read,filehash
from .timing_p6 import gzread,write_equal
from .week3_pieces_coverage import authenticated
from .timing_pmap_source import completed

PROPERTIES=('sentence_length','words_per_burst','pause_before_sentence','acceptance_rate',
            'edit_after_accept_rate','retained_share','lexical_density','punctuation_rate')
CONFIG=dict(card='WC4-inputs',mode='full',expected_sessions=1399,session_limit=1399,seed=20261026)
PILOT=dict(CONFIG,mode='pilot',session_limit=140)


def summarize_tokens(sentences):
    """Pinned spaCy tokens; words contain a letter, punctuation is Unicode P."""
    all_tokens=[t for s in sentences for t in s]
    words=[t for t in all_tokens if any(c.isalpha() for c in t['text'])]
    punctuation=[t for t in all_tokens if t['text'] and all(unicodedata.category(c).startswith('P') for c in t['text'])]
    lengths=[sum(any(c.isalpha() for c in t['text']) for t in s) for s in sentences]
    lengths=[n for n in lengths if n]
    return dict(sentence_length=float(np.mean(lengths)) if lengths else None,
                lexical_density=sum(t['pos'] in {'NOUN','PROPN','VERB','ADJ','ADV'} for t in words)/len(words) if words else None,
                punctuation_rate=len(punctuation)/(len(words)+len(punctuation)) if words or punctuation else None,
                artifact_words=len(words),artifact_sentences=len(lengths))


class LocalTagger:
    def __init__(self,manifest):
        import importlib.metadata
        import spacy
        spacy.require_cpu()
        pin=read(manifest)
        if pin['model']!='en_core_web_sm' or pin['model_version']!='3.8.0':raise ValueError('frozen WC4 English POS model required')
        for package,version in pin['versions'].items():
            if importlib.metadata.version(package)!=version:raise ValueError('WC4 tagger version changed')
        root=Path(pin['model_root']).resolve()
        for relative,expected in pin['files'].items():
            path=(root/relative).resolve();path.relative_to(root)
            if filehash(path)!=expected:raise ValueError('WC4 tagger bytes changed')
        self.nlp=spacy.load(root,disable=['parser','ner','lemmatizer'])
        self.nlp.add_pipe('sentencizer')

    def __call__(self,text):
        doc=self.nlp(text)
        return summarize_tokens([[dict(text=t.text,pos=t.pos_) for t in s if not t.is_space] for s in doc.sents])


def prepare_session(meta,events,timeline,canonical,p6,wb1,annotation):
    sid=meta['session']
    if any(wb1[k]!=meta[k] for k in ('session','writer','prompt','timestamp')):raise ValueError('WC4 event identity differs')
    if wb1['final_document_sha256']!=hashlib.sha256(timeline['final_document'].encode()).hexdigest():raise ValueError('WC4 final document differs')
    spans=[s for s in spans_source.spans(events,timeline,canonical) if s['canonical']]
    menu=[m for m in io.menus(events,timeline,canonical) if not m['censored']]
    counts=Counter(m['handling'] for m in menu);accepted=counts['accept']+counts['edit']
    tokens=[w for w in p6['words'] if w['is_word']]
    burst_words=[]
    for b in wb1['actions']:
        if b['kind']=='burst':
            ordinals=set(b['source_ordinals']);burst_words.append(sum(w['ordinal'] in ordinals for w in tokens))
    pauses=[v['interval_seconds'] for v in wb1['intervals'] if v['location'] in {'before_sentence','before_paragraph'}]
    if any(not math.isfinite(v) or v<=0 for v in pauses):raise ValueError('WC4 sentence intervals invalid')
    original=sum(s['original_codepoints'] for s in spans);retained=sum(s['retained_codepoints'] for s in spans)
    props=dict(sentence_length=annotation['sentence_length'],words_per_burst=float(np.mean(burst_words)) if burst_words else None,
               pause_before_sentence=float(np.mean(pauses)) if pauses else None,
               acceptance_rate=accepted/len(menu) if menu else None,edit_after_accept_rate=counts['edit']/accepted if accepted else None,
               retained_share=retained/original if original else None,
               lexical_density=annotation['lexical_density'],punctuation_rate=annotation['punctuation_rate'])
    if any(v is not None and (not math.isfinite(v) or v<0) for v in props.values()):raise ValueError('invalid WC4 property')
    return dict(**{k:meta[k] for k in ('session','writer','prompt','timestamp')},properties=props,events=wb1['raw_events'],
                event_eligible=wb1['raw_events']>=50,missing=[k for k,v in props.items() if v is None],
                opportunities=dict(typed_words=len(tokens),bursts=len(burst_words),sentence_pauses=len(pauses),observed_menus=len(menu),
                                   censored_menus=len(io.menus(events,timeline,canonical))-len(menu),accepted_menus=accepted,
                                   original_accepted_codepoints=original,retained_accepted_codepoints=retained,**{k:annotation[k] for k in ('artifact_words','artifact_sentences')}))


def assemble(sessions):
    return dict(sessions=sessions,summary=dict(card='WC4-inputs',sessions=len(sessions),writers=len({s['writer'] for s in sessions}),
                event_eligible=sum(s['event_eligible'] for s in sessions),complete_properties=sum(s['event_eligible'] and not s['missing'] for s in sessions),
                property_missing={k:sum(s['properties'][k] is None for s in sessions) for k in PROPERTIES},properties=list(PROPERTIES),
                support_state='source_only',support=False))


def run(output,inputs,config,verification=False):
    started=time.process_time()
    if config['mode']!='constructed' and config not in (CONFIG,PILOT):raise ValueError('frozen WC4 source configuration required')
    output=Path(output)
    binding=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    if config['mode']=='constructed':
        if set(inputs)!={'fixture'}:raise ValueError('constructed WC4 fixture required')
        def prepare(**args):
            annotation=args.pop('annotation');wb1=args.pop('wb1')
            return prepare_session(**args,wb1=wb1,annotation=annotation)
        result=io.run(output,inputs,config,prepare,assemble,verification)
    else:
        if set(inputs)!={'pmap_completion','event_completion','event_index','event_result','model_manifest','tagger_completion'}:raise ValueError('full WC4 source inputs required')
        smoke_root=Path(inputs['tagger_completion']).resolve().parent
        completed(inputs['tagger_completion'],smoke_root/'output/TAGGER_SMOKE.json')
        smoke=read(smoke_root/'output/TAGGER_SMOKE.json')
        if smoke.get('card')!='WC4-tagger-smoke' or smoke.get('model_manifest_sha256')!=filehash(inputs['model_manifest']):raise ValueError('actual WC4 POS model gate required')
        for k in ('event_index','event_result'):authenticated(inputs['event_completion'],inputs[k])
        source_result=read(inputs['event_result'])
        if source_result['sessions']!=1399:raise ValueError('full WC4 event census required')
        for path,expected in source_result['source_bindings'].items():
            if filehash(path)!=expected:raise ValueError('WC4 original event source changed')
        index_path=Path(inputs['event_index']).resolve();rows=read(index_path);index={r['session']:r for r in rows}
        if len(rows)!=1399 or len(index)!=1399:raise ValueError('WC4 event census differs')
        pmap_root=Path(inputs['pmap_completion']).resolve().parent
        completed(inputs['pmap_completion'],pmap_root/'PLAN.json')
        p2_index=Path(read(pmap_root/'PLAN.json')['inputs']['session_index']).resolve()
        p2_pins={r['session']:r['sha256'] for r in read(p2_index)}
        tagger=LocalTagger(inputs['model_manifest'])
        def prepare(**args):
            item=index[args['meta']['session']];path=(index_path.parent/item['file']).resolve();path.relative_to(index_path.parent)
            if filehash(path)!=item['sha256']:raise ValueError('WC4 event unit changed')
            wb1=gzread(path)
            if wb1['raw_sha256']!=args['timeline']['source_sha256'] or wb1['p2_sha256']!=p2_pins[args['meta']['session']]:raise ValueError('WC4 original raw/P2 identity differs')
            value=prepare_session(**args,wb1=wb1,annotation=tagger(args['timeline']['final_document']))
            if filehash(path)!=item['sha256']:raise ValueError('WC4 event unit changed during extraction')
            return value
        result=io.run(output,{'pmap_completion':inputs['pmap_completion']},config,prepare,assemble,verification)
    if binding!=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())}):raise ValueError('WC4 input changed during run')
    if verification:
        if read(output/'WC4_INPUT_BINDING.json')!=binding:raise ValueError('WC4 complete source binding differs')
    else:
        write_equal(output/'WC4_INPUT_BINDING.json',binding)
        if not (output/'WC4_TIMING.json').exists():
            cpu=time.process_time()-started
            write_equal(output/'WC4_TIMING.json',dict(cpu_seconds=cpu,
                projected_full_source_and_replay_cpu_seconds=2*cpu*config['expected_sessions']/config['session_limit'],
                includes='cold model load, full source validation and extraction; full first-tenth ratio is conservative',
                excludes='prior/native/pilot charges and later statistics'))
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
