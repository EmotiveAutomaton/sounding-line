"""Authenticated PMAP session features and the shared corpus style dictionary.

DESIGN CHECK: LESSONS 3-5, October 18. Source disagreement refuses a unit;
missing timing is missing, never a zero/key press. Known raw insert/delete
fixtures distinguish original accepted characters from new user additions.
Canonical actual option identities, not the logged selected index, choose vectors.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import unicodedata

import numpy as np

from .timing_census import read, filehash
from .timing_p6 import gzread
from .timing_text import TOKEN, WORD
from runners.stage9.coauthor import units, text_of, delta_ops
from runners.stage9.common import digest

INPUTS = frozenset(('repo_root', 'foundation_complete', 'foundation_plan', 'session_index',
    'prepared_sessions', 'raw_roster', 'source_pins', 'p6_index', 'p6_completion',
    'p5_index', 'p5_completion', 'tc_primary', 'tc_completion', 'content_complete',
    'selection_audit_complete'))
ACTIONS = ('accept', 'edit', 'dismiss', 'ignore')


def completed(complete, path, fresh=True):
    complete, path = Path(complete).resolve(), Path(path).resolve()
    c = read(complete)
    if c.get('status') != 'COMPLETE' or fresh and not c.get('fresh_process_verified'):
        raise ValueError('dependency not verified complete')
    if c['outputs'].get(path.relative_to(complete.parent).as_posix()) != filehash(path):
        raise ValueError('completed dependency changed')
    return c


def indexed(path):
    rows = read(path)
    result = {r['session']: r for r in rows}
    if not rows or len(result) != len(rows):
        raise ValueError('empty or duplicate session index')
    return result


def bound_record(index_path, row):
    root = Path(index_path).resolve().parent
    path = (root / row['file']).resolve(); path.relative_to(root)
    if filehash(path) != row['sha256']:
        raise ValueError('source unit hash changed')
    return gzread(path) if path.suffix == '.gz' else read(path)


def dictionary(rows):
    """Transductive feature roster: all completed produced typed occurrences.

    Includes later-deleted words. Unicode casefold; ties sort by codepoint.
    Punctuation is Unicode category P; symbols are not silently punctuation.
    Relative-frequency denominator is all produced word and punctuation tokens.
    """
    words, punctuation, bigrams = Counter(), Counter(), Counter()
    for r in rows:
        words.update(r['word_counts']); punctuation.update(r['punctuation_counts'])
        bigrams.update(r['bigram_counts'])
    chosen = sorted(words, key=lambda t: (-words[t], t))[:100]
    pairs = sorted(bigrams, key=lambda t: (-bigrams[t], t))[:20]
    return dict(words=chosen, punctuation=sorted(punctuation), character_bigrams=pairs,
        word_counts={k: words[k] for k in chosen}, punctuation_counts=dict(sorted(punctuation.items())),
        bigram_counts={k: bigrams[k] for k in pairs}, word_types=len(words),
        typed_words=sum(words.values()), punctuation_tokens=sum(punctuation.values()),
        population='completed produced typed occurrences, including later-deleted; P6 source replay',
        normalization='Unicode casefold; P6 word regex; punctuation Unicode category P',
        bigram_population='adjacent typed codepoint atoms at insertion, including whitespace/punctuation; each atom pair once',
        timing='single-codepoint user delta pairs at distinct ordinals only; logged intervals, not keypresses')


def raw_features(events, timeline, canonical):
    """Original-character deletion share and adjacent typed-atom bigram timing.

    Noncanonical API insertions remain non-typed provenance. Only canonical
    usable accept/edit origins contribute to the accepted denominator. All raw
    transforms, including terminal-newline relocation, must reconstruct P2.
    """
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('initialization required')
    clock = [float(e['eventTimestamp']) / 1000 for e in events]
    if not all(map(math.isfinite, clock)) or clock != sorted(clock):
        raise ValueError('invalid raw chronology')
    accepted = {r['ordinal']: r for r in canonical['events']
                if r['usable'] and r['decision'] in ('accept', 'edit')}
    doc = units(events[0]['currentDoc']); atoms = []; owners = []
    original, deleted, seen_pairs = set(), set(), set()
    bigram_counts, intervals = Counter(), defaultdict(list)
    current = pending = None
    inside_additions = excluded_api_characters = 0

    def mint(text, source, ordinal, single):
        result = []
        for char in text:
            idx = len(atoms)
            atoms.append((char, source, ordinal, single))
            result.extend([idx] * len(units(char)))
            if source == 'accepted': original.add(idx)
        return result

    owners = mint(events[0]['currentDoc'], 'prompt', 0, False)
    for ordinal, e in enumerate(events):
        if e['eventName'] == 'suggestion-open': current = ordinal
        if e['eventName'] == 'suggestion-select': pending = current
        ops = delta_ops(e.get('textDelta'))
        if not ops: continue
        user = e.get('eventSource') == 'user'
        text = ''.join(o['insert'] for o in ops if 'insert' in o)
        source = 'typed' if user else 'accepted' if pending in accepted else 'api_excluded'
        single = user and len(text) == 1
        before, prior = text_of(doc), owners
        out, labels, newids, chunks, position = [], [], [], [], 0
        for op in ops:
            if 'insert' in op:
                ids = mint(op['insert'], source, ordinal, single)
                if user and 0 < position < len(prior) and prior[position-1] in original and prior[position] in original:
                    inside_additions += len(op['insert'])
                chunks.append((len(labels),len(labels)+len(ids)))
                out.extend(units(op['insert'])); labels.extend(ids); newids.extend(ids)
            else:
                count = op.get('retain', op.get('delete'))
                if type(count) is not int or count < 0 or position + count > len(doc):
                    raise ValueError('invalid UTF16 delta')
                if 'retain' in op:
                    out.extend(doc[position:position+count]); labels.extend(prior[position:position+count])
                elif user:
                    deleted.update(a for a in prior[position:position+count] if a in original)
                position += count
        out.extend(doc[position:]); labels.extend(prior[position:]); doc, owners = out, labels
        after = text_of(doc)
        if not user and pending is not None:
            if not before.endswith('\n') or not after.startswith(before[:-1]) or not after.endswith('\n') or len(doc)-len(prior) != len(newids):
                raise ValueError('API insertion is not exact canonical append')
            actual = after[len(before)-1:-1]
            if pending in accepted:
                c = accepted[pending]
                choices = [o for o in c['options'] if o['index'] in c['matched_option_indices']]
                if not c['verified_insertion'] or not choices or any(o['original'].replace('\r\n','\n').replace('\r','\n') != actual for o in choices):
                    raise ValueError('accepted raw insertion differs from verified canonical identity')
            else: excluded_api_characters += len(actual)
            owners = prior[:-1] + newids + prior[-1:]; pending = None
        if user and newids:
            # Only new adjacency at this insertion, never a pair manufactured by deletion.
            fresh = set(newids)
            adjacent = set()
            for start,stop in chunks:
                ids = list(dict.fromkeys(owners[max(0,start-2):min(len(owners),stop+2)]))
                adjacent.update(zip(ids,ids[1:]))
            for a, b in sorted(adjacent):
                if (a in fresh or b in fresh) and atoms[a][1] == atoms[b][1] == 'typed' and (a,b) not in seen_pairs:
                    seen_pairs.add((a,b)); ca, _, oa, sa = atoms[a]; cb, _, ob, sb = atoms[b]
                    pair = ca.casefold() + cb.casefold()
                    if len(ca.casefold()) != 1 or len(cb.casefold()) != 1: continue
                    bigram_counts[pair] += 1
                    if sa and sb and oa < ob:
                        dt = clock[ob] - clock[oa]
                        if dt >= 0: intervals[pair].append(dt)
    if text_of(doc) != timeline['final_document']:
        raise ValueError('raw reconstruction differs from P2')
    return dict(bigram_counts=dict(sorted(bigram_counts.items())),
        bigram_intervals={k:v for k,v in sorted(intervals.items())}, accepted_characters=len(original),
        edited_accepted_characters=len(deleted), internal_added_characters=inside_additions,
        excluded_api_characters=excluded_api_characters)


class Sources:
    def __init__(self, inputs):
        if set(inputs) != INPUTS: raise ValueError('exact PMAP inputs required')
        self.inputs = inputs; self.root = Path(inputs['repo_root']).resolve()
        plan = read(inputs['foundation_plan']); c = read(inputs['foundation_complete'])
        if c.get('status') != 'COMPLETE' or c.get('plan_sha256') != filehash(inputs['foundation_plan']):
            raise ValueError('foundation plan unauthenticated')
        for name in ('prepared_sessions','raw_roster','source_pins'):
            p = Path(inputs[name]).resolve()
            if plan['pins'].get(p.relative_to(self.root).as_posix()) != filehash(p):
                raise ValueError('foundation source metadata changed')
        for index, complete in (('session_index','foundation_complete'),('p6_index','p6_completion'),
                               ('p5_index','p5_completion'),('tc_primary','tc_completion')):
            completed(inputs[complete], inputs[index], fresh=index != 'session_index')
        self.tc = read(inputs['tc_primary'])
        self.p2, self.p5, self.p6 = (indexed(inputs[k]) for k in ('session_index','p5_index','p6_index'))
        self.meta, self.roster = (indexed(inputs[k]) for k in ('prepared_sessions','raw_roster'))
        if not (self.p2.keys() == self.p5.keys() == self.p6.keys() == self.meta.keys() == self.roster.keys()):
            raise ValueError('source session populations differ')
        self.pins = {Path(k).as_posix():v for k,v in read(inputs['source_pins']).items()}
        content = Path(inputs['content_complete']).parent
        for name in ('RECORDS.json','VECTORS.npy','PLAN.json'):
            completed(inputs['content_complete'], content/name, fresh=False)
        cp = read(content/'PLAN.json')
        if cp['pins'].get(Path(inputs['prepared_sessions']).resolve().relative_to(self.root).as_posix()) != filehash(inputs['prepared_sessions']):
            raise ValueError('content/prepared population differs')
        records = read(content/'RECORDS.json'); self.content = {r['key']:r for r in records}
        if len(self.content) != len(records): raise ValueError('duplicate content key')
        self.vectors = np.load(content/'VECTORS.npy', mmap_mode='r', allow_pickle=False)
        if self.vectors.ndim != 2 or self.vectors.shape[1] != 384 or not np.isfinite(self.vectors).all():
            raise ValueError('invalid MiniLM vectors')
        audit = Path(inputs['selection_audit_complete']).parent
        completed(inputs['selection_audit_complete'], audit/'ROWS.json', fresh=False)
        ar = read(audit/'ROWS.json'); self.audit = {r['key']:r for r in ar}
        if len(self.audit) != len(ar) or self.audit.keys() != self.content.keys():
            raise ValueError('canonical/content menu populations differ')

    def unit_binding(self, sid):
        """Authenticate every byte feeding a reusable complete session checkpoint."""
        meta=self.roster[sid]; raw=(self.root/meta['path']).resolve(); raw.relative_to(self.root)
        canonical=self.root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
        result={}
        for name,expected in (('raw',meta['source_sha256']),('canonical',self.pins.get(canonical.relative_to(self.root).as_posix()))):
            path=raw if name=='raw' else canonical
            if expected is None or filehash(path)!=expected:raise ValueError('reused source bytes changed')
            result[name]=expected
        for name,index in (('p2','session_index'),('p5','p5_index'),('p6','p6_index')):
            row=getattr(self,name)[sid]; path=Path(self.inputs[index]).parent/row['file']
            path.resolve().relative_to(Path(self.inputs[index]).resolve().parent)
            if filehash(path)!=row['sha256']:raise ValueError('reused derived source changed')
            result[name]=row['sha256']
        return result

    def session(self, sid):
        i = self.inputs; row = self.p2[sid]; meta = self.meta[sid]; roster = self.roster[sid]
        timeline = bound_record(i['session_index'], row)
        p5, p6 = bound_record(i['p5_index'],self.p5[sid]), bound_record(i['p6_index'],self.p6[sid])
        identity = (sid,row['writer'],timeline['prompt'])
        for r in (timeline,meta,p5,p6):
            if (r['session'],r['writer'],r['prompt']) != identity: raise ValueError('session identity mismatch')
        if p5['source_sha256'] != timeline['source_sha256'] or p5['p2_sha256'] != row['sha256']:
            raise ValueError('P5 source mismatch')
        if (p6['timestamp'],p6['end_at']) != (meta['timestamp'],meta['end_at']):
            raise ValueError('P6 chronology mismatch')
        raw = (self.root/roster['path']).resolve(); raw.relative_to(self.root)
        if filehash(raw) != timeline['source_sha256'] or self.pins.get(roster['path']) != timeline['source_sha256']:
            raise ValueError('raw source mismatch')
        canonical_path = self.root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
        chash = filehash(canonical_path)
        if self.pins.get(canonical_path.relative_to(self.root).as_posix()) != chash:
            raise ValueError('canonical source unauthenticated')
        canonical = read(canonical_path)
        if not canonical['usable'] or not canonical['reconstructed'] or canonical['errors'] or canonical['final_document'] != timeline['final_document']:
            raise ValueError('canonical replay invalid')
        cr = {r['ordinal']:r for r in canonical['events'] if r['usable']}
        if len(cr) != sum(bool(r['usable']) for r in canonical['events']) or set(cr) != {m['ordinal'] for m in meta['rows']}:
            raise ValueError('canonical decision coverage differs')
        if {r['ordinal']:r['handling'] for r in timeline['decisions']} != {o:r['decision'] for o,r in cr.items()}:
            raise ValueError('canonical handling differs')
        accept, decline = np.zeros(384), np.zeros(384); na = nd = mismatch = 0
        for m in meta['rows']:
            c, a, v = cr[m['ordinal']], self.audit[m['key']], self.content[m['key']]
            if (a['key'],a['session'],a['writer'],a['ordinal'],a['prepared_handling']) != (m['key'],sid,row['writer'],m['ordinal'],m['handling']):
                raise ValueError('selection audit identity differs')
            choices = [j for j,o in enumerate(c['options']) if o['index'] in c['matched_option_indices']] if c['decision'] in ('accept','edit') else []
            if [o['original'] for o in c['options']] != m['menu'] or len(v['options']) != len(m['menu']):
                raise ValueError('canonical/content menu order mismatch')
            if (a['canonical_sha256'],a['canonical_positions'],a['raw_source_sha256'],a['canonical_handling']) != (chash,choices,timeline['source_sha256'],c['decision']):
                raise ValueError('selection audit disagrees with source reconstruction')
            if (v['session'],v['writer']) != (sid,row['writer']): raise ValueError('content identity differs')
            if c['decision'] in ('accept','edit'):
                if not c['verified_insertion'] or len(choices) != 1:
                    raise ValueError('accepted option identity not uniquely verified')
                accept += self.vectors[v['options'][choices[0]]]; na += 1
                mismatch += int(a['index_status'] == 'proven_disjoint_choice')
            if c['decision']=='dismiss':
                if not v['options']:raise ValueError('dismissed menu has no offered vectors')
                decline += np.mean(self.vectors[v['options']],axis=0); nd += 1
        events = [json.loads(line) for line in raw.read_text(encoding='utf8').splitlines()]
        extra = raw_features(events,timeline,canonical)
        words = Counter(w['token'] for w in p6['words'] if w['is_word'])
        punctuation = Counter(w['token'] for w in p6['words'] if not w['is_word'] and all(unicodedata.category(c).startswith('P') for c in w['token']))
        within = [dt for w in p6['words'] if w['is_word'] for dt in w['within_intervals'] if math.isfinite(dt) and dt >= 0]
        onset = [w['pause_seconds'] for w in p6['words'] if w['is_word'] and w['pause_seconds'] is not None and math.isfinite(w['pause_seconds']) and w['pause_seconds'] >= 0]
        return dict(session=sid,writer=row['writer'],prompt=timeline['prompt'],timestamp=meta['timestamp'],
            word_counts=dict(sorted(words.items())),punctuation_counts=dict(sorted(punctuation.items())),
            typed_words=sum(words.values()),within_intervals=within,onset_intervals=onset,
            handling=dict(Counter(d['handling'] for d in timeline['decisions'])),
            revision=dict(Counter(e['split'] for e in p5['edits'])), requests=timeline['event_counts'].get('suggestion-get',0),
            final_words=sum(bool(WORD.fullmatch(m.group())) for m in TOKEN.finditer(timeline['final_document'])),
            accepted_vector_sum=accept.tolist(),declined_vector_sum=decline.tolist(),accepted_options=na,declined_options=nd,
            canonical_choice_disagreements=mismatch,tc_timing_mode=self.tc['timing_mode'],
            source_hashes=dict(raw=timeline['source_sha256'],p2=row['sha256'],p5=self.p5[sid]['sha256'],p6=self.p6[sid]['sha256'],canonical=chash),**extra)
