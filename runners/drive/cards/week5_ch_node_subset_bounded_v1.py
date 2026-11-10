"""Unqualified counted CH node-texture roster, exact original selection.

DESIGN CHECK: whole players, original seeded rank and greedy capacity rule,
original within-player order, complete parent census and independent replay.
This produces one shared subset before either node-count readout. No engine
value enters selection; both texture routes retain the same original roster.
"""
from pathlib import Path
import gzip
import hashlib
import json
import os
import sqlite3
import time

from . import week5_ch_batch_planner as original
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest, write_json


FILES = ('PRIVATE_POSITIONS.jsonl.gz', 'SUBSET.json')
SELECTION = 'whole players by seeded player hash, before engine readout; shared by both node counts'
ROW_BYTES = 4*1024**2


def identity(inputs, config):
    if set(inputs) != {'positions'} or set(config)-{'expected_positions','maximum_positions','max_new_draws','constructed_fixture'}:
        raise ValueError('Exact complete parent-roster contract required')
    expected, maximum = config.get('expected_positions'), config.get('maximum_positions',25000)
    if type(expected) is not int or not 1 <= expected <= 400000:
        raise ValueError('Complete parent denominator required')
    if type(maximum) is not int or not 1 <= maximum <= 25000:
        raise ValueError('Packet node-texture position cap')
    return ck.binding(inputs, config, dict(adapter=digest(__file__), original=digest(original.__file__)))


class Control:
    def __init__(self, output, request_root, config, operation):
        self.output, self.root = Path(output), Path(request_root)
        self.operation, self.quantum = operation, config.get('max_new_draws')
        self.new, self.started = 0, time.process_time()
        self.phase, self.done, self.total = 'authentication', 0, None

    def check(self):
        if ck.requested(self.root):
            raise ck.YieldRequested('Owner request at node-subset boundary')
        if self.quantum is not None and self.new >= self.quantum:
            raise ck.YieldRequested('Completed node-subset operational quantum')

    def advance(self, phase, done, total):
        self.new += 1
        self.phase, self.done, self.total = phase, done, total

    def record(self):
        write_json(self.output/'PROGRESS.json', dict(
            operation=self.operation, phase=self.phase, completed=self.done,
            total=self.total, new_this_invocation=self.new,
            invocation_cpu_seconds=time.process_time()-self.started,
            unit='one parent row, complete player capacity decision, or gzip row',
            first_five_percent_total_work_claim=False, population_complete=False), mutable=True)


def next_path(root, prefix, suffix=''):
    index = 1
    while (root/(prefix+f'-{index:06}'+suffix)).exists():
        index += 1
    return root/(prefix+f'-{index:06}'+suffix)


