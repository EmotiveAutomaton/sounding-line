"""Text-free final-word offsets and source/timing labels; no scientific fit.

DESIGN CHECK: back-half EX1/T, LESSONS 2 (unit and join identity), Unicode
fixture lesson, original UTF-16/P6 and Week4 ruler contracts. Every final word
remains; mixed source and unsupported timing are explicit, never imputed.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import re
import shutil
import time
import unicodedata as ud

from runners.stage9 import coauthor
from . import week5_at_source as source
from . import week5_at_analysis as analysis
from . import week5_at_scoring as scoring
from . import week5_qualification_io as io
from .timing_text import TOKEN, WORD

MODULE = 'runners.drive.cards.week5_ex1'
LABELS = ('typed', 'accepted_suggestion', 'prompt')
VERSION = 'EX1-NFC-1'
LEDGER = ('OPS-S15-W3-TR3-TYPING-COMPLETE', 'OPS-S15-W4-TIMING-FULL')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def normalize_with_origins(text):
    """NFC after CRLF/CR -> LF and whole-document rstrip, with exact ancestry.

    Canonical ordering/composition carries sets of original code-point indexes.
    A composed code point can consequently have more than one source label.
    No edit-distance or repeated-spelling alignment is used.
    """
    coauthor.units(text)  # Reject unpaired surrogates before offsets are trusted.
    line = []
    at = 0
    while at < len(text):
        if text[at] == '\r':
            stop = at + 2 if text[at:at+2] == '\r\n' else at + 1
            line.append(('\n', frozenset(range(at, stop))))
            at = stop
        else:
            line.append((text[at], frozenset((at,))))
            at += 1
    while line and line[-1][0].isspace():
        line.pop()
    # Canonical decomposition and stable canonical-class ordering.
    ordered = []
    for ch, origins in line:
        for decomposed in ud.normalize('NFD', ch):
            item = (decomposed, origins)
            ccc = ud.combining(decomposed)
            position = len(ordered)
            while ccc and position and ud.combining(ordered[position-1][0]) > ccc:
                position -= 1
            ordered.insert(position, item)
    normalized = []
    starter = None
    last_ccc = 0
    for ch, origins in ordered:
        ccc = ud.combining(ch)
        composite = (ud.normalize('NFC', normalized[starter][0] + ch)
                     if starter is not None and (last_ccc < ccc or last_ccc == 0)
                     else '')
        if len(composite) == 1:
            old, ancestry = normalized[starter]
            normalized[starter] = (composite, ancestry | origins)
            continue
        if ccc == 0:
            starter = len(normalized)
        normalized.append((ch, origins))
        last_ccc = ccc
    actual = ''.join(ch for ch, _ in normalized)
    expected = ud.normalize('NFC', text.replace('\r\n', '\n').replace('\r', '\n').rstrip())
    if actual != expected:
        raise ValueError('Unicode normalization ancestry differs from standard NFC')
    return actual, [origins for _, origins in normalized]


def final_sources(events):
    """Strict replay and the already frozen verified-suggestion transform."""
    canonical = coauthor.replay(events)
    if not canonical['reconstructed']:
        raise ValueError('Final source replay is not reconstructed')
    decisions = {row['ordinal']: row for row in canonical['events']}
    document = coauthor.units(events[0]['currentDoc'])
    owners = ['prompt'] * len(document)
    active = None
    pending = False
    for ordinal, event in enumerate(events):
        name = event.get('eventName')
        if name == 'suggestion-open':
            active, pending = ordinal, False
        elif name == 'suggestion-select':
            pending = True
        ops = coauthor.delta_ops(event.get('textDelta'))
        if not ops:
            continue
        old = owners
        origin = 'typed' if event.get('eventSource') == 'user' else None
        document, owners, _ = coauthor.apply_delta(document, owners,
            {'ops': ops}, insertion_owner=origin)
        if pending:
            decision = decisions.get(active, {})
            if decision.get('verified_insertion') and event.get('eventSource') == 'api':
                count = len(document) - len(old)
                if count < 0 or not old:
                    raise ValueError('Invalid accepted-suggestion ownership transform')
                owners = old[:-1] + ['accepted_suggestion'] * count + old[-1:]
            pending = False
    text = coauthor.text_of(document)
    if text != canonical['final_document'] or len(owners) != len(document):
        raise ValueError('Final source replay disagrees with canonical final document')
    points, offset = [], 0
    for ch in text:
        width = len(coauthor.units(ch))
        labels = set(owners[offset:offset+width])
        if len(labels) != 1:
            raise ValueError('Surrogate code units have different provenance')
        points.append(labels.pop())
        offset += width
    return text, points


def session_projection(session, writer, fold, events, production, posteriors, qualified_locations=None):
    if not isinstance(session, str) or not session or not re.fullmatch('[0-9a-f]{64}', writer):
        raise ValueError('Canonical session and already hashed writer required')
    if type(fold) is not int or not 0 <= fold < 5:
        raise ValueError('Five-fold writer assignment required')
    raw, labels = final_sources(events)
    text, origins = normalize_with_origins(raw)
    production = [word for word in production if word['is_word']]
    if qualified_locations is None:
        locations = scoring.context_rows(events, production)
    else:
        by_index = {row['index']:row for row in qualified_locations}
        if len(by_index)!=len(qualified_locations) or set(by_index)!={word['index'] for word in production}:
            raise ValueError('Qualified AT locations do not cover exact P6 word occurrences')
        locations = [by_index[word['index']] for word in production]
    if len(locations) != len(production):
        raise ValueError('Incomplete exact production occurrence mapping')
    posterior = {row['ordinal']: row for row in posteriors}
    if len(posterior) != len(posteriors):
        raise ValueError('Duplicate preceding-interval timing identity')
    surviving = {}
    for word, location in zip(production, locations):
        if not word['is_word'] or not location['final_supported']:
            continue
        start = len(location['final_prefix'])
        stop = start + len(location['target'])
        if raw[start:stop] != location['target']:
            raise ValueError('Exact surviving production does not match final location')
        key = frozenset(range(start, stop))
        if key in surviving:
            raise ValueError('Two production records claim the same final occurrence')
        surviving[key] = word
    rows = []
    for token in TOKEN.finditer(text):
        if not WORD.fullmatch(token.group()):
            continue
        a, b = token.span()
        ancestry = frozenset().union(*origins[a:b])
        constituents = {labels[index] for index in ancestry}
        mixed = len(constituents) > 1
        origin = next(iter(constituents)) if len(constituents) == 1 else None
        counts = Counter()
        for points in origins[a:b]:
            counts.update(set(labels[index] if labels[index] is not None else 'unresolved'
                              for index in points))
        row = dict(start=a, end=b, source=origin, mixed_provenance=mixed,
            unresolved_provenance=None in constituents,
            constituent_sources=sorted(c for c in constituents if c is not None),
            source_codepoint_counts=dict(sorted(counts.items())),
            stop=None, log_pause=None, timing_status='not_wholly_typed')
        if origin == 'typed':
            word = surviving.get(ancestry)
            post = posterior.get(word['ordinal']) if word else None
            pause = word.get('pause_seconds') if word else None
            supported = bool(word and post and post.get('onset') and
                             word.get('first_delta_characters') == 1 and
                             isinstance(pause, (int, float)) and math.isfinite(pause) and pause > 0)
            if supported:
                fast = post['fast']
                if not isinstance(fast, (int, float)) or not math.isfinite(fast) or not 0 <= fast <= 1:
                    raise ValueError('Invalid frozen fluent posterior')
                if not math.isclose(pause, post['interval_seconds'], rel_tol=0, abs_tol=1e-6):
                    raise ValueError('Production pause differs from preceding ruler interval')
                row.update(stop=fast < .5, log_pause=math.log(pause), timing_status='supported')
            else:
                row['timing_status'] = ('no_exact_surviving_production' if word is None
                                        else 'unsupported_preceding_interval')
        rows.append(row)
    result = dict(schema=VERSION, session_id=session, hashed_writer_id=writer,
        writer_fold=fold, normalized_text_sha256=hashlib.sha256(text.encode('utf8')).hexdigest(),
        normalized_codepoints=len(text), words=rows)
    validate_projection(result)
    return result


def validate_projection(value):
    keys = {'schema','session_id','hashed_writer_id','writer_fold','normalized_text_sha256',
            'normalized_codepoints','words'}
    word_keys = {'start','end','source','mixed_provenance','unresolved_provenance',
                 'constituent_sources','source_codepoint_counts','stop','log_pause','timing_status'}
    if set(value) != keys or value['schema'] != VERSION:
        raise ValueError('Export schema permits no text or arbitrary fields')
    if not re.fullmatch('[0-9a-f]{64}', value['hashed_writer_id']):
        raise ValueError('Writer export is not a hash')
    if not re.fullmatch('[0-9a-f]{64}', value['normalized_text_sha256']):
        raise ValueError('Final text hash malformed')
    if (not isinstance(value['session_id'], str) or not value['session_id'] or
        type(value['writer_fold']) is not int or not 0 <= value['writer_fold'] < 5 or
        type(value['normalized_codepoints']) is not int or value['normalized_codepoints'] < 0):
        raise ValueError('Session/fold/code-point metadata malformed')
    previous = 0
    for word in value['words']:
        if set(word) != word_keys or word['source'] not in (*LABELS, None):
            raise ValueError('Unexpected exported word field or source')
        if (type(word['start']) is not int or type(word['end']) is not int or
            type(word['mixed_provenance']) is not bool or type(word['unresolved_provenance']) is not bool or
            word['timing_status'] not in ('supported','not_wholly_typed',
                'no_exact_surviving_production','unsupported_preceding_interval')):
            raise ValueError('Word quality field has invalid type or value')
        if not 0 <= previous <= word['start'] < word['end'] <= value['normalized_codepoints']:
            raise ValueError('Exported word offsets are out of order or range')
        previous = word['end']
        if word['stop'] is not None and (type(word['stop']) is not bool or word['source'] != 'typed'):
            raise ValueError('Stop label requires a wholly typed word')
        if word['log_pause'] is not None and not math.isfinite(word['log_pause']):
            raise ValueError('Exported log pause is nonfinite')
        if (word['stop'] is None) != (word['log_pause'] is None):
            raise ValueError('Partially present timing label')
        if set(word['constituent_sources']) - set(LABELS):
            raise ValueError('Unrecognized constituent source')
        if set(word['source_codepoint_counts']) - {*LABELS, 'unresolved'}:
            raise ValueError('Unrecognized source count key')
        if any(type(n) is not int or n <= 0 for n in word['source_codepoint_counts'].values()):
            raise ValueError('Invalid constituent code-point count')
        if (word['timing_status']=='supported') != (word['stop'] is not None):
            raise ValueError('Timing quality and label availability disagree')
    return True


def upstream(inputs):
    if set(inputs) != {'at_root'}:
        raise ValueError('Exactly one complete canonical AT source required')
    root = source.authenticate(inputs['at_root'])
    plan = read(root/'PLAN.json')
    if plan.get('module') != 'runners.drive.cards.week5_at_source' or plan.get('config') != {}:
        raise ValueError('AT source producer or scope changed')
    bound = plan['inputs']
    p6, index, roster, posteriors, timing_roster = source.load_sources(bound)
    summary = read(root/'output/SUMMARY.json')
    pins = {key:io.sha(Path(value)/'COMPLETE.json') if key in ('p6_root','timing_root')
            else io.sha(value) for key,value in bound.items() if key != 'repo_root'}
    if summary['source_pins'] != pins or summary['sessions'] != len(index):
        raise ValueError('Completed AT source no longer binds the exact parents')
    hashes = {'at_complete':io.sha(root/'COMPLETE.json'), 'at_plan':io.sha(root/'PLAN.json'), **pins}
    at_index=read(root/'output/INDEX.json')
    if len(at_index)!=len(index):raise ValueError('Qualified AT index population differs')
    return bound, p6, index, roster, posteriors, timing_roster, hashes, root, at_index


def run(output, inputs, config, verifying=False):
    if set(config) - {'max_new_documents','max_wall_seconds'}:
        raise ValueError('Only operational session quantum and wall limit are configurable')
    limit = config.get('max_new_documents', 1399)
    wall = config.get('max_wall_seconds', 1800)
    if type(limit) is not int or limit <= 0 or not isinstance(wall,(int,float)) or not math.isfinite(wall) or wall <= 0:
        raise ValueError('Invalid operational limit')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    bound,p6,index,roster,posteriors,timing_roster,pins,at_root,at_index = upstream(inputs)
    ordered = sorted(index, key=lambda row:row['session'])
    writers = [timing_roster[row['session']]['writer'] for row in ordered]
    folds = analysis.folds(writers, 5).tolist()
    binding = dict(schema=VERSION, source_pins=pins, module_sha256=io.sha(__file__),
                   fold_seed=scoring.SEED, sessions=len(ordered), normalization='NFC(CRLF/CR_to_LF(text).rstrip())')
    bind_path = output/'BINDING.json'
    if bind_path.exists() and read(bind_path) != binding:
        raise ValueError('EX1 source or semantic binding changed')
    if not bind_path.exists():
        if verifying: raise ValueError('Verification lacks production binding')
        io.write_json(bind_path,binding)
    state_path = output/('VERIFY_CHECKPOINT.json' if verifying else 'CHECKPOINT.json')
    state = read(state_path) if state_path.exists() else dict(binding=binding,completed=0,files={})
    if state['binding'] != binding or not 0 <= state['completed'] <= len(ordered):
        raise ValueError('EX1 checkpoint binding/count differs')
    if set(state['files']) != {f'bundle/sessions/session-{i:04d}.json' for i in range(state['completed'])}:
        raise ValueError('EX1 checkpoint must bind every contiguous completed session')
    for name,sha in state['files'].items():
        path=output/name; path.resolve().relative_to(output.resolve())
        if io.sha(path) != sha: raise ValueError('Sealed EX1 session changed')
    start=time.monotonic(); done=0
    for position in range(state['completed'],len(ordered)):
        meta=ordered[position]; sid=meta['session']; record_path=p6/'output'/meta['file']
        if io.sha(record_path)!=meta['sha256']:raise ValueError('P6 production session changed')
        record=source.gzread(record_path); rawmeta=roster[sid]
        rawpath=(Path(bound['repo_root'])/rawmeta['path']).resolve()
        rawpath.relative_to(Path(bound['repo_root']).resolve())
        if io.sha(rawpath)!=rawmeta['source_sha256']:raise ValueError('Raw session source changed')
        if record['session']!=sid or record['writer']!=writers[position]:
            raise ValueError('Timing and production writer/session differ')
        at_meta=at_index[position];at_path=at_root/'output'/at_meta['file']
        at_path.resolve().relative_to((at_root/'output').resolve())
        if io.sha(at_path)!=at_meta['sha256']:raise ValueError('Qualified AT session changed')
        qualified=source.gzread(at_path)
        expected_binding=scoring.digest({k:v for k,v in pins.items() if k not in ('at_complete','at_plan')})
        if qualified['binding']!=expected_binding or len(qualified['rows'])!=at_meta['words']:
            raise ValueError('Qualified AT session binding/count differs')
        if any(row['session']!=sid or row['writer']!=record['writer'] for row in qualified['rows']):
            raise ValueError('Qualified AT session identity differs')
        events=[json.loads(line) for line in rawpath.read_text(encoding='utf8').splitlines() if line]
        value=session_projection(sid,record['writer'],folds[position],events,record['words'],posteriors[sid],qualified['rows'])
        name=f'bundle/sessions/session-{position:04d}.json';path=output/name
        if path.exists():
            if read(path)!=value:raise ValueError('Fresh EX1 projection differs')
        elif verifying:raise ValueError('EX1 production session is missing')
        else:io.write_json(path,value)
        state['files'][name]=io.sha(path);state['completed']=position+1;done+=1
        io.write_json(state_path,state)
        io.write_json(output/'PROGRESS.json',dict(phase='verify' if verifying else 'execute',
            completed=state['completed'],total=len(ordered)))
        if state['completed']<len(ordered) and (done>=limit or time.monotonic()-start>=wall or
                (output/'YIELD_REQUEST.json').exists()):
            return dict(status='yielded',verified=False,completed=state['completed'],total=len(ordered))
    counts=Counter({key:0 for key in ('words','source_typed','source_accepted_suggestion',
        'source_prompt','source_None','mixed_provenance','unresolved_provenance',
        'timing_supported','timing_not_wholly_typed','timing_no_exact_surviving_production',
        'timing_unsupported_preceding_interval')});files={}
    for position in range(len(ordered)):
        name=f'bundle/sessions/session-{position:04d}.json';value=read(output/name)
        validate_projection(value);files[name.removeprefix('bundle/')]=io.sha(output/name)
        for row in value['words']:
            counts['words']+=1;counts['source_'+str(row['source'])]+=1
            counts['mixed_provenance']+=int(row['mixed_provenance'])
            counts['unresolved_provenance']+=int(row['unresolved_provenance'])
            counts['timing_'+row['timing_status']]+=1
    summary=dict(schema=VERSION,card='EX1',record_kind='run',by_construction=False,theory_tags=[],
        sessions=len(ordered),writers=len(set(writers)),counts=dict(sorted(counts.items())),
        source_pins=pins,files=files,scientific_effect=False,text_exported=False)
    markdown=readme(summary)
    for name,value in (('bundle/MANIFEST.json',summary),):
        if verifying:
            if read(output/name)!=value:raise ValueError('EX1 aggregate replay differs')
        else:io.write_json(output/name,value)
    dest=output/'bundle/README.md'
    if verifying:
        if dest.read_text(encoding='utf8')!=markdown:raise ValueError('EX1 README replay differs')
    elif dest.exists():
        if dest.read_text(encoding='utf8')!=markdown:raise ValueError('EX1 README already differs')
    else:dest.write_text(markdown,encoding='utf8',newline='\n')
    return dict(verified=True,full_source_replay=True,text_exported=False) if verifying else summary


def readme(summary):
    return ('# EX1: CoAuthor final-word stop and source labels\n\n'
        'No text is included. Offsets are zero-based half-open Unicode code points. '
        'Replay the canonical local session, replace CRLF and CR with LF, strip trailing '
        'whitespace from the whole document (not each line), then NFC-normalize and '
        'check the UTF-8 SHA-256. Words use the existing P6 TOKEN/WORD rule after normalization.\n\n'
        'Writer hashes and session identifiers are the original canonical private pipeline '
        'identifiers; five writer-disjoint folds use sorted writer hashes, NumPy seed 20261107 '
        'permutation and round-robin assignment. No writer is split across folds.\n\n'
        'Sources are typed, accepted_suggestion (verified offered insertion), or prompt. '
        'A mixed or unresolved source stays null, with quality flags and constituent '
        'code-point counts. Composition can give a single normalized code point multiple '
        'constituents, so their counts can exceed word length. All words remain.\n\n'
        'Only exact surviving wholly typed production occurrences with supported preceding '
        'Week 4 timing intervals receive stop = fluent posterior < 0.5 and natural log of '
        'the original positive delta interval in seconds. Unsupported timing stays null. '
        'These labels do not identify psychological states.\n\n'
        'Licence/permission: author-released CoAuthor data for private research; the code MIT '
        'licence is not imputed to the data. This particular local text-free transfer is '
        'authorized by the November 11 back-half packet, amendment T. No public redistribution '
        'or provider transfer is licensed here. Cite CoAuthor and retain its local source notice.\n\n'
        'Evidence records: '+', '.join(LEDGER)+'. Exact source completion hashes are in MANIFEST.json.\n\n'
        'Counts (complete final texts only):\n\n'+json.dumps({key:summary[key] for key in
        ('sessions','writers','counts')},indent=2)+'\n')


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


def export_local(run_root,destination):
    """Owner-only post-completion materialization; never copy outside this repo."""
    repo=Path(__file__).resolve().parents[3]
    allowed=repo/'corpora/store/exports/engine_bench_20261111/EX1'
    destination=Path(destination).resolve()
    if destination!=allowed.resolve() or destination.exists():
        raise ValueError('Only a new named local ignored EX1 destination is allowed')
    root=source.authenticate(run_root);plan=read(root/'PLAN.json')
    if plan.get('module')!=MODULE or read(root/'output/BINDING.json')['module_sha256']!=io.sha(__file__):
        raise ValueError('Completed export producer differs')
    bundle=root/'output/bundle';manifest=read(bundle/'MANIFEST.json')
    expected=set(manifest['files'])|{'MANIFEST.json','README.md'}
    actual={p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    if actual!=expected:raise ValueError('Export bundle contains unexpected files')
    for name,sha in manifest['files'].items():
        path=bundle/name;path.resolve().relative_to(bundle.resolve())
        if path.is_symlink() or io.sha(path)!=sha:raise ValueError('Export session differs')
        validate_projection(read(path))
    destination.mkdir(parents=True)
    for name in sorted(expected):
        source_path=bundle/name;target=destination/name
        if source_path.is_symlink():raise ValueError('Export symlink refused')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source_path,target)
        if io.sha(source_path)!=io.sha(target):raise ValueError('Local copy hash mismatch')
    return dict(destination_relative=destination.relative_to(repo).as_posix(),
        files={name:io.sha(destination/name) for name in sorted(expected)},text_exported=False)
