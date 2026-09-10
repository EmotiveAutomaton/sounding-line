"""CoAuthor task replay with UTF-16 positions and persistent insertion provenance.

DESIGN CHECK: LESSONS sections 2, 3 and 5, especially session-state reconstruction.
NULL: malformed/overflowing deltas, missing selected text, or unjoined sessions
cannot acquire valid handling labels. ALTERNATIVE: exact fixture documents and
accept/edit/dismiss/ignore labels survive Unicode, shifted spans and multi-op edits.
Bands: reconstructed and semantically supported, or retained explicit exclusion.
No independent final document exists: exact fixture equality and internal source
consistency are different checks. Reopen resumes one decision, not another sample.
"""
from collections import Counter
import csv
import io
import json
from pathlib import Path
import time

from runners.stage9.common import REPO, ROOT, closure, digest, file_hash, freeze, read

DECISIONS = ('accept', 'edit', 'dismiss', 'ignore')


def units(text):
    if not isinstance(text, str):
        raise ValueError('non-text document or insertion')
    raw = text.encode('utf-16-le')
    return [int.from_bytes(raw[i:i+2], 'little') for i in range(0, len(raw), 2)]


def text_of(values):
    return b''.join(v.to_bytes(2, 'little') for v in values).decode('utf-16-le')


def delta_ops(value):
    if value in ('', None):
        return []
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict) or set(value) != {'ops'} or not isinstance(value['ops'], list):
        raise ValueError('invalid Quill change delta')
    for op in value['ops']:
        if not isinstance(op, dict) or len(set(op) & {'retain', 'delete', 'insert'}) != 1:
            raise ValueError('delta operation must have one action')
        if set(op) - {'retain', 'delete', 'insert', 'attributes'}:
            raise ValueError('unknown delta operation')
    return value['ops']


def apply_delta(document, provenance, value, *, insertion_owner=None, watched_owner=None):
    """All indexes are UTF-16 code units, as in the released Quill JavaScript.

    Human deletion of any owned character is an edit, including a deletion starting
    before its span. Insertion strictly inside two owned neighbors is an edit;
    appending outside that span is continuation. Earlier unrelated edits shift the
    provenance with the surviving characters. No fuzzy repair of malformed deltas.
    """
    if len(document) != len(provenance):
        raise ValueError('provenance/document disagreement')
    out, owners, position, edited = [], [], 0, False
    for op in delta_ops(value):
        if 'insert' in op:
            new = units(op['insert'])
            if watched_owner is not None and 0 < position < len(document):
                edited |= provenance[position-1] == provenance[position] == watched_owner and bool(new)
            out.extend(new); owners.extend([insertion_owner] * len(new))
        else:
            action = 'retain' if 'retain' in op else 'delete'
            count = op[action]
            if type(count) is not int or count < 0 or position + count > len(document):
                raise ValueError('invalid UTF-16 retain/delete boundary')
            if action == 'retain':
                out.extend(document[position:position+count]); owners.extend(provenance[position:position+count])
            elif watched_owner is not None:
                edited |= watched_owner in provenance[position:position+count]
            position += count
    out.extend(document[position:]); owners.extend(provenance[position:])
    text_of(out)  # An edit cannot silently leave half of a surrogate pair.
    return out, owners, edited


def suggestions(value):
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list) or not 1 <= len(value) <= 20:
        raise ValueError('invalid offered suggestion support')
    out = []
    for option in value:
        if not isinstance(option, dict) or type(option.get('index')) is not int:
            raise ValueError('invalid suggestion index')
        if not isinstance(option.get('original'), str) or not isinstance(option.get('trimmed'), str):
            raise ValueError('missing original/display suggestion text')
        out.append({k: option[k] for k in ('index', 'original', 'trimmed')})
    if len({r['index'] for r in out}) != len(out):
        raise ValueError('repeated suggestion index')
    return out


