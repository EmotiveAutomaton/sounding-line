"""Frozen whole-meeting sample, stratified by corpus before LA scoring."""
from pathlib import Path
from .week5_at_source import authenticate
from .week5_at_scope import select
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal


def produce(output, inputs, config, verifying=False):
    if set(inputs) != {'source_root'} or set(config) != {'meetings'}:
        raise ValueError('Exact whole-meeting sample required')
    source = authenticate(inputs['source_root']) / 'output'
    metadata = gzread(source / 'METADATA.json.gz')
    chosen, allocation = select({m: {m: v['corpus']} for m, v in metadata.items()}, int(config['meetings']))
    selected = set(chosen); root = Path(output)
    for name in ('ACTS.json.gz', 'LAUGHS.json.gz', 'METADATA.json.gz'):
        value = ({m: metadata[m] for m in chosen} if name == 'METADATA.json.gz' else
                 [r for r in gzread(source / name) if r['meeting'] in selected])
        if verifying:
            if gzread(root / name) != value:
                raise ValueError('Complete meeting-scope replay differs')
        else:
            gzip_equal(root / name, value)
    summary = dict(source_complete_sha256=filehash(Path(inputs['source_root']) / 'COMPLETE.json'),
                   meetings=len(chosen), population_meetings=len(metadata),
                   population_share=len(chosen) / len(metadata), sample_scoped=len(chosen) < len(metadata),
                   allocation=allocation, chosen_meetings=chosen, seed=20261102, scientific_admission=False)
    if verifying:
        if read(root / 'SUMMARY.json') != summary:
            raise ValueError('Scope reduction differs')
        return dict(verified=True, complete_metadata_scope_replay=True)
    write_equal(root / 'SUMMARY.json', summary)
    return dict(status='complete')


def execute(output, inputs, config): return produce(output, inputs, config)
def verify(output, inputs, config): return produce(output, inputs, config, True)
