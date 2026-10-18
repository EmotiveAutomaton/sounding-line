"""Outcome-blind supported D33 roster and raw common-screen covariates.

DESIGN CHECK: LESSONS 3-5, October18. No target or future insertion contributes
to its own screen/cache predictor. Raw P6 occurrence identities and complete
support receipts must reconstruct. Missing history is disclosed in a separate
population, never patched into the original full-population question. The raw
transform, not a prepared selected-option index, supplies accepted text.
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path

from .timing_census import read, filehash
from .timing_d33 import cache, cache_probability, WEIGHTS
from .timing_d33_match import earlier, truncate_sequences
from . import timing_d33_pair_intake as intake
from .timing_pmap_source import completed
from .timing_revision_source import Sources as RevisionSources, INPUTS as RAW_INPUTS
from .timing_text import tokens
from runners.stage9.coauthor import units, text_of, apply_delta, suggestions

INPUTS = RAW_INPUTS | intake.INPUTS | {'support_completion', 'supported_decision'}


def visible_sequences(document, origins):
    """Keep prompt boundaries; include all currently visible nonprompt sources."""
    out, current = [], []
    for char, origin in zip(document, origins):
        if origin == 'prompt':
            if current:
                out.extend(tokens(part) for part in text_of(current).splitlines() if tokens(part))
                current = []
        else:
            current.append(char)
    if current:
        out.extend(tokens(part) for part in text_of(current).splitlines() if tokens(part))
    return out


def screen_covariates(events, words):
    if not events or events[0]['eventName'] != 'system-initialize':
        raise ValueError('screen replay requires initialization')
    document = units(events[0]['currentDoc'])
    origins = ['prompt'] * len(document)
    prompt = set(tokens(events[0]['currentDoc']))
    shown = set()
    by_ordinal = defaultdict(list)
    for word in words:
        by_ordinal[word['ordinal']].append(word)
    out = {}
    last_time = -math.inf
    for ordinal, event in enumerate(events):
        stamp = float(event['eventTimestamp'])
        if not math.isfinite(stamp) or stamp < last_time:
            raise ValueError('screen source chronology invalid')
        last_time = stamp
        if ordinal in by_ordinal:
            sequences = visible_sequences(document, origins)
            present = {w for seq in sequences for w in seq}
            counts = cache([dict(end_at=0, training_sequences=sequences)], 1)
            for word in by_ordinal[ordinal]:
                p = word['population_probability']
                if p is None or p <= 0:
                    continue
                token = word['token']
                flags = dict(in_prompt=token in prompt, in_visible_text=token in present,
                             in_previous_shown_suggestion=token in shown)
                out[word['index']] = dict(on_screen=int(any(flags.values())), **flags,
                    session_surprisal=-math.log(cache_probability(word, counts, p)),
                    prior_visible_tokens=counts[-1], first_insertion_ordinal=ordinal)
        # Deliberately AFTER the predictor snapshot, even when a log event both
        # displays alternatives and inserts text. No within-delta time invented.
        if event['eventName'] in ('suggestion-open', 'suggestion-reopen'):
            for option in suggestions(event.get('currentSuggestions')):
                shown.update(tokens(option['trimmed']))
        document, origins, _ = apply_delta(document, origins, event.get('textDelta'),
            insertion_owner='typed' if event.get('eventSource') == 'user' else 'api')
    supported = {w['index'] for w in words if w['population_probability'] is not None and w['population_probability'] > 0}
    if out.keys() != supported:
        raise ValueError('screen occurrence coverage differs')
    return out


def histories(proof, lookup):
    if not proof['supported']:
        raise ValueError('unsupported history cannot be scored')
    own = [lookup[sid] for sid in proof['own_sessions']]
    donor = [dict(lookup[sid], training_sequences=truncate_sequences(lookup[sid]['training_sequences'], n))
             for sid, n in zip(proof['donor_sessions'], proof['trim_allocations'])]
    if len(donor) != len(proof['donor_sessions']):
        raise ValueError('donor history allocation differs')
    return cache(own, proof['before']), cache(donor, proof['before'])


def population_roster(saved, roster, units_by_session, lookup, variant):
    """Select support using only frozen matching receipts, before any fitting."""
    result = dict(variant=variant, writers={}, retained_keys=[], unsupported_keys=[])
    for writer, parts in sorted(roster['writers'].items()):
        kept, missing = {}, {}
        for split in ('calibration', 'evaluation'):
            ids = parts[split + '_sessions']
            kept[split] = [sid for sid in ids if units_by_session[sid]['proof']['supported']]
            missing[split] = [sid for sid in ids if not units_by_session[sid]['proof']['supported']]
        calibration_keys = [[sid, w['index']] for sid in kept['calibration'] for w in lookup[sid]['words']
            if w['is_word'] and w['population_probability'] is not None and w['population_probability'] > 0]
        original_calibration_words = sum(w['is_word'] and w['population_probability'] is not None and w['population_probability'] > 0
            for sid in parts['calibration_sessions'] for w in lookup[sid]['words'])
        own_rows = [r for r in saved['rows'] if r['writer'] == writer]
        keys = [[r['session'], r['index']] for r in own_rows if r['session'] in kept['evaluation']]
        unsupported = [[r['session'], r['index']] for r in own_rows if r['session'] not in kept['evaluation']]
        result['writers'][writer] = dict(supported_sessions=kept, unsupported_sessions=missing,
            calibration_keys=calibration_keys, calibration_words=len(calibration_keys),
            original_calibration_words=original_calibration_words, original_alpha=parts['original_alpha'],
            retained_evaluation_words=len(keys), unsupported_evaluation_words=len(unsupported),
            calibration_available=bool(calibration_keys))
        result['retained_keys'].extend(keys)
        result['unsupported_keys'].extend(unsupported)
    if len(result['retained_keys']) + len(result['unsupported_keys']) != len(saved['rows']):
        raise ValueError('supported roster does not partition original rows')
    result['coverage'] = dict(original_words=len(saved['rows']), retained_words=len(result['retained_keys']),
        unsupported_words=len(result['unsupported_keys']), original_writers=len(result['writers']),
        retained_writers=sum(v['retained_evaluation_words'] > 0 for v in result['writers'].values()),
        wholly_unsupported_writers=sum(v['retained_evaluation_words'] == 0 for v in result['writers'].values()),
        writers_with_any_unsupported_words=sum(v['unsupported_evaluation_words'] > 0 for v in result['writers'].values()),
        retained_sessions={split:sum(len(v['supported_sessions'][split]) for v in result['writers'].values()) for split in ('calibration','evaluation')},
        unsupported_sessions={split:sum(len(v['unsupported_sessions'][split]) for v in result['writers'].values()) for split in ('calibration','evaluation')},
        retained_calibration_words=sum(v['calibration_words'] for v in result['writers'].values()),
        unsupported_calibration_words=sum(v['original_calibration_words']-v['calibration_words'] for v in result['writers'].values()))
    return result


class Sources:
    def __init__(self, inputs):
        if set(inputs) != INPUTS:
            raise ValueError('exact supported D33 source inputs required')
        self.inputs = inputs
        decision = read(inputs['supported_decision'])
        if decision.get('authority') != 'Curator reply: Build the supported match variant.':
            raise ValueError('supported population decision differs')
        root = Path(inputs['support_completion']).resolve().parent
        completed(inputs['support_completion'], root/'PLAN.json')
        plan = read(root/'PLAN.json')
        if plan['module'] != 'runners.drive.cards.timing_d33_pair_intake' or plan['config'] != intake.CONFIG:
            raise ValueError('support census plan differs')
        original_inputs = {k:inputs[k] for k in intake.INPUTS}
        if plan['inputs'] != original_inputs:
            raise ValueError('support census used different sources')
        self.saved, self.roster, self.by_writer, self.lookup, targets = intake.load(original_inputs, intake.CONFIG)
        completed(inputs['support_completion'], root/'output/PRIMARY_ROSTER.json')
        if read(root/'output/PRIMARY_ROSTER.json') != self.roster:
            raise ValueError('support census original roster differs')
        self.units = {v:{} for v in intake.CONFIG['variants']}
        for target in targets:
            for variant in intake.CONFIG['variants']:
                path = root/'output/sessions'/variant/(target['session']+'.json')
                completed(inputs['support_completion'], path)
                value = intake.unit(target, variant, self.by_writer, self.lookup)
                if read(path) != value:
                    raise ValueError('support history differs from authenticated source')
                self.units[variant][target['session']] = value
        self.raw = RevisionSources({k:inputs[k] for k in RAW_INPUTS})

    def roster_for(self, variant):
        return population_roster(self.saved,self.roster,self.units[variant],self.lookup,variant)

    def covariates(self, sid):
        receipt = self.raw.session(sid)  # exact original P6 fields vs raw replay
        path = (self.raw.root/self.raw.raw[sid]['path']).resolve()
        with path.open(encoding='utf8') as stream:
            events = [json.loads(line) for line in stream]
        return dict(session=sid, writer=self.lookup[sid]['writer'], source_hashes=receipt['source_hashes'],
                    words={str(k):v for k,v in screen_covariates(events,self.lookup[sid]['words']).items()})


def calibrate(roster, units_by_session, lookup):
    """Paired calibration policy is separately reviewed before dispatch."""
    result = {}
    for writer, parts in sorted(roster['writers'].items()):
        losses = {arm:{alpha:[] for alpha in WEIGHTS} for arm in ('own','donor')}
        for sid in parts['supported_sessions']['calibration']:
            counts = histories(units_by_session[sid]['proof'],lookup)
            for word in lookup[sid]['words']:
                p = word['population_probability']
                if not word['is_word'] or p is None or p <= 0:
                    continue
                for arm, history in zip(('own','donor'),counts):
                    q = cache_probability(word,history,p)
                    for alpha in WEIGHTS:
                        losses[arm][alpha].append(-math.log((1-alpha)*p+alpha*q))
        if not losses['own'][0.]:
            result[writer] = dict(valid=False,reason='no supported calibration words; evaluation rows retained, whole variant invalid if they occur')
            continue
        means = {arm:{str(a):sum(v)/len(v) for a,v in values.items()} for arm,values in losses.items()}
        result[writer] = dict(valid=True, words=len(losses['own'][0.]), original_alpha=parts['original_alpha'],
            alpha={arm:min(WEIGHTS,key=lambda a:(means[arm][str(a)],a)) for arm in losses}, losses=means)
    return result


def scientific_rows(saved, roster, units_by_session, lookup, tuning, covariates):
    keys = {tuple(k) for k in roster['retained_keys']}
    out=[]; cached={}
    for row in saved['rows']:
        sid,writer,index = row['session'],row['writer'],row['index']
        if (sid,index) not in keys:
            continue
        if not tuning[writer]['valid']:
            raise ValueError('retained writer has no supported calibration words')
        if sid not in cached:
            cached[sid] = histories(units_by_session[sid]['proof'],lookup)
        word = lookup[sid]['words'][index]
        p = word['population_probability']; deviations={}
        for arm, counts in zip(('own','donor'),cached[sid]):
            alpha = tuning[writer]['alpha'][arm]
            deviations[arm+'_surprise'] = math.log(p/((1-alpha)*p+alpha*cache_probability(word,counts,p)))
        screen = covariates[sid]['words'][str(index)] if str(index) in covariates[sid]['words'] else covariates[sid]['words'][index]
        out.append(dict(row,original_personal_surprise=row['personal_surprise'], **deviations,
            on_screen=screen['on_screen'],session_surprisal=screen['session_surprisal']))
    if len(out) != len(keys):
        raise ValueError('supported scoring rows differ from frozen roster')
    return out