def replay(lines):
    document, provenance, decisions = [], [], []
    active = None
    pending = False
    initialized = False
    failures, semantics, event_counts = Counter(), Counter(), Counter()
    previous_event_num = None
    n_events = n_deltas = 0

    def finish():
        nonlocal pending
        if active is not None:
            if active['decision'] is None:
                active['decision'] = 'ignore'
            if pending:
                active['exclusion'] = 'selected suggestion lacks a verified insertion'
        pending = False

    for ordinal, raw in enumerate(lines):
        n_events += 1
        try:
            event = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(event, dict):
                raise ValueError('non-object event')
            name = event.get('eventName', '')
            event_counts[name] += 1
            number = event.get('eventNum')
            if number is not None:
                if type(number) is not int or (previous_event_num is not None and number <= previous_event_num):
                    raise ValueError('non-increasing recorded event order')
                previous_event_num = number
            if name == 'system-initialize':
                if initialized:
                    raise ValueError('repeated document initialization')
                document = units(event.get('currentDoc')); provenance = [None] * len(document)
                initialized = True
                continue
            if not initialized:
                raise ValueError('event before document initialization')
        except (ValueError, TypeError, UnicodeError, KeyError) as exc:
            failures[str(exc)] += 1
            continue

        # Suggestion correspondence and document reconstruction are separate
        # measurements. A correspondence failure MUST NOT skip a valid edit.
        try:
            if name == 'suggestion-open':
                finish()
                active = {'ordinal': ordinal, 'document': text_of(document),
                          'options': [], 'decision': None, 'selected_index': None,
                          'matched_option_indices': [], 'logged_index_agrees': None,
                          'exclusion': None, 'reopens': 0, 'verified_insertion': False}
                decisions.append(active)
                active['options'] = suggestions(event.get('currentSuggestions'))
            elif name == 'suggestion-reopen':
                if active is None or active['decision'] not in (None, 'dismiss'):
                    raise ValueError('reopen has no unselected suggestion set')
                if suggestions(event.get('currentSuggestions')) != active['options']:
                    raise ValueError('reopen changes offered alternatives')
                active['decision'] = None; active['reopens'] += 1
            elif name == 'suggestion-select':
                if active is None or active['decision'] is not None:
                    raise ValueError('selection has no active undecided set')
                active['decision'] = 'accept'
                active['selected_index'] = event.get('currentSuggestionIndex')
                pending = True
            elif name == 'suggestion-close':
                if active is not None and active['decision'] is None:
                    active['decision'] = 'dismiss'
        except (ValueError, TypeError, UnicodeError, KeyError) as exc:
            semantics[str(exc)] += 1
            if active is not None:
                active['exclusion'] = str(exc)

        delta = event.get('textDelta')
        if delta not in ('', None):
            n_deltas += 1
            before, previous_provenance = text_of(document), provenance
            watched = (active['ordinal'] if active is not None and active['decision'] == 'accept'
                       and event.get('eventSource') == 'user' else None)
            try:
                document, provenance, edited = apply_delta(document, provenance, delta, watched_owner=watched)
            except (ValueError, TypeError, UnicodeError, KeyError) as exc:
                failures[str(exc)] += 1
                continue
            if pending:
                after = text_of(document)
                matches = [o for o in active['options'] if before.endswith('\n') and after ==
                    before[:-1] + o['original'].replace('\r\n','\n').replace('\r','\n') + '\n']
                if event.get('eventSource') == 'api' and matches:
                    active['verified_insertion'] = True
                    active['matched_option_indices'] = [o['index'] for o in matches]
                    active['logged_index_agrees'] = active['selected_index'] in active['matched_option_indices']
                    # Quill can shift an existing terminal newline across a delta's
                    # insertion span. Tag the full verified document transform.
                    count = len(document) - len(previous_provenance)
                    provenance = previous_provenance[:-1] + [active['ordinal']] * count + previous_provenance[-1:]
                    assert len(provenance) == len(document)
                else:
                    active['exclusion'] = 'selected API insertion does not match an offered full-document transform'
                    semantics[active['exclusion']] += 1
                pending = False
            elif edited:
                active['decision'] = 'edit'
    finish()
    reconstructed = initialized and n_deltas > 0 and not failures
    for row in decisions:
        row['usable'] = reconstructed and row['exclusion'] is None
    return {'events': decisions, 'events_count': n_events, 'event_counts': dict(event_counts),
            'deltas': n_deltas, 'errors': dict(failures), 'semantic_errors': dict(semantics),
            'reconstructed': reconstructed,
            'final_document': text_of(document), 'final_utf16_length': len(document),
            'decision_counts': dict(Counter(r['decision'] for r in decisions))}


def project(row, view, history=()):
    """The current choice and its future handling never enter a reader projection."""
    if view not in ('artifact', 'record'):
        raise ValueError('unknown CoAuthor evidence view')
    evidence = {'document': row['document'], 'suggestions': [s['trimmed'] for s in row['options']]}
    if view == 'record':
        evidence['earlier_handling'] = [r['decision'] for r in history]
        if any(r['ordinal'] >= row['ordinal'] or not r['usable'] for r in history):
            raise ValueError('unobserved, unsupported or future handling in history')
    return evidence


