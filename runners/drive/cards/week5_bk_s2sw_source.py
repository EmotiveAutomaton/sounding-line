"""S2.sw released-insert spans, temporal continuity and later overlap.

DESIGN CHECK: LESSONS 2-5 and BK_S2SW.md. A missing clock, discontinuous
editor view or author boundary cannot create a negative revision observation.
Null and signed worlds share exactly the same source eligibility. This is a
descriptive released-change timing proxy; physical word-onset flow is absent.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib, hmac, json, math, re, time
import numpy as np
from sklearn.mixture import GaussianMixture
from threadpoolctl import threadpool_limits
from runners.stage9.scholawrite import validate, boundary, SOURCE_COUNTS
from .week3_pp3_inputs import load as load_rows, CONFIG as SOURCE_CONFIG, envelope
from .week5_bk_klicke_intake import read, write, digest

SEED = 20261102
WORD = re.compile(r"[^\W\d_]+(?:['\u2019][^\W\d_]+)?", re.UNICODE)
CONTROL_NAMES = ('log_words', 'mean_word_length', 'population_log_frequency',
                 'own_prior_log_frequency', 'sentence_boundary', 'paragraph_boundary',
                 'time_on_segment_minutes', 'segment_order', 'distance_from_visible_end',
                 'remaining_minutes')


def key(salt, value):
    return hmac.new(salt, json.dumps(value, ensure_ascii=False, sort_keys=True).encode(), hashlib.sha256).hexdigest()


def groups(inputs, mode):
    wanted = {'fixture', 'identity_salt'} if mode == 'constructed' else {'source_identity', 'identity_salt'}
    if set(inputs) != wanted: raise ValueError('Exact ScholaWrite source/salt inputs required')
    salt = Path(inputs['identity_salt']).read_bytes()
    if len(salt) != 32: raise ValueError('Campaign identity salt must be 32 bytes')
    rows = read(inputs['fixture']) if mode == 'constructed' else load_rows({'source_identity': inputs['source_identity']}, SOURCE_CONFIG)
    streams = defaultdict(list); labels = Counter()
    for ordinal, row in enumerate(rows):
        validate(row); labels[row['label']] += 1
        streams[(row['project'], row['author'])].append(dict(row, ordinal=ordinal))
    if mode == 'corpus' and (len(rows) != 61504 or len(streams) != 12 or len({p for p, a in streams}) != 5 or dict(labels) != SOURCE_COUNTS):
        raise ValueError('Full ScholaWrite population/canonical labels differ')
    result = []
    for (project, author), stream in sorted(streams.items()):
        stream.sort(key=lambda r: (r['timestamp'], r['ordinal']))
        counts = Counter(r['timestamp'] for r in stream)
        for row in stream: row['timestamp_count'] = counts[row['timestamp']]
        result.append((key(salt, ['project', project]), key(salt, ['project-author', project, author]), stream))
    return result, dict(rows=len(rows), projects=len({p for p, a in streams}), project_scoped_authors=len(streams), labels=dict(sorted(labels.items())))


def distance(text, offset):
    """Visible sentence/paragraph separators, not hidden cursor telemetry."""
    tail = text[offset:]
    chunks = [s for s in re.split(r'(?<=[.!?])\s+|\n+', tail) if s.strip()]
    return max(0, len(chunks)-1), bool(re.search(r'\n[^\n]*\S', tail))


def segment_rows(stream):
    segments = []; current = []; audit = Counter()
    for row in stream:
        reason = boundary(current[-1], row) if current else None
        if current and reason:
            segments.append((current, reason)); current = []; audit[reason] += 1
        current.append(row)
    if current: segments.append((current, 'end of released author stream'))
    return segments, audit


def project_segment(rows, author, project, number, ending, callback=lambda: None):
    """Exact single-envelope deltas; insert-only runs never use annotation labels."""
    current = rows[0]['before text']; lineage = [frozenset() for _ in current]
    units = []; active = None; start = rows[0]['timestamp']; end = rows[-1]['timestamp']
    for index, row in enumerate(rows):
        if current != row['before text']: raise ValueError('Segment editor continuity changed')
        left, deleted, inserted = envelope(current, row['after text'])
        pure = deleted == 0 and inserted > 0
        continuation = pure and active is not None and left == active['current_end']
        if not continuation: active = None
        hits = set().union(*lineage[left:left+deleted]) if deleted else set()
        if not deleted and inserted and 0 < left < len(lineage):
            hits = set(lineage[left-1] & lineage[left])
        sentences, paragraph = distance(current, left)
        for unit_id in sorted(hits):
            unit = units[unit_id]
            if active is not None and unit_id == active['unit']: continue
            if row['ordinal'] in unit['ordinals']: continue
            unit['later_edits'].append(dict(ordinal=row['ordinal'], lag_seconds=(row['timestamp']-unit['end_ms'])/1000,
                label=row['label'], category=row['high-level'], visible_sentence_nonlocal=sentences >= 1,
                visible_paragraph_nonlocal=paragraph, deleted_chars=deleted, inserted_chars=inserted))
        if pure:
            if active is None:
                active = dict(unit=len(units), ordinals=[], gaps_seconds=[], text='', start_ms=row['timestamp'], end_ms=row['timestamp'],
                    current_end=left, start_distance=sentences, sentence_boundary=left == 0 or current[left-1] in '.!?\n',
                    paragraph_boundary=left == 0 or current[left-1] == '\n', later_edits=[], production_labels=[])
                units.append(active)
            if active['ordinals']: active['gaps_seconds'].append((row['timestamp']-active['end_ms'])/1000)
            active['ordinals'].append(row['ordinal']); active['end_ms'] = row['timestamp']
            active['text'] += row['after text'][left:left+inserted]
            active['production_labels'].append(row['label']); active['current_end'] = left+inserted
            inherited = frozenset(hits | {active['unit']})
        else: inherited = frozenset(hits)
        lineage[left:left+deleted] = [inherited for _ in range(inserted)]
        current = row['after text']
        if len(lineage) != len(current): raise ValueError('Inserted lineage length mismatch')
        if index % 100 == 0: callback()
    for unit in units:
        unit['remaining_seconds'] = (end-unit['end_ms'])/1000
        unit['observed_later_rows'] = sum(r['timestamp'] > unit['end_ms'] for r in rows)
        unit['time_on_segment_minutes'] = (unit['start_ms']-start)/60000
        unit['segment_order'] = number; unit['author'] = author; unit['project'] = project
        unit['session'] = f'{author}:{number}'
        unit['end_reason'] = ending
        # Preserve empty/deleted/short spans; these are explicit timing strata.
        unit['words'] = [m.group().casefold() for m in WORD.finditer(unit['text'])]
        unit.pop('current_end')
    return units


def fit_mixture(gaps):
    if len(gaps) < 30 or len(set(gaps)) < 3:
        return dict(state='unsupported', intervals=len(gaps)), None
    median = float(np.median(gaps)); z = np.log(np.asarray(gaps)/median).reshape(-1, 1)
    model = GaussianMixture(n_components=3, covariance_type='full', reg_covar=1e-6, tol=1e-4,
        max_iter=500, n_init=1, random_state=SEED, means_init=np.quantile(z, [.2,.65,.95]).reshape(3,1)).fit(z)
    order = np.argsort(model.means_.ravel())
    if not model.converged_: return dict(state='invalid', reason='nonconverged released-gap mixture', intervals=len(gaps)), None
    if np.any(np.diff(model.means_.ravel()[order]) <= 1e-6) or np.any(model.weights_[order] <= 1e-6):
        return dict(state='invalid', reason='collapsed released-gap mixture', intervals=len(gaps)), None
    result = dict(state='fitted released-change proxy', intervals=len(gaps), median_seconds=median,
        means=model.means_.ravel()[order].tolist(), variances=model.covariances_.ravel()[order].tolist(), weights=model.weights_[order].tolist())
    return result, (model, int(order[0]), median)


def project_author(project, author, rows, callback=lambda: None):
    segments, breaks = segment_rows(rows); units = []; gaps = []
    edge_counts = Counter()
    for left,right in zip(rows,rows[1:]):
        delta = (right['timestamp']-left['timestamp'])/1000
        edge_counts['released_edges'] += 1
        edge_counts['nonpositive_clock_edges'] += delta <= 0
        edge_counts['ambiguous_clock_edges'] += left['timestamp_count'] != 1 or right['timestamp_count'] != 1
        edge_counts['gaps_over_thirty_minutes'] += delta > 1800
        edge_counts['discontinuous_visible_edges'] += left['after text'] != right['before text']
    for number, (segment, ending) in enumerate(segments):
        gaps.extend((b['timestamp']-a['timestamp'])/1000 for a,b in zip(segment, segment[1:]))
        units.extend(project_segment(segment, author, project, number, ending, callback)); callback()
    mixture, model = fit_mixture(gaps)
    for unit in units:
        durations = unit['gaps_seconds']; reason = None
        if not durations: reason = 'single released insert; no internal gap'
        elif max(durations) > 60: reason = 'internal gap over sixty seconds'
        elif not unit['words']: reason = 'no words in inserted span'
        elif model is None: reason = 'unavailable author timing mixture'
        if reason: unit['timing_state'] = reason; unit['hesitancy'] = None; unit['class'] = None
        else:
            fitted, fastest, median = model
            unit['hesitancy'] = float(np.mean(1-fitted.predict_proba(np.log(np.asarray(durations)/median).reshape(-1,1))[:,fastest]))
            unit['timing_state'] = 'eligible released-change proxy'
    values = [u['hesitancy'] for u in units if u['hesitancy'] is not None]
    thresholds = np.quantile(values, [1/3,2/3]).tolist() if values else None
    for unit in units:
        if unit['hesitancy'] is not None:
            unit['class'] = 'flow_proxy' if unit['hesitancy'] < thresholds[0] else 'hesitant_proxy' if unit['hesitancy'] > thresholds[1] else 'middle_or_tie'
    return dict(author=author, project=project, rows=len(rows), segments=len(segments), boundary_counts=dict(breaks),
        edge_counts=dict(edge_counts), observed_contiguous_gaps=len(gaps), mixture=mixture, thresholds=thresholds, units=units)


def controls(authors):
    vocab = set(); total = Counter(); own = {}
    for record in authors:
        counts = Counter(w for u in record['units'] for w in u['words']); own[record['author']] = counts
        total.update(counts); vocab.update(counts)
    v = max(1, len(vocab))
    for record in authors:
        counts = own[record['author']]; population = total-counts; n = sum(population.values()); past = Counter(); past_total = 0
        for unit in record['units']:
            words = unit['words']; size = len(words)
            unit['controls'] = dict(log_words=math.log1p(size), mean_word_length=float(np.mean([len(w) for w in words])) if words else 0.,
                population_log_frequency=float(np.mean([math.log((population[w]+1)/(n+v)) for w in words])) if words else 0.,
                own_prior_log_frequency=float(np.mean([math.log((past[w]+1)/(past_total+v)) for w in words])) if words else 0.,
                sentence_boundary=int(unit['sentence_boundary']), paragraph_boundary=int(unit['paragraph_boundary']),
                time_on_segment_minutes=unit['time_on_segment_minutes'], segment_order=unit['segment_order'],
                distance_from_visible_end=unit['start_distance'], remaining_minutes=unit['remaining_seconds']/60)
            past.update(words); past_total += len(words)
    return authors


def run(output, inputs, config, verification=False):
    if set(config) != {'card','mode','max_new_draws'} or config['card'] != 'BK-S2.sw-source' or config['mode'] not in ('constructed','corpus') or type(config['max_new_draws']) is not int or config['max_new_draws'] < 1:
        raise ValueError('Frozen S2.sw source configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True); start = time.process_time()
    streams, census = groups(inputs, config['mode']); records = []; new = 0
    binding = {name: digest(path) for name,path in inputs.items()}
    if (output/'BINDING.json').exists() and read(output/'BINDING.json') != binding: raise ValueError('Source checkpoint input changed')
    def check():
        if (output/'YIELD_REQUEST.json').exists(): raise InterruptedError('owner request')
    try:
        with threadpool_limits(limits=1):
            for i, (project, author, stream) in enumerate(streams):
                dest = output/'authors'/f'{i:03d}.json.gz'
                if verification or not dest.exists():
                    value = project_author(project, author, stream, check); new += 1
                    if verification:
                        if read(dest) != value: raise ValueError('Fresh complete source reconstruction differs')
                    else: write(dest, value)
                else: value = read(dest)
                if value['author'] != author or value['rows'] != len(stream): raise ValueError('Saved author population differs')
                records.append(value)
                if not verification and new == 1 and not (output/'PILOT.json').exists():
                    write(output/'PILOT.json', dict(new_source_rows=len(stream), total_source_rows=census['rows'], cpu_seconds=time.process_time()-start,
                        projected_execute_verify_cpu=2*(time.process_time()-start)*census['rows']/len(stream)))
                if not verification and i+1 < len(streams) and new >= config['max_new_draws']:
                    write(output/'BINDING.json', binding)
                    return dict(status='yielded', reason='complete author boundary', completed_units=i+1, new_authors=new)
                check()
    except InterruptedError:
        write(output/'BINDING.json', binding)
        return dict(status='yielded', reason='owner request; incomplete author restarts; fresh verification always restarts all authors')
    derived = controls(records)
    summary = dict(card='BK-S2.sw-source', constructed=config['mode']=='constructed', census=census,
        production_spans=sum(len(r['units']) for r in records),
        timing_states=dict(Counter(u['timing_state'] for r in records for u in r['units'])),
        classifications=dict(Counter(u['class'] or 'timing unavailable' for r in records for u in r['units'])),
        boundary_counts=dict(sum((Counter(r['boundary_counts']) for r in records), Counter())),
        edge_counts=dict(sum((Counter(r['edge_counts']) for r in records), Counter())),
        no_later_observed_row=sum(u['observed_later_rows']==0 for r in records for u in r['units']),
        internal_break_spans=sum(any(g>60 for g in u['gaps_seconds']) for r in records for u in r['units']),
        complete_population=True, physical_word_onset_flow_available=False, effect_computed=False)
    for name, value in [('BINDING.json',binding),('PRIVATE_SPANS.json.gz',derived),('SUMMARY.json',summary)]:
        if verification:
            if read(output/name) != value: raise ValueError('Source final summary or control replay differs')
        else: write(output/name,value)
    return dict(verified=True,complete_source_replay=True,new_authors=new) if verification else dict(status='complete',new_authors=new)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
