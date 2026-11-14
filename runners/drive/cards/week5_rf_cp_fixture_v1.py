"""Hand-answer source fixtures. All strings are authored synthetic examples.

The literal counts below were derived by reading the frozen lists, never by the
adapter under test. These fixtures qualify intake/markers, not election models.
"""
from pathlib import Path
import gzip
import json
import zipfile

RF_CASES = (
    ('Experienced, competent, knowledgeable.', (3, 0, 0, 0, 0, 0)),
    ('Inexperienced; too few edits.', (0, 2, 0, 0, 0, 0)),
    ("I don't trust this candidate. Poor judgment.", (0, 0, 0, 2, 0, 0)),
    ('Trustworthy, honest, fair, and mature.', (0, 0, 4, 0, 0, 0)),
    ('Friendly and pleasant. A pleasure to work with.', (0, 0, 0, 0, 3, 0)),
    ('Rude, hostile, and uncivil.', (0, 0, 0, 0, 0, 3)),
    ('Skilled, with good contributions; sound judgment.', (2, 0, 1, 0, 0, 0)),
    ('Not enough experience; abuse the tools; arrogant.', (0, 1, 0, 1, 0, 1)),
    ('Competently written material has no marker here.', (0, 0, 0, 0, 0, 0)),
    ('Level\u2011headed and responsible; good guy.', (0, 0, 2, 0, 1, 0)),
    ('Doesn\u2019t understand policy; untrustworthy and unfriendly.', (0, 1, 0, 1, 0, 1)),
    ("Knows policy; I trust them, but I don't trust this proposal.", (1, 0, 1, 1, 0, 0)))

NEUTRAL = 'alpha beta gamma delta epsilon zeta eta theta iota kappa.'
# Each side: text, tokens, (warmth, deference, assertion).
CP_PAIRS = (
    (('Stop. '+NEUTRAL, 11, (0,0,1)), ('Perhaps. '+NEUTRAL, 11, (0,1,0))),
    (('You should. '+NEUTRAL, 12, (0,0,1)), ('I think. '+NEUTRAL, 12, (0,1,0))),
    (('Thanks. '+NEUTRAL, 11, (1,0,0)), ('Thank you. '+NEUTRAL, 12, (1,0,0))),
    (('Obviously. '+NEUTRAL, 11, (0,0,1)), ('Clearly. '+NEUTRAL, 11, (0,0,1))),
    (('Do you. '+NEUTRAL, 12, (0,0,0)), ('Could you. '+NEUTRAL, 12, (0,1,0))),
    (('> Stop thanks.\n'+NEUTRAL, 10, (0,0,0)), ('Please. '+NEUTRAL, 11, (0,1,0))),
    (('Stop. Read. '+NEUTRAL, 12, (0,0,2)), ('Maybe. Sorry. '+NEUTRAL, 12, (1,1,0))),
    (('Good point. '+NEUTRAL, 12, (1,0,0)), ('Good work. '+NEUTRAL, 12, (1,0,0))),
    (('Nothing noteworthy. '+NEUTRAL, 12, (0,0,0)), ("If you don't mind. "+NEUTRAL, 14, (0,1,0))),
    (('<blockquote>You must. Thanks.</blockquote>'+NEUTRAL, 10, (0,0,0)), ("Don't. "+NEUTRAL, 11, (0,0,1))))


def prepare(root, family, repeat=1):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    salt = root / 'constructed-salt.bin'; salt.write_bytes(bytes(range(32)))
    if family == 'RF1':
        archive = root / 'constructed-rfa.txt.gz'
        records = []
        for i in range(repeat):
            for j, (text, _) in enumerate(RF_CASES):
                records.append(f'SRC:constructed-voter-{i}-{j}\nTGT:constructed-candidate-{j%3}\nVOT:1\nRES:1\nYEA:2010\nDAT:12:00, 01 January 2010\nTXT:{text}\n\n')
        archive.write_bytes(gzip.compress(''.join(records).encode('utf8'), mtime=0))
        n = 12*repeat
    else:
        archive = root / 'constructed-wiki.zip'; rows = []
        for i in range(repeat):
            for j, pair in enumerate(CP_PAIRS):
                for k, case in enumerate(pair):
                    rows.append({'id': f'constructed-{i}-{j}-{k}', 'root': f'constructed-conversation-{i}',
                        'user': 'constructed-a' if k == 0 else 'constructed-b',
                        'reply-to': None if k == 0 else f'constructed-{i}-{j}-0',
                        'text': case[0], 'timestamp': '2005-01-01', 'meta': {'is-admin': k == 0}})
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('wiki-corpus/speakers.json', json.dumps({'constructed-a': {'is-admin': True, 'edit-count': '100'}, 'constructed-b': {'is-admin': False, 'edit-count': '10'}}))
            z.writestr('wiki-corpus/utterances.jsonl', '\n'.join(json.dumps(r) for r in rows)+'\n')
        n = 20*repeat
    return archive, salt, n


def constructed_native_receipt(native, source_output):
    """Explicit synthetic runtime envelope for the real producer/consumer boundary."""
    import shutil
    from . import week5_rf_cp_source_v1 as source
    native=Path(native); target=native/'output'
    shutil.copytree(source_output,target)
    source.write_equal(native/'PLAN.json',{'module':'runners.drive.cards.week5_rf_cp_source_v1','constructed_fixture':True})
    source.write_equal(native/'VERIFIED.json',{'verified':True,'constructed_fixture':True})
    names=['PLAN.json','VERIFIED.json']+['output/'+n for n in
        ('BINDING.json','SOURCE_COMPLETE.json','SOURCE_VERIFIED.json','SUMMARY.json','REVIEW_PRIVATE.json')]
    source.write_equal(native/'COMPLETE.json',{'status':'COMPLETE','fresh_process_verified':True,
        'constructed_fixture':True,'outputs':{n:source.sha(native/n) for n in names}})
    sample=json.loads((target/'REVIEW_PRIVATE.json').read_text('utf8'))
    counts={}; labels=[]
    for row in sample:
        n=counts.get(row['family'],0);counts[row['family']]=n+1
        labels.append({'id':row['id'],'family':row['family'],'correct':n<80,'reason':'Constructed fixed 80/100 annotation boundary'})
    annotation=native/'constructed-annotations.json'
    source.write_equal(annotation,{'method':'constructed_labels','reviewer':'constructed fixture',
        'private_review_sha256':source.sha(target/'REVIEW_PRIVATE.json'),'labels':labels})
    family=json.loads((target/'SUMMARY.json').read_text('utf8'))['family']
    return {'source_native_root':str(native),'annotations':str(annotation)}, {'family':family,'constructed_fixture':True,
        'source_native_complete_sha256':source.sha(native/'COMPLETE.json'),'annotations_sha256':source.sha(annotation)}
