"""WA0 authenticated session-summary inputs; no identification scores.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7 reread 2026-10-25.
Null and alternative both require the entire completed population, exact
identities, provenance partition and original profile reconstruction. Changed
bytes, duplicate sessions, missing variants or unequal source joins refuse
completion. No unsupported channel is silently zero-filled. Real/reference
profile aggregation is declared separately from the retained pooled audit.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import math
from pathlib import Path
import unicodedata

from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_pmap_source import completed
from .timing_stats import bind, check_binding
from . import timing_pmap_stats as pmap
from . import engine_habits_identification as habits
from . import week_genre_compare as genre
from .timing_text import tokens, WORD

CONFIG = dict(card='WA0-inputs', schema=1, mode='full', expected_sessions=1399,
              expected_genre_sessions=990, expected_genre_writers=24)
CONSTRUCTED = dict(CONFIG, mode='constructed', expected_sessions=24,
                   expected_genre_sessions=24, expected_genre_writers=3)
INPUTS = {'pmap_completion','habit_completion','document_completion','genre_completion'}
CHANNELS = pmap.CHANNELS[:-1]


def accepted_share(document):
    """Surviving accepted codepoints divided by all final-document codepoints."""
    text = document['text']
    if hashlib.sha256(text.encode('utf8')).hexdigest() != document['textSha256']:
        raise ValueError('final document text digest differs')
    cursor = accepted = 0
    for span in document['provenance']:
        if (type(span['start']) is not int or type(span['end']) is not int
                or span['start'] != cursor or not cursor < span['end'] <= len(text)
                or span['source'] not in ('typed','accepted','prompt')):
            raise ValueError('unsupported or incomplete provenance partition')
        if span['source'] == 'accepted': accepted += span['end']-span['start']
        cursor = span['end']
    if cursor != len(text) or not text:
        raise ValueError('empty or incomplete final document')
    return accepted/len(text)


def final_style(document, dictionary):
    word, punct = Counter(), Counter()
    for token in tokens(document['text']):
        if WORD.fullmatch(token): word[token] += 1
        elif all(unicodedata.category(c).startswith('P') for c in token): punct[token] += 1
    total = sum(word.values())+sum(punct.values())
    return ([word[k]/total if total else None for k in dictionary['words']]+
            [punct[k]/total if total else None for k in dictionary['punctuation']])


def unique(rows, key='session'):
    result = {r[key]:r for r in rows}
    if not rows or len(rows) != len(result): raise ValueError('duplicate or empty source roster')
    return result


def prepare(pmap_rows, habit_rows, documents, dictionary, genre_rows, genre_dictionary, genre_summary):
    process = unique(pmap_rows)
    hh = unique([dict(r, session=r['keys']['session']) for r in habit_rows])
    dd = unique([dict(r, session=r['keys']['session']) for r in documents])
    if set(process) != set(hh) or set(process) != set(dd):
        raise ValueError('complete source populations differ')
    lengths = defaultdict(list)
    for row in pmap_rows: lengths[row['prompt']].append(row['final_words'])
    prompt_medians = {p:pmap.median(v) for p,v in lengths.items()}
    rows = []
    for sid,row in sorted(process.items()):
        keys = {k:row[k] for k in ('session','writer','prompt')}
        if any(value['keys'] != keys for value in (hh[sid],dd[sid])):
            raise ValueError('cross-producer session identity differs')
        vectors = pmap.profile([row],dictionary,prompt_medians)
        features = {'PMAP.'+c:vectors[c] for c in CHANNELS}
        features.update({'EV3.'+v:habits.vector(hh[sid][v]) for v in habits.VARIANTS})
        features['PMAP.final_style'] = final_style(dd[sid],dictionary)
        rows.append(dict(**keys,timestamp=row['timestamp'],
                         accepted_share=accepted_share(dd[sid]),features=features))
    g_rows = []
    for row in sorted(genre_rows,key=lambda r:r['session']):
        if row['session'] not in process: raise ValueError('genre session outside complete corpus')
        if any(row[k] != process[row['session']][k] for k in ('writer','prompt','timestamp')):
            raise ValueError('genre chronology or identity differs')
        g_rows.append({**{k:row[k] for k in ('session','writer','prompt','timestamp','genre','pair','half')},
                       'features':genre.profile([row],genre_dictionary)})
    unique(g_rows)
    if genre_summary['mode'] != 'primary' or not genre_summary['primary_population_supported']:
        raise ValueError('original matched primary population required')
    legacy_pmap, excluded, splits = pmap.profiles(pmap_rows,dictionary)
    legacy_genre, g_splits = genre.profiles(genre_rows,genre_dictionary,'primary')
    legacy = dict(pmap=legacy_pmap, pmap_excluded=excluded, pmap_splits=splits,
                  genre={g:{w:v for (w,gg),v in legacy_genre.items() if gg==g} for g in genre.GENRES},
                  genre_splits={g:{w:v for (w,gg),v in g_splits.items() if gg==g} for g in genre.GENRES})
    return dict(rows=rows,genre_rows=g_rows,legacy=legacy,
                names={'PMAP.'+k:v for k,v in pmap.feature_names(dictionary).items() if k in CHANNELS},
                method='WA0.session-summary: finite-feature mean over whole sessions in every arm; original pooled profiles retained only as audit')


def load(inputs, config):
    if config not in (CONFIG,CONSTRUCTED) or set(inputs) != INPUTS: raise ValueError('fixed WA0 input commission required')
    bindings = {}
    def artifact(key, relative):
        terminal = Path(inputs[key]).resolve(); path = terminal.parent/relative
        completed(terminal,path)
        bindings[str(terminal)] = filehash(terminal); bindings[str(path)] = filehash(path)
        return gzread(path) if path.suffix == '.gz' else read(path)
    allowed = {'pmap_completion':{'runners.drive.cards.timing_pmap_recovery'},
               'habit_completion':{'runners.drive.cards.engine_habits_input'},
               'document_completion':{'runners.drive.cards.engine_input_full'},
               'genre_completion':{'runners.drive.cards.week_genre_features_resume'}}
    for key in sorted(INPUTS):
        if artifact(key,'PLAN.json')['module'] not in allowed[key]: raise ValueError('wrong input producer')
    terminal = read(inputs['pmap_completion'])
    pmap_rows = [artifact('pmap_completion',n) for n in sorted(terminal['outputs'])
                 if n.startswith('output/sessions/') and n.endswith('.json.gz')]
    dictionary = artifact('pmap_completion','output/STYLE_DICTIONARY.json')
    habit_rows = artifact('habit_completion','output/HABITS.json.gz')
    summary = artifact('habit_completion','output/SUMMARY.json')
    if not summary['final_export_parity'] or summary['documents'] != config['expected_sessions']:
        raise ValueError('complete habit input parity absent')
    source = Path(inputs['document_completion']).resolve(); doc_path = source.parent/'output/DOCUMENTS.jsonl'
    completed(source,doc_path); bindings[str(doc_path)] = filehash(doc_path)
    import json
    with doc_path.open(encoding='utf8') as stream: documents = [json.loads(s) for s in stream]
    genre_rows = artifact('genre_completion','output/FEATURES.json.gz')
    gd = artifact('genre_completion','output/DICTIONARY.json')
    gs = artifact('genre_completion','output/SUMMARY.json')
    if (len(pmap_rows) != config['expected_sessions'] or len(genre_rows) != config['expected_genre_sessions']
            or len({r['writer'] for r in genre_rows}) != config['expected_genre_writers']):
        raise ValueError('fixed complete population changed')
    prepared = prepare(pmap_rows,habit_rows,documents,dictionary,genre_rows,gd,gs)
    return prepared,bindings


def run(output,inputs,config,verification=False):
    output = Path(output); output.mkdir(parents=True,exist_ok=True)
    value,bindings = load(inputs,config)
    summary = dict(card='WA0-inputs',sessions=len(value['rows']),
                   writers=len({r['writer'] for r in value['rows']}),
                   genre_sessions=len(value['genre_rows']),
                   genre_writers=len({r['writer'] for r in value['genre_rows']}),
                   channels=sorted(value['rows'][0]['features']),
                   scientific_admission=False,method=value['method'])
    if verification:
        check_binding(output,inputs,config)
        if gzread(output/'INPUTS.json.gz') != value or read(output/'SUMMARY.json') != summary or read(output/'SOURCE_BINDINGS.json') != bindings:
            raise ValueError('fresh complete WA0 input reconstruction differs')
        return dict(verified=True,source_only=True)
    gzip_equal(output/'INPUTS.json.gz',value); write_equal(output/'SUMMARY.json',summary)
    write_equal(output/'SOURCE_BINDINGS.json',bindings)
    if (output/'TIMING_BINDINGS.json').exists(): check_binding(output,inputs,config)
    else: bind(output,inputs,config,['INPUTS.json.gz','SUMMARY.json','SOURCE_BINDINGS.json'])
    return dict(status='complete',source_only=True)


def execute(output,inputs,config): return run(output,inputs,config)
def verify(output,inputs,config): return run(output,inputs,config,True)