def run(output, request_root, inputs, config, operation):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    bound = identity(inputs,config)
    control = Control(output,request_root,config,operation)
    source = ck.checked(inputs['positions'],control.check)
    expected, maximum = config['expected_positions'],config.get('maximum_positions',25000)
    db = output/'PRIVATE_NODE_SUBSET.sqlite'
    if db.exists():
        if operation != 'execute':
            raise ValueError('Independent subset workspace must be fresh')
        ck.copied(db,request_root,control.check)
    con = sqlite3.connect(db)
    con.execute('PRAGMA journal_mode=DELETE')
    con.execute('PRAGMA synchronous=FULL')
    con.execute('PRAGMA temp_store=FILE')
    con.execute('PRAGMA cache_size=-8192')
    con.execute('CREATE TABLE IF NOT EXISTS rows(ordinal INTEGER PRIMARY KEY,player TEXT,payload TEXT NOT NULL)')
    con.execute('CREATE INDEX IF NOT EXISTS player_rows ON rows(player,ordinal)')
    con.execute('CREATE TABLE IF NOT EXISTS players(player TEXT PRIMARY KEY,rank TEXT,first_ordinal INTEGER,n INTEGER)')
    con.execute('CREATE INDEX IF NOT EXISTS player_rank ON players(rank,first_ordinal)')
    con.execute('CREATE TABLE IF NOT EXISTS selected(player TEXT PRIMARY KEY,pick INTEGER UNIQUE)')
    state = ck.initialize(con,bound,dict(phase='source',rows=0,players_visited=0,
                                       selected_players=0,selected_positions=0))

    def save():
        ck.put(con,'state',state)
        con.commit()
        control.record()

    def advance(phase,done,total):
        control.advance(phase,done,total)
        if control.new%100 == 0:
            save()

    try:
        if state['phase'] == 'source':
            ordinal = 0
            with gzip.open(source,'rb') as stream:
                while True:
                    control.check()
                    line = stream.readline(ROW_BYTES+1)
                    if not line:
                        break
                    if len(line)>ROW_BYTES:
                        raise ValueError('Parent row exceeds resource bound; no truncation')
                    ordinal += 1
                    if ordinal <= state['rows']:
                        continue
                    row = json.loads(line)
                    player = row['player']
                    if not isinstance(player,str):
                        raise ValueError('Original string player key required')
                    rank = hashlib.sha256(('20261107:CH-node-texture:'+player).encode()).hexdigest()
                    con.execute('INSERT INTO rows VALUES(?,?,?)',
                                (ordinal,player,json.dumps(row,sort_keys=True,separators=(',',':'))))
                    con.execute('INSERT INTO players VALUES(?,?,?,1) ON CONFLICT(player) DO UPDATE SET n=n+1',
                                (player,rank,ordinal))
                    state['rows'] = ordinal
                    if ordinal>expected:
                        raise ValueError('Parent roster exceeds admitted denominator')
                    advance('parent_rows',ordinal,expected)
            if ordinal != expected:
                raise ValueError('Complete parent roster denominator differs')
            state['phase'] = 'players'
            save()

        if state['phase'] == 'players':
            players = con.execute('SELECT COUNT(*) FROM players').fetchone()[0]
            for index,(player,count) in enumerate(con.execute('SELECT player,n FROM players ORDER BY rank,first_ordinal'),1):
                control.check()
                if index<=state['players_visited']:
                    continue
                if state['selected_positions']+count<=maximum:
                    con.execute('INSERT INTO selected VALUES(?,?)',(player,state['selected_players']))
                    state['selected_players'] += 1
                    state['selected_positions'] += count
                state['players_visited'] = index
                advance('complete_player_capacity_decisions',index,players)
            if not state['selected_positions']:
                raise ValueError('No whole player fits node-texture subset')
            state['phase'] = 'gzip'
            save()

        if state['phase'] == 'gzip':
            partial = next_path(output,'PRIVATE_POSITIONS.partial','.gz')
            # Hash-rank player order, then original parent order within player,
            # including the original stable first-occurrence rank tie break.
            query = 'SELECT r.payload FROM selected s JOIN rows r ON r.player=s.player ORDER BY s.pick,r.ordinal'
            with partial.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as stream:
                for index,(payload,) in enumerate(con.execute(query),1):
                    control.check()
                    stream.write((payload+'\n').encode())
                    advance('gzip_rows_restart_on_interrupt',index,state['selected_positions'])
            check = lambda: ck.require(request_root)
            check()
            destination = output/FILES[0]
            if destination.exists():
                if ck.file_digest(destination,check)!=ck.file_digest(partial,check):
                    raise ValueError('Existing subset output differs')
            else:
                os.replace(partial,destination)
            write_json(output/'SUBSET.json',dict(
                parent_roster_sha256=inputs['positions']['sha256'],
                selected_positions=state['selected_positions'],selected_players=state['selected_players'],
                maximum_positions=maximum,selection=SELECTION,texture_only=True,
                positions_sha256=ck.file_digest(destination,check)))
            state['phase'] = 'complete'
            save()
        return dict(status='complete',positions=state['selected_positions'],players=state['selected_players'])
    except ck.YieldRequested as exc:
        save()
        return dict(status='yielded',reason=str(exc),operation=operation,phase=state['phase'],
                    completed=control.done,total=control.total,new_completed_units=control.new,
                    first_five_percent_total_work_claim=False,verification_prefix_credited=False,
                    incomplete_gzip_reused=False,population_complete=False)
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def _execute(output,inputs,config):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    check = lambda: ck.require(output)
    bound = identity(inputs,config)
    if ck.sealed(output,bound,check):
        return dict(status='complete',sealed_output_reused=True)
    result = run(output,output,inputs,config,'execute')
    if result['status']=='complete':
        ck.seal(output,bound,FILES,check)
    return result


def _verify(output,inputs,config):
    output = Path(output)
    check = lambda: ck.require(output)
    if not ck.sealed(output,identity(inputs,config),check):
        raise ValueError('Complete subset execution required')
    independent = next_path(output,'independent_subset')
    result = run(independent,output,inputs,config,'verify')
    if result['status']=='yielded':
        return result
    for name in FILES:
        if ck.file_digest(output/name,check)!=ck.file_digest(independent/name,check):
            raise ValueError('Full parent-source subset replay differs: '+name)
    return dict(verified=True,complete_recalculation=True,source_start_ordinal=0,
                execution_selection_reused=False,verification_prefix_credited=False)


def execute(output,inputs,config):
    return ck.guarded(_execute,output,inputs,config)


def verify(output,inputs,config):
    return ck.guarded(_verify,output,inputs,config)
