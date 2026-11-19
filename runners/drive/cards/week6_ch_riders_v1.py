"""Isolated CH13/CH14 SG1 consumer, checkpointed whole-player bootstrap.

DESIGN CHECK: LESSONS 2/3/5, extension AC/AD/AF. Complete native-qualified SG1
and prospective owner decisions are mandatory. The original source is immutable;
only new private projections are writable. Null/trap fixtures and independent
formula replay must qualify before any human admission. Source setup, failed
fits, all 2,000 refits and replay share each card's 40,000-CPU total allowance.
"""
from pathlib import Path
from collections import Counter
from collections.abc import Mapping
import json
import math
import sqlite3
import numpy as np
from . import week5_sg1_source_v1 as sg1
from . import week5_ch_pipeline_checkpoint as ck
from . import week5_ch_forecast_two_day_v1 as forecast
from . import week5_ch11_table_v2 as parity
from . import week5_ch10_table_v1 as berserk_gate
from . import week6_ch_riders_fields_v1 as fields
from . import week6_ch13_math_v1 as ch13
from . import week6_ch14_math_v1 as ch14
from .week5_ch_source import digest, write_json

SEED=20261115
DECISIONS=dict(wait_units='physical_minutes',outcome_centering='within_player',
    peer_scope='all_other_original_salted_2pct_players',peer_one_per_player='nearest_end_then_end_then_game',
    peer_window_seconds=60,peer_minimum_donors=1,peer_priority='both_intervals_exclude_zero_opposite_signs',
    peer_unsupported='retain_own_wait_with_self_selection_limit',
    ch13_loss_kind_comparator='same_forecast_stratum_for_loss_and_win',
    pair_order='adjacent_full_player_history_same_arena',
    ch14_fit='pooled_coefficients_equal_player_gain_whole_player_refits',
    ch14_options='prior_only_exclude_novel_then_update',ch14_minimum_options=2,
    ch14_split='floor_two_thirds_eligible_choices',ch14_centering='common_per_choice_shift',
    ch14_game_recency='all_intervening_player_games',ch14_week_break='same_fit_heldout_subset')


def identity(inputs,config):
    if set(config)-{'card','draws','constructed_fixture','max_new_draws','instrument_admitted'}:raise ValueError('Undeclared chess rider configuration')
    if config.get('card') not in ('CH13','CH14'):raise ValueError('Unknown chess rider')
    if config.get('draws',2000)!=2000 and not config.get('constructed_fixture'):raise ValueError('Full2,000 player draws required')
    if 'decisions' not in inputs:raise ValueError('Prospective exact owner decisions required')
    decision=ck.checked(inputs['decisions'])
    value=json.loads(decision.read_text('utf8'))
    if value.get('choices')!=DECISIONS or (value.get('status')!='OWNER_REVIEWED_CH_RIDERS_V1' and not config.get('constructed_fixture')):
        raise ValueError('Exact reviewed rider design choices required')
    return ck.binding(inputs,config,{m.__name__:digest(m.__file__) for m in
        (sg1,forecast,fields,ch13,ch14,parity,berserk_gate,berserk_gate.instrument)}|{'handler':digest(__file__)})


class AnalysisStore(Mapping):
    def __init__(self,store):self.store=store;self.names=[p for p in store if not forecast.calibration(p)]
    def __iter__(self):return iter(self.names)
    def __len__(self):return len(self.names)
    def __getitem__(self,key):
        if forecast.calibration(key):raise KeyError(key)
        return self.store[key]


