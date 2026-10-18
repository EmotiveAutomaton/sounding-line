"""Causal recent-own-text window and separate explicitly later-text sentence."""
from pathlib import Path
import numpy as np
from .menus_io import read,sha256
from .timing_p6 import gzread
from . import menus_d20_sources as common


def prior_words(words,ordinal):
    rows=sorted((w for w in words if w['is_word'] and w['completed_ordinal']<ordinal),
                key=lambda w:(w['completed_ordinal'],w['index']))
    return rows[-50:]


def next_sentence(words,resolution):
    ordered=sorted((w for w in words if w['ordinal']>resolution and w['completed_ordinal']>resolution),
                   key=lambda w:(w['completed_ordinal'],w['index']))
    current=[]
    for word in ordered:
        if word['is_word'] and word.get('sentence_start',False):current=[word];continue
        if not current:continue
        if word.get('previous_typed_token_index')!=current[-1]['index']:
            current=[];continue
        current.append(word)
        if not word['is_word'] and word['token'] in ('.','!','?'):
            return current
    return None


def extract(data,sid):
    session=data['sessions'][sid];entry=data['p6'][sid]
    path=(data['p6_root']/entry['file']).resolve();path.relative_to(data['p6_root'].resolve())
    if sha256(path)!=entry['sha256']:raise ValueError('D11 ledger changed')
    ledger=gzread(path);timeline=read(data['timelines'][sid]);decisions={r['key']:r for r in timeline['decisions']}
    for record in (ledger,timeline):
        if (record['session'],record['writer'],record['prompt'])!=(sid,session['writer'],session['prompt']):raise ValueError('D11 session identity differs')
    if set(decisions)!={r['key'] for r in session['rows']}:raise ValueError('D11 coverage differs')
    rows=[]
    for row in sorted(session['rows'],key=lambda r:(r['ordinal'],r['key'])):
        before=prior_words(ledger['words'],row['ordinal']);decision=decisions[row['key']]
        if decision['handling']!=row['handling'] or decision['ordinal']!=row['ordinal']:raise ValueError('D11 decision mismatch')
        later=next_sentence(ledger['words'],decision['resolution_ordinal']) if decision['resolution_ordinal'] is not None else None
        feature=data['features'][row['key']];vectors=data['vectors'][feature['options']]
        if (feature['session'],feature['writer'])!=(sid,session['writer']) or len(vectors)!=len(row['menu']):raise ValueError('D11 content identity differs')
        selected=[j for j,text in enumerate(row['menu']) if text==row.get('inserted')]
        rows.append(dict(key=row['key'],session=sid,writer=session['writer'],prompt=session['prompt'],
            handling=row['handling'],half=data['halves'][sid],history=' '.join(w['token'] for w in before),
            history_count=len(before),history_indices=[w['index'] for w in before],
            history_completed_ordinals=[w['completed_ordinal'] for w in before],
            prompt_text=timeline['initial_document'],menu_mean_vector=vectors.mean(axis=0).tolist(),
            menu_dissimilarity=float(1-np.mean(vectors@vectors.T)) if len(vectors)>1 else 0.,
            later_sentence=None if later is None else ' '.join(w['token'] for w in later),
            later_indices=None if later is None else [w['index'] for w in later],
            accepted_vector=vectors[selected[0]].tolist() if row['handling']=='accept' and len(selected)==1 else None))
    return rows,dict(ledger=sha256(path),timeline=sha256(data['timelines'][sid]))
