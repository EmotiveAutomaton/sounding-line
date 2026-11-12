"""Complete R2 input-frame immutability, including sampler preparation.

DESIGN CHECK: v2 covers the selector connection but the unchanged sampler's
prepare() also opens the input. Replace only that module-scoped entry point in
this native child. Output/scratch SQLite connections remain writable. No global
sqlite monkeypatch, source selection change or previous-module mutation on disk.
"""
from contextlib import contextmanager
import hashlib
import json
from . import week5_ch_backhalf_roster_v2 as previous

source=previous.source
sample=previous.sample
ck=previous.ck
MONTHS=previous.MONTHS
QUOTAS=previous.QUOTAS
allocate=previous.allocate
choose_players=previous.choose_players
completed_frame=previous.completed_frame


def prepare(inputs,config,check=None):
    """Exact sample.prepare contract with only its input connection replaced."""
    frame=ck.checked(inputs['frame'],check);salt=ck.checked(inputs['salt'],check).read_bytes()
    con=completed_frame(frame)
    try:
        stamps={m:(s,json.loads(c),complete) for m,s,c,complete in con.execute('SELECT month,source,counts,complete FROM checkpoints')}
        if not stamps or any(not x[2] for x in stamps.values()):raise ValueError('Complete source census required')
        if con.execute("SELECT value FROM settings WHERE key='salt_sha256'").fetchone()!=(hashlib.sha256(salt).hexdigest(),):raise ValueError('Campaign salt mismatch')
    finally:con.close()
    sources=config['sources']
    if len({s['month'] for s in sources})!=len(sources) or set(s['month'] for s in sources)!=set(stamps):raise ValueError('Source roster must exactly match all census months')
    for spec in sources:
        ck.checked(spec,check)
        if stamps[spec['month']][0]!=spec['sha256']:raise ValueError('Raw source does not match counted month')
    selected,counts=source.choose_players(frame,config.get('players',10000))
    return salt,sources,selected,counts,sum(x[1]['source_games'] for x in stamps.values())


@contextmanager
def adapted(output,config):
    saved=sample.prepare
    try:
        with previous.selector(output,config):
            sample.prepare=prepare
            yield
    finally:sample.prepare=saved


def configured(config):
    return dict(previous.configured(config),back_half_prepare_sha256=source.digest(__file__))


def execute(output,inputs,config):
    with adapted(output,config):return sample.execute(output,inputs,configured(config))


def verify(output,inputs,config):
    with adapted(output,config):return sample.verify(output,inputs,configured(config))