def project_pairs(path,store,model,root,binding,reference=False,instrument_admitted=False,control_root=None):
    """Whole-player transaction checkpoints in this attempt's private scratch."""
    control_root=Path(control_root) if control_root is not None else root
    if path.exists():
        if reference:raise ValueError('Independent projection must start fresh')
        ck.copied(path,root,lambda:ck.require(root))
    con=sqlite3.connect(path)
    try:
        con.execute('PRAGMA journal_mode=DELETE')
        con.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        con.execute('CREATE TABLE IF NOT EXISTS pairs (player TEXT, game TEXT, arena TEXT, end REAL, analysis INTEGER, payload TEXT, PRIMARY KEY(player,game))')
        con.execute('CREATE INDEX IF NOT EXISTS arena_end ON pairs(arena,end)')
        con.execute('CREATE TABLE IF NOT EXISTS census (player TEXT PRIMARY KEY, payload TEXT)')
        state=dict(con.execute('SELECT key,value FROM settings'))
        encoded=json.dumps(binding,sort_keys=True)
        if state and state.get('binding')!=encoded:raise ValueError('Changed private pair projection')
        if not state:
            con.execute('INSERT INTO settings VALUES (?,?)',('binding',encoded));con.commit()
        last=state.get('last_player','')
        for player in store:
            ck.require(control_root)
            if player<=last:continue
            analysis=not forecast.calibration(player)
            rows,census=fields.arena_pairs(player,store[player],lambda r:forecast.predict(r,model,reference),analysis)
            for row in rows:row['berserk_admitted']=instrument_admitted
            with con:
                for row in rows:
                    con.execute('INSERT INTO pairs VALUES (?,?,?,?,?,?)',(player,row['game'],row['arena'],row['end'],int(analysis),json.dumps(row,sort_keys=True,allow_nan=False)))
                con.execute('INSERT INTO census VALUES (?,?)',(player,json.dumps(census,sort_keys=True)))
                con.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('last_player',player))
            write_json(root/'PROGRESS.json',dict(phase='complete_player_timing_projection',players_projected=con.execute('SELECT count(*) FROM census').fetchone()[0]),mutable=True)
        con.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('complete','true'));con.commit()
    finally:con.close()


