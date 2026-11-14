"""SG1.v table-only clock instrument check; no automatic CH10 admission.

DESIGN CHECK: a produced histogram is not a validated flag. Missing/outside
clocks cannot dilute the non-tournament rate. Boundary bins are explicit.
Independent arithmetic replays every row from the authenticated SG1 table.
"""
from pathlib import Path
import json,math
from . import week5_sg1_source_v1 as sg1
from . import week5_sg1_fields_v1 as fields
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest,write_json


def histogram(rows,reference=False):
    if not reference:return fields.histogram(rows)
    result={name:dict(bins=[0]*20,in_band=0,denominator=0,missing=0,outside=0)
            for name in ['tournament','other']}
    edges=[k/20 for k in range(21)]
    for row in rows:
        if row['increment']!=0:continue
        group=result['tournament' if row['tournament'] else 'other']
        actual=None if row['own_first_clock'] is None else row['own_first_clock']/row['initial']
        if actual!=row['first_clock_ratio']:raise ValueError('SG1 ratio disagrees with its verified clock columns')
        if actual is None:group['missing']+=1;continue
        if not math.isfinite(actual):raise ValueError('Nonfinite SG1 clock ratio')
        group['denominator']+=1
        if .45<=actual<=.55:group['in_band']+=1
        if actual<0 or actual>1:group['outside']+=1;continue
        # Independent ordered comparisons, including the right-closed last bin.
        position=19 if actual==1 else next(i for i in range(20) if edges[i]<=actual<edges[i+1])
        group['bins'][position]+=1
    return result


def decision(hist):
    for group in hist.values():
        if (len(group['bins'])!=20 or any(type(n) is not int or n<0 for n in group['bins'])
                or sum(group['bins'])+group['outside']!=group['denominator']
                or group['in_band']>sum(group['bins'])):
            raise ValueError('Clock histogram denominator mismatch')
    valid=sum(hist['other']['bins']);rate=None if not valid else hist['other']['in_band']/valid
    bins=hist['tournament']['bins']
    half=max(bins[9:11]);whole=bins[19]
    half_mode=half>max(bins[8],bins[11])
    whole_mode=whole>bins[18]
    valley=min(bins[11:19])<min(half,whole)
    supported=bool(rate is not None and rate<.002 and half_mode and whole_mode and valley)
    return dict(card='SG1.v',histogram=hist,non_tournament_band_rate=rate,
        non_tournament_valid_clock_denominator=valid,
        excluded_from_rate=dict(missing=hist['other']['missing'],outside=hist['other']['outside']),
        modes=dict(half_mode=half_mode,whole_mode=whole_mode,intervening_valley=valley,
                   half_peak_bins=[9,10],half_exterior_bins=[8,11],whole_peak_bin=19,whole_adjacent_bin=18),
        instrument_supported=supported,flag_admitted=False,
        status='instrument check passes, owner admission pending' if supported else 'instrument unsupported; CH10 held',
        boundary_definition='20 half-open bins [i/20,(i+1)/20), last includes 1; flag band [0.45,0.55] inclusive; half-mode bins [0.45,0.55) exclude the 0.55 endpoint only from modal location',
        denominator_definition='Gate rate uses finite observed zero-increment ratios in [0,1]; missing and outside clocks reported and excluded, not counted as non-berserk',
        record_kind='run',theory_tags=['H15-T2'],by_construction=True,activation=[],
        interpretation='Instrument validation only; a public game rating is not standing in a room; no behavioral/channel verdict.')


def identity(inputs,config):
    if set(config)-{'constructed_fixture','max_new_draws'}:raise ValueError('Unknown SG1.v configuration')
    return ck.binding(inputs,config,dict(handler=digest(__file__),source=digest(sg1.__file__),fields=digest(fields.__file__)))


def run(output,root,inputs,config,reference=False):
    output=Path(output);root=Path(root);output.mkdir(parents=True,exist_ok=True)
    bound=identity(inputs,config);path=sg1.authenticate_consumer(inputs,config,root)
    checkpoint=output/'INSTRUMENT_CHECKPOINT.json'
    state=dict(binding=bound,players_done=0,last_player=None,histogram=histogram([]))
    if checkpoint.exists():
        if reference:raise ValueError('Instrument replay starts from zero')
        ck.copied(checkpoint,root,lambda:ck.require(root))
        state=json.loads(checkpoint.read_text())
        if state['binding']!=bound:raise ValueError('Changed SG1.v checkpoint')
    new=0
    def save():write_json(checkpoint,state,mutable=True)
    try:
        with sg1.HistoryStore(path,bool(config.get('constructed_fixture'))) as store:
            total=len(store)
            for player in store:
                if state['last_player'] is not None and player<=state['last_player']:continue
                ck.require(root)
                quantum=config.get('max_new_draws') if not reference else None
                if quantum is not None and new>=quantum:
                    save();return dict(status='yielded',completed_players=state['players_done'],total_players=total)
                sg1.histogram_add(state['histogram'],histogram(store[player],reference))
                state['last_player']=player;state['players_done']+=1;new+=1;save()
                if state['players_done']>=math.ceil(total/20) and not (output/'PILOT.json').exists():
                    write_json(output/'PILOT.json',dict(completed_players=state['players_done'],total_players=total,
                        basis='whole-player table units, not equal rows/CPU; source authentication already charged'))
            if state['players_done']!=total:raise ValueError('Incomplete SG1.v player coverage')
        if not config.get('constructed_fixture'):
            index=json.loads(Path(inputs['index']['path']).read_text())
            if state['histogram']!=index['sg1v']['histogram']:raise ValueError('SG1 instrument histogram differs from completed source')
        value=decision(state['histogram']);value['constructed_fixture']=bool(config.get('constructed_fixture'))
        write_json(output/'SCIENCE.json',value)
        return dict(status='complete',players=total,automatic_ch10_admission=False)
    except ck.YieldRequested:
        save();return dict(status='yielded',reason='Owner request at whole-player boundary',verification_prefix_credited=False)


def _execute(output,inputs,config):
    output=Path(output);bound=identity(inputs,config)
    if ck.sealed(output,bound,lambda:ck.require(output)):return dict(status='complete',sealed_output_reused=True)
    result=run(output,output,inputs,config)
    if result['status']=='complete':ck.seal(output,bound,['SCIENCE.json'],lambda:ck.require(output))
    return result


def _verify(output,inputs,config):
    output=Path(output)
    if not ck.sealed(output,identity(inputs,config),lambda:ck.require(output)):raise ValueError('Completed instrument output required')
    ordinal=1
    while (output/f'independent-{ordinal:04}').exists():ordinal+=1
    target=output/f'independent-{ordinal:04}'
    result=run(target,output,inputs,config,True)
    if result['status']!='complete':return result
    if json.loads((output/'SCIENCE.json').read_text())!=json.loads((target/'SCIENCE.json').read_text()):
        raise ValueError('Independent clock instrument differs')
    return dict(verified=True,complete_table_replay=True,independent_clock_arithmetic=True,automatic_ch10_admission=False)


def execute(output,inputs,config):return ck.guarded(_execute,output,inputs,config)
def verify(output,inputs,config):return ck.guarded(_verify,output,inputs,config)
