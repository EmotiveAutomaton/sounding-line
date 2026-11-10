"""Metadata-only whole-writer scopes and the complete at-typing union.

DESIGN CHECK: frozen before scoring. Hamilton allocation by majority genre,
seed 20261102; selection never reads scores or pause outcomes. The original
source and its first-twenty-percent membership remain immutable.
"""
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from .week5_at_source import authenticate
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal


def select(metadata, count):
    writers = sorted(metadata)
    if not 1 <= count <= len(writers):
        raise ValueError('Whole-writer count outside source support')
    groups = defaultdict(list)
    for writer in writers:
        genres = Counter(metadata[writer].values())
        genre = min(genres, key=lambda k: (-genres[k], k))
        groups[genre].append(writer)
    quota = {g: count * len(v) / len(writers) for g, v in groups.items()}
    allocation = {g: int(v) for g, v in quota.items()}
    for g in sorted(groups, key=lambda g: (-(quota[g] - allocation[g]), g))[:count - sum(allocation.values())]:
        allocation[g] += 1
    rng = np.random.default_rng(20261102)
    chosen = []
    for g in sorted(groups):
        chosen.extend(rng.permutation(sorted(groups[g]))[:allocation[g]].tolist())
    return sorted(chosen), dict(allocation)


def produce(output, inputs, config, verifying=False):
    if set(inputs) != {'source_root'} or set(config) - {'writers', 'typing_population'}:
        raise ValueError('Exact scope inputs required')
    population = config.get('typing_population', 'frozen20')
    if population not in ('frozen20', 'full'):
        raise ValueError('Unregistered typing population')
    source = authenticate(inputs['source_root']) / 'output'
    index = read(source / 'INDEX.json'); metadata = defaultdict(dict)
    for item in index:
        p = source / item['file']
        if filehash(p) != item['sha256']:
            raise ValueError('Source session changed')
        for r in gzread(p)['rows']:
            metadata[r['writer']][r['session']] = r['genre']
    count = int(config.get('writers', len(metadata)))
    chosen, allocation = select(metadata, count); chosen = set(chosen)
    root = Path(output); root.mkdir(parents=True, exist_ok=True)
    entries = []; batches = []
    for item in index:
        payload = gzread(source / item['file'])
        rows = [r for r in payload['rows'] if r['writer'] in chosen]
        if not rows:
            continue
        value = dict(payload, rows=rows)
        target = root / item['file']
        if verifying:
            if gzread(target) != value:
                raise ValueError('Scoped source replay differs')
        else:
            gzip_equal(target, value)
        entries.append(dict(item, words=len(rows), sha256=filehash(target)))
        # Preserve original session ordinal in each batch key, so already
        # verified first-twenty-percent scores can be reused in a full union.
        ordinal = Path(item['file']).stem.split('-')[-1].split('.')[0]
        for context in ('final', 'at_typing'):
            supported = [r for r in rows if r[context + '_prefix'] is not None and
                         (context == 'final' or population == 'full' or r['at_typing_frozen20'])]
            for offset in range(0, len(supported), 256):
                name = f'batches/{context}-{ordinal}-{offset // 256:04d}.json.gz'
                value = supported[offset:offset + 256]
                if verifying:
                    if gzread(root / name) != value:
                        raise ValueError('Scoped batch replay differs')
                else:
                    gzip_equal(root / name, value)
                batches.append(dict(file=name, words=len(value), context=context, sha256=filehash(root / name)))
    summary = dict(source_complete_sha256=filehash(Path(inputs['source_root']) / 'COMPLETE.json'),
                   sample_scoped=count < len(metadata), writers=count, population_writers=len(metadata),
                   population_share=count / len(metadata), chosen_writers=sorted(chosen),
                   allocation=allocation, seed=20261102, typing_population=population,
                   scientific_admission=False)
    for name, value in [('INDEX.json', entries), ('BATCHES.json', batches), ('SUMMARY.json', summary)]:
        if verifying:
            if read(root / name) != value:
                raise ValueError('Scope reduction differs')
        else:
            write_equal(root / name, value)
    return dict(verified=True, complete_metadata_scope_replay=True) if verifying else dict(status='complete')


def execute(output, inputs, config): return produce(output, inputs, config)
def verify(output, inputs, config): return produce(output, inputs, config, True)