class PairStore(Mapping):
    def __init__(self,path,root,reference=False):
        self.manager=sg1.snapshots.readonly_snapshot(path);self.con=self.manager.__enter__();self.root=root;self.reference=reference
        if dict(self.con.execute('SELECT key,value FROM settings')).get('complete')!='true':
            self.manager.__exit__(None,None,None);raise ValueError('Incomplete pair source')
        self.names=[r[0] for r in self.con.execute('SELECT DISTINCT player FROM pairs WHERE analysis=1 ORDER BY player')]
    def __iter__(self):return iter(self.names)
    def __len__(self):return len(self.names)
    def __getitem__(self,player):
        answer=[]
        for (payload,) in self.con.execute('SELECT payload FROM pairs WHERE player=? ORDER BY game',(player,)):
            ck.require(self.root);target=json.loads(payload);donors={}
            query='SELECT payload FROM pairs WHERE arena=? AND end>=? AND end<=? AND player<>? ORDER BY end,player,game'
            for (raw,) in self.con.execute(query,(target['arena'],target['end']-60,target['end']+60,player)):
                other=json.loads(raw);key=(abs(other['end']-target['end']),other['end'],other['game'])
                if other['player'] not in donors or key<donors[other['player']][0]:donors[other['player']]=(key,other['wait'])
            values=sorted(v[1] for v in donors.values());n=len(values)
            target['pool_donors']=n
            target['pool_wait']=((values[(n-1)//2]+values[n//2])/2 if self.reference else fields.statistics.median(values)) if n else None
            answer.append(target)
        return answer
    def close(self):self.manager.__exit__(None,None,None)


def run(output,root,inputs,config,reference=False):
    output=Path(output);root=Path(root);output.mkdir(parents=True,exist_ok=True)
    binding=identity(inputs,config)
    source_inputs={k:v for k,v in inputs.items() if k!='decisions'}
    if config.get('instrument_admitted'):
        if config['card']!='CH13':raise ValueError('Berserk instrument only belongs to CH13 secondary')
        source=berserk_gate.authenticate(source_inputs,config,root)
    else:source=sg1.authenticate_consumer(source_inputs,config,root)
    checkpoint=output/'RIDER_CHECKPOINT.json';values=[]
    if checkpoint.exists():
        if reference:raise ValueError('Independent formula replay starts fresh')
        ck.copied(checkpoint,root,lambda:ck.require(root));prior=json.loads(checkpoint.read_text('utf8'))
        if prior['binding']!=binding:raise ValueError('Changed rider checkpoint')
        values=prior['draws']
    def save():write_json(checkpoint,dict(binding=binding,draws=values),mutable=True)
    pairs=None
    try:
        with sg1.HistoryStore(source,bool(config.get('constructed_fixture'))) as store:
            if config['card']=='CH13':
                model_path=output/'FORECAST.json'
                if model_path.exists() and not reference:
                    ck.copied(model_path,root,lambda:ck.require(root));model=json.loads(model_path.read_text('utf8'))
                else:
                    model=forecast.prepare(store,lambda:ck.require(root),reference);write_json(model_path,model)
                private=output/'PRIVATE_ARENA_PAIRS.sqlite'
                project_pairs(private,store,model,output,binding,reference,bool(config.get('instrument_admitted')),root)
                pairs=PairStore(private,root,reference)
                prepared=ch13.prepare_grouped(pairs,reference,lambda:ck.require(root))
                source_census=Counter()
                for (raw,) in pairs.con.execute('SELECT payload FROM census'):source_census.update(json.loads(raw))
                point=None;sets=None
            else:
                prepared=ch14.prepare(AnalysisStore(store),lambda:ck.require(root));sets=ch14.model_sets(prepared)
                point=ch14.draw(prepared,sets,np.ones(len(prepared['names'])),reference,lambda:ck.require(root))
                source_census={}
            n=len(prepared['names']);rng=np.random.default_rng(SEED);new=0
            for index in range(config.get('draws',2000)):
                weights=np.bincount(rng.integers(0,n,n),minlength=n) if n else np.zeros(0)
                if index<len(values):continue
                ck.require(root)
                if not reference and new>=config.get('max_new_draws',2000):
                    save();return dict(status='yielded',phase='whole_player_refits',completed_draws=len(values))
                value=ch13.draw(prepared,weights,reference) if config['card']=='CH13' else ch14.draw(prepared,sets,weights,reference,lambda:ck.require(root))
                values.append(value);new+=1
                if new%10==0:save()
                write_json(output/'PROGRESS.json',dict(phase='whole_player_refits',completed=len(values),total=config.get('draws',2000),reference=reference),mutable=True)
                if len(values)>=math.ceil(config.get('draws',2000)/20) and not (output/'PILOT.json').exists():
                    write_json(output/'PILOT.json',dict(draws=len(values),setup_already_charged=True,basis='5% of draws, not total CPU fraction'))
            result=ch13.result(prepared,values) if config['card']=='CH13' else ch14.result(prepared,point,values)
            result.update(source_census=dict(source_census),constructed_fixture=bool(config.get('constructed_fixture')),
                source_scope='original salted 2% April–June2017 player histories; analysis split unchanged',
                record_kind='claim',by_construction=False,theory_tags=['H24-S20','LEFTOVER-LIFETIME'] if config['card']=='CH13' else ['H24-S21','READINESS'],
                activation=[dict(channel='not identified',set_point='public game forecast, behavioral analogy',moved='prior result' if config['card']=='CH13' else 'past use and recency',could_do='wait or choose a prior opening',observed='recorded game timing or first move',relation='mechanism not established')])
            write_json(output/'SCIENCE.json',result);save()
            return dict(status='complete',card=config['card'],scientific_result_complete=True)
    except ck.YieldRequested:
        save();return dict(status='yielded',phase='source_setup_or_whole_player_refits',completed_draws=len(values),verification_prefix_credited=False)
    finally:
        if pairs is not None:pairs.close()


def _execute(output,inputs,config):
    output=Path(output);binding=identity(inputs,config)
    if ck.sealed(output,binding,lambda:ck.require(output)):return dict(status='complete',sealed_output_reused=True)
    answer=run(output,output,inputs,config)
    if answer['status']=='complete':
        names=['SCIENCE.json']+(['FORECAST.json','PRIVATE_ARENA_PAIRS.sqlite'] if config['card']=='CH13' else [])
        ck.seal(output,binding,names,lambda:ck.require(output))
    return answer


def _verify(output,inputs,config):
    output=Path(output)
    if not ck.sealed(output,identity(inputs,config),lambda:ck.require(output)):raise ValueError('Sealed complete rider output required')
    ordinal=1
    while (output/f'independent-{ordinal:04}').exists():ordinal+=1
    target=output/f'independent-{ordinal:04}'
    answer=run(target,output,inputs,config,True)
    if answer['status']!='complete':return answer
    left=json.loads((output/'SCIENCE.json').read_text('utf8'));right=json.loads((target/'SCIENCE.json').read_text('utf8'))
    # Solver diagnostics can differ, while every fitted coefficient, held-out
    # point, denominator, classification and bootstrap interval must agree.
    for result in (left,right):
        for fitted in result.get('fit',{}).values():
            fitted.pop('max_gradient',None);fitted.pop('minimum_information_eigenvalue',None)
    parity.equivalent(left,right)
    return dict(verified=True,independent_formulas=True,all_whole_player_draws_recomputed=True,raw_source_requalification=False)


def execute(output,inputs,config):return ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config):return ck.guarded(_verify,output,inputs,config)
