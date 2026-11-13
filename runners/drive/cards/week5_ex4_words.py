"""EX4 surviving typed-word provenance over the original exact KLiCKe replay.

DESIGN CHECK: UTF-16 edit coordinates are not Unicode code-point offsets.
Moves preserve origins; removed word starts cannot acquire an invented pause.
All unsupported timing is nullable and counted, never relabelled fluent.
"""
from collections import Counter
import hashlib
import math
import os
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
from runners.stage9.coauthor import units, text_of
from . import week5_bk_s4k_navigation as original
from .timing_text import TOKEN, WORD


def word_start(prefix, character):
    if not WORD.fullmatch(character):
        return False
    if not prefix:
        return True
    previous = prefix[-1]
    if WORD.fullmatch(previous):
        return False
    if previous in ("'", '\u2019') and len(prefix) > 1 and WORD.fullmatch(prefix[-2]):
        return False
    return True


def replay(record):
    doc, owners, origins = [], [], []
    previous_up = None
    census = Counter()
    for event in record['events']:
        census['events'] += 1
        new, _ = original.operation(doc, event)
        activity = event['Activity']; ordinal = int(event['ordinal'])
        stamp = float(event['DownTime']) / 1000
        up = float(event['UpTime']) / 1000
        logged_pause = float(event['PauseTime']) / 1000
        if not all(math.isfinite(x) for x in (stamp, up, logged_pause)) or up < stamp:
            raise ValueError('Invalid source event clock')
        computed_pause = (float(event['DownTime']) - previous_up) / 1000 if previous_up is not None else None
        pause = computed_pause if (computed_pause is not None and computed_pause >= 0
                   and logged_pause >= 0 and math.isclose(logged_pause, computed_pause, rel_tol=0, abs_tol=.001)) else None
        if activity != 'Nonproduction':
            change = original.logged_text(event['TextChange']); cursor = int(event['CursorPosition'])
            if activity in ('Input', 'Paste'):
                insert = change; removed = 0; start = cursor - len(units(insert))
            elif activity == 'Remove/Cut':
                insert = ''; removed = len(units(change)); start = cursor
            elif activity == 'Replace':
                before, insert = change.split(' => '); removed = len(units(before)); start = cursor - len(units(insert))
            else:
                match = original.MOVE.fullmatch(activity)
                if not match:
                    raise ValueError('Unrecognized provenance operation')
                a, b, c, d = map(int, match.groups())
                moved = owners[a:b]
                remaining = owners[:a] + owners[b:]
                owners = remaining[:c] + moved + remaining[c:]
                if a != c:
                    for identity in set(moved):
                        origins[identity]['moved'] = True
                doc = new; previous_up = float(event['UpTime']); census['moves'] += 1
                if len(owners) != len(doc):
                    raise ValueError('Move provenance extent differs')
                continue
            added = []
            prefix = text_of(doc[:start])
            for offset, character in enumerate(insert):
                identity = len(origins)
                origins.append({'ordinal': ordinal, 'character_offset': offset, 'source': activity,
                    'pause': pause, 'starts_word': word_start(prefix, character),
                    'bulk': len(insert) != 1, 'inserted_later': start < len(doc), 'moved': False})
                added.extend([identity] * len(units(character))); prefix += character
            owners = owners[:start] + added + owners[start + removed:]
        if len(owners) != len(new):
            raise ValueError('Text/provenance extent differs')
        doc = new; previous_up = float(event['UpTime'])
    final = text_of(doc)
    if final != original.canonical_final(record['final_text']):
        raise ValueError('Independent final text mismatch')
    codepoint_owners = []; at = 0
    for character in final:
        width = len(units(character)); held = owners[at:at + width]
        if len(held) != width or len(set(held)) != 1:
            raise ValueError('A Unicode code point has contradictory origins')
        codepoint_owners.append(held[0]); at += width
    words = []
    for match in TOKEN.finditer(final):
        if not WORD.fullmatch(match.group()):
            continue
        census['final_words'] += 1
        ids = codepoint_owners[match.start():match.end()]
        characters = [origins[i] for i in ids]
        typed = [r for r in characters if r['source'] == 'Input']
        if not typed:
            census['words_without_typed_material'] += 1
            continue
        first = characters[0]
        reason = 'supported'
        if any(r['source'] != 'Input' for r in characters):
            reason = 'mixed_noninput_provenance'
        elif any(r['bulk'] for r in characters):
            reason = 'bulk_input_has_no_word_specific_first_keystroke'
        elif not first['starts_word']:
            reason = 'original_word_start_did_not_survive'
        elif first['ordinal'] != min(r['ordinal'] for r in characters):
            reason = 'later_inserted_start_precedes_older_word_material'
        elif any(r['starts_word'] for r in characters[1:]):
            reason = 'multiple_original_word_starts_merged'
        elif first['pause'] is None:
            reason = 'missing_overlapping_or_inconsistent_clock'
        timing = first['pause'] if reason == 'supported' else None
        row = {'start': match.start(), 'end': match.end(),
               'first_typing_event': min(r['ordinal'] for r in typed),
               'pause_seconds': timing, 'stop_2_seconds': None, 'stop_essay_p80': None,
               'inserted_later': any(r['inserted_later'] for r in typed),
               'moved_after_typing': any(r['moved'] for r in characters), 'timing_status': reason}
        words.append(row); census['typed_final_words'] += 1; census['timing_' + reason] += 1
    words.sort(key=lambda r: (r['first_typing_event'], r['start'], r['end']))
    pauses = [r['pause_seconds'] for r in words if r['pause_seconds'] is not None]
    threshold = float(np.quantile(pauses, .8, method='linear')) if pauses else None
    for row in words:
        if row['pause_seconds'] is not None:
            row['stop_2_seconds'] = row['pause_seconds'] >= 2.
            row['stop_essay_p80'] = row['pause_seconds'] >= threshold
    return {'session': record['session'], 'final_text': final,
            'final_text_sha256': hashlib.sha256(final.encode('utf8')).hexdigest(),
            'words': words, 'essay_pause_p80_seconds': threshold, 'counts': dict(census),
            'word_scope': 'final surviving words containing typed Input material; unsupported timing explicit',
            'offset_units': 'Unicode code points in exact replayed final text', 'writer_id_included': False}