def raw_inputs():
    """Read the complete original log roster and source-bound task metadata."""
    sources = read(ROOT/'intake/COAUTHOR_TASK_SOURCE.json')
    objects = ROOT/'private/intake/objects'
    metadata = {}
    for source, domain in (('metadata', 'creative'), ('argumentative_metadata', 'argumentative')):
        path = objects/sources[source]['sha256']
        if file_hash(path) != sources[source]['sha256']:
            raise ValueError('released task metadata bytes differ from their original intake identity')
        for raw in csv.DictReader(io.StringIO(path.read_text(encoding='utf-8'))):
            key = raw['session_id']
            if key in metadata:
                raise ValueError('duplicate released session metadata')
            metadata[key] = {'writer': digest({'coauthor-writer': raw['worker_id']}),
                'prompt': digest({'coauthor-prompt': raw['prompt_code']}), 'domain': domain,
                'source_event_count': int(raw['num_event']), 'source_selected_count': int(raw['num_selected']),
                'source_query_count': int(raw['num_query'])}
    paths = sorted((REPO/'corpora/coauthor/coauthor-v1.0').glob('*.jsonl'))
    if len(metadata) != 1445 or set(metadata) - {p.stem for p in paths}:
        raise ValueError('published session roster is incomplete')
    identities = {digest({'coauthor-session': p.stem}): file_hash(p) for p in paths}
    identity = {'sources': closure([Path(__file__).resolve(), REPO/'runners/stage9/common.py']),
        'source_files': identities, 'metadata_sources': {k:sources[k] for k in ('metadata','argumentative_metadata')},
        'interface_revision': sources['revision']['sha'],
        'permission': 'author-released research dataset, private analysis only; code MIT not imputed to dataset',
        'reserve': 'none: corpus previously exposed in earlier stages',
        'unit': 'writer crossed with prompt, session decisions remain dependent',
        'handling': 'selected then edited before next new menu; any deletion overlap or strictly internal insertion; reopen resumes same decision',
        'query_count_definition': 'metadata query count equals displayed suggestion-open opportunities, not raw request attempts',
        'selection_correspondence': 'API full-document append of an actually offered original, CR/CRLF normalized; recorded index agreement retained separately; duplicate texts remain equivalent',
        'reconstruction': 'strict UTF-16 change-delta replay, zero bad deltas; no independent final document'}
    return paths, metadata, identity


def reconstruct(paths, metadata):
    """Rebuild all exposed sessions and exclusions without writing or fetching."""
    sessions = {}
    ledger, counts, errors, semantics = [], Counter(), Counter(), Counter()
    for path in paths:
        key = digest({'coauthor-session': path.stem})
        if path.stem not in metadata:
            ledger.append({'key':key,'usable':False,'reason':'local log absent from released task metadata'})
            continue
        with path.open(encoding='utf-8') as stream:
            result = replay(stream)
        meta = metadata[path.stem]
        source_checks = {'event_count': result['events_count'] == meta['source_event_count'],
                         'selection_count': result['event_counts'].get('suggestion-select',0) == meta['source_selected_count'],
                         'query_count': result['event_counts'].get('suggestion-open',0) == meta['source_query_count']}
        usable = result['reconstructed'] and all(source_checks.values())
        for row in result['events']:
            row['usable'] &= usable
            counts['attempted_decisions'] += 1
            if row['usable']:
                counts['usable_decisions'] += 1; counts['decision_'+row['decision']] += 1
        errors.update(result['errors']); semantics.update(result['semantic_errors'])
        counts['verified_selection_index_disagreement'] += sum(r['verified_insertion'] and r['logged_index_agrees'] is False for r in result['events'])
        # Historical data receive development/discovery roles, never new untouched status.
        split = 'development' if int(meta['writer'][:8],16) % 3 == 0 else 'discovery'
        record = {'key':key, **meta, 'split':split, **result, 'source_checks':source_checks, 'usable':usable}
        sessions[key] = record
        ledger.append({'key':key,'writer':meta['writer'],'prompt':meta['prompt'],'domain':meta['domain'],
            'split':split,'usable':usable,'source_checks':source_checks,
            'reason':None if usable else 'strict reconstruction or published per-session counts fail',
            'events':len(result['events']),'usable_decisions':sum(r['usable'] for r in result['events'])})
    summary = {'local_files':len(paths),'published_sessions':len(metadata),
        'extra_local_files':len(paths)-len(metadata),'metadata_writers':len({r['writer'] for r in metadata.values()}),
        'website_writers':63,'writer_count_reproduced':len({r['writer'] for r in metadata.values()})==63,
        'prompts':len({r['prompt'] for r in metadata.values()}),'domains':dict(Counter(r['domain'] for r in metadata.values())),
        'usable_sessions':sum(r['usable'] for r in ledger),'counts':dict(counts),'replay_errors':dict(errors),
        'per_session_source_checks':{k:sum(r.get('source_checks',{}).get(k,False) for r in ledger)
                                     for k in ('event_count','selection_count','query_count')},
        'reserve_groups':0,
        'scientific_launch_accepted':False,'next':'development baseline and scoped H07 reader execution'}
    return sessions, ledger, summary


def prepare():
    started = time.time(); output = ROOT/'private/prepared/coauthor-v2'
    if (output/'COMPLETE.json').exists():
        completed = read(output/'COMPLETE.json')
        freeze(ROOT/'intake/COAUTHOR_PREPARATION_V2.json',completed)
        return completed
    paths, metadata, identity = raw_inputs()
    freeze(output/'IDENTITY.json', identity)
    sessions, ledger, summary = reconstruct(paths, metadata)
    for key, record in sessions.items():
        freeze(output/'sessions'/(key+'.json'),record)
    freeze(output/'LEDGER.json',ledger)
    receipt = {'identity_sha256':digest(identity), **summary,
        'elapsed_seconds':time.time()-started,'completed_at':time.time()}
    freeze(output/'COMPLETE.json',receipt);freeze(ROOT/'intake/COAUTHOR_PREPARATION_V2.json',receipt)
    return receipt


if __name__ == '__main__':
    print(prepare())
