"""CH7 adds authenticated pregame ratings to the immutable CH history projection.

DESIGN CHECK: source rows already contain only sampled players. No username,
new selection, engine result or inferred rating is introduced. Fresh verification
reprojects every complete source game; old CH4/CH6 indexes remain untouched.
"""
from contextlib import contextmanager
import json
import sqlite3
from . import week5_ch_history_index_bounded as base
from .week5_ch_source import digest

MONTHS=('2017-04','2017-05','2017-06')
ORIGINAL_PROJECTED=base.projected
ORIGINAL_SOURCE_INFO=base.source_info


def projected(month,ordinal,payload):
    meta=json.loads(payload)['meta']
    for player,value in ORIGINAL_PROJECTED(month,ordinal,payload):
        side=meta['players'].index(player)
        value.update(rating=meta['ratings'][side],opponent_rating=meta['ratings'][1-side],source_ordinal=ordinal)
        if meta['result'] not in ('1-0','0-1','1/2-1/2'):
            value['result']=None
        yield player,value


def source_info(inputs,config,check=None):
    path,total=ORIGINAL_SOURCE_INFO(inputs,config,check)
    con=sqlite3.connect(path)
    try:
        months=tuple(row[0] for row in con.execute('SELECT DISTINCT month FROM histories ORDER BY month'))
        if months!=MONTHS:
            raise ValueError('CH7 requires all three R2 source months')
    finally:con.close()
    return path,total


@contextmanager
def patched():
    old_projected,old_info=base.projected,base.source_info
    base.projected,base.source_info=projected,source_info
    try:yield
    finally:base.projected,base.source_info=old_projected,old_info


def configured(config):
    if set(config)-{'constructed_fixture','max_new_draws'}:
        raise ValueError('Unknown CH7 source configuration')
    return dict(config,ch7_projection_sha256=digest(__file__),months=list(MONTHS))


def execute(output,inputs,config):
    with patched():return base.execute(output,inputs,configured(config))


def verify(output,inputs,config):
    with patched():return base.verify(output,inputs,configured(config))
