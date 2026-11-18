"""Additive ES1/ES2 population-guard kernel, called by counted runtime only.

DESIGN CHECK: unchanged source/code/config binding, whole-person resampling,
all invalid draws retained, separately completed fresh replay. Partial work is
PAUSED and cannot set verified=true. This is not a launcher or live admission.
Unknown ES-family runtime wiring remains an owner integration requirement.
"""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
if __package__:
    from . import es_core_v2 as core, es_source_v1 as source, es_secondary_v1 as secondary
else:
    import es_core_v2 as core
    import es_source_v1 as source
    import es_secondary_v1 as secondary


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def digest(value):return hashlib.sha256(canonical(value)).hexdigest()


def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def exclusive_json(path,value):
    """Crash-safe sealed output. Existing bytes must match; never overwrite."""
    path=Path(path);payload=canonical(value)+b'\n'
    if path.exists():
        core.need(path.read_bytes()==payload,'sealed output differs');return
    temp=path.with_name(path.name+'.pending')
    # A leftover partial temp is not a committed result and may be replaced.
    with temp.open('wb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
    os.replace(temp,path)


class Pause(Exception):pass


class DrawJournal:
    def __init__(self,root,binding):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.binding=binding;self.rows=[];self.pending=[];self.previous=None
        for path in sorted(self.root.glob('DRAW_*.json')):
            entry=read_json(path);start=len(self.rows)
            claimed=entry.pop('payload_sha256')
            core.need(digest(entry)==claimed,'draw payload hash differs')
            core.need(entry['binding']==binding and entry['previous']==self.previous,'draw chain binding differs')
            rows=entry['rows']
            core.need(1<=len(rows)<=25,'draw block size invalid')
            core.need(path.name==f'DRAW_{start:04d}_{start+len(rows):04d}.json','draw block name differs')
            for index,row in enumerate(rows,start):
                core.need(row.get('draw')==index and row.get('status') in ('VALID','INVALID'),'draw coverage differs')
                if row['status']=='VALID':
                    core.need(set(row)=={'draw','status','value'},'valid draw fields differ')
                    core.need(len(core.finite_array(row['value'],1))>0,'empty valid draw')
                else:core.need(set(row)=={'draw','status','reason'} and bool(row['reason']),'invalid draw reason absent')
            self.rows.extend(rows);self.previous=source.sha256(path)
        core.need(len(self.rows)<=2000,'excess draw coverage')

    def append(self,row):
        core.need(row['draw']==len(self.rows)+len(self.pending),'draw append order differs')
        self.pending.append(row)
        if len(self.pending)==25:self.flush()

    def flush(self):
        if not self.pending:return
        start=len(self.rows);entry={'binding':self.binding,'previous':self.previous,'rows':self.pending}
        entry['payload_sha256']=digest(entry)
        path=self.root/f'DRAW_{start:04d}_{start+len(self.pending):04d}.json'
        exclusive_json(path,entry);self.previous=source.sha256(path)
        self.rows.extend(self.pending);self.pending=[]


def panel_definition(member,card,panel):
    """Every supported panel has fixed original item membership and its own scope."""
    if card=='ES1':
        core.need(member in ('0056','0057'),'ES1 member differs')
        if panel=='usual_respected_moderation':
            return {'x':core.EVENTS,'y':('ashamed',),'kind':'moderation','missing':[],'minimum':10,'require_days':False}
        outcomes={'primary_ab':('ashamed','lonely'),'a':('ashamed',),'c':('angry',),
                  'd':('proud','relaxed'),'e':('envious',)}
        if panel.startswith('table_'):
            name=panel.removeprefix('table_');core.need(name in core.FEELINGS,'unknown table feeling')
            y=(name,);kind='table'
        else:core.need(panel in outcomes,'unresolved ES1 panel');y=outcomes[panel];kind='contrast'
        missing=sorted(set(y)&({'lonely','excluded'} if member=='0056' else set()))
        return {'x':core.EVENTS,'y':y,'kind':kind,'missing':missing,'require_days':False,'minimum':10}
    core.need(card=='ES2','ES3 actual source/runtime route is held separately')
    if member=='0062':
        core.need(panel=='anger_fear','0062 supports the approved anger/fear daily replication only')
        return {'x':source.DAILY_EVENTS,'y':source.DAILY_FEELINGS,'first':('angry_daily',),
                'second':('afraid_daily','worried_daily'),'kind':'dial','missing':[],
                'require_days':True,'minimum':10}
    core.need(member in ('0056','0057'),'ES2 member differs')
    if panel.startswith('week_prediction_'):
        family=panel.removeprefix('week_prediction_');core.need(family in core.FAMILIES,'unknown prediction family')
        y=core.FAMILIES[family]
        return {'x':core.NEGATIVE,'y':y,'kind':'week','missing':sorted(set(y)&({'lonely','excluded'} if member=='0056' else set())),
                'require_days':True,'minimum':10}
    floor_kind=None
    for candidate in ('occurrence','strength'):
        if panel.startswith('floor_'+candidate+'_'):
            floor_kind=candidate;panel=panel.removeprefix('floor_'+candidate+'_');break
    pair=panel.split('_');core.need(len(pair)==2 and pair[0]!=pair[1] and all(x in core.FAMILIES for x in pair),'unknown family pair')
    first,second=(core.FAMILIES[pair[0]],core.FAMILIES[pair[1]])
    missing=sorted(set(first+second)&({'lonely','excluded'} if member=='0056' else set()))
    return {'x':core.NEGATIVE,'y':first+second,'first':first,'second':second,'kind':'floor' if floor_kind else 'dial','floor_kind':floor_kind,
            'missing':missing,'require_days':True,'minimum':10}


def bind_config(config,intake):
    core.need(config['schema']=='ES_PANEL_PROSPECTIVE_V1','configuration schema differs')
    member,card,panel=(config[k] for k in ('member','card','panel'))
    definition=panel_definition(member,card,panel)
    core.need(config['source_pin']==intake['members'][member]['raw_ts_pin_from_receipt_only'],'source pin not retained member receipt')
    core.need(config['draws']==2000 and type(config['seed']) is int and config['seed']>=0,'draw recipe differs')
    core.need(config['pooled_scale']=='within_person_sample_N_minus_P','pooled scaling differs')
    core.need(config['invalid_draw_policy']=='retain_all_no_redraw_no_selective_interval','invalid draw policy differs')
    core.need(config['primary_scope']=='common_complete_case_panel','panel scope differs')
    core.need(config['source_layout_review']['status']=='OWNER_REVIEWED','source layout not yet reviewed')
    # That status is only an input declaration; enclosing runtime authenticates the
    # actual immutable source-admission, code/runtime, budget and drain receipts.
    core.need(type(config['missing_tokens']) is list,'source missing-token declaration absent')
    if definition['kind']=='week':
        core.need(config['source_layout_review'].get('original_day_wave_identity')=='OWNER_REVIEWED_UNAMBIGUOUS',
                  'first-week source day/wave identity not yet reviewed')
    return definition


def make_statistic(stats,definition):
    kind=definition['kind'];y=definition['y']
    if kind=='moderation':return lambda w:secondary.moderation(stats,w),['criticised_minus_ignored_interaction']
    if kind=='floor':return lambda w:secondary.floor_dial(stats,w),['latent_correlation']
    if kind=='week':return lambda w:secondary.week_prediction(stats,w)['reactivity_coefficient'],['week1_reactivity_to_week2_endorsements']
    if kind=='dial':
        fn=lambda w:core.dial(stats,definition['first'],definition['second'],w)
        return fn,['latent_correlation']
    if kind=='table':return lambda w:core.joint_fit(stats,w)[0].tolist(),list(core.EVENTS)
    names=list(core.es1_contrasts(core.joint_fit(stats),y))
    return lambda w:[core.es1_contrasts(core.joint_fit(stats,w),y)[k] for k in names],names


def run_phase(config,intake,source_path,output,phase,guard,max_new_draws=100):
    """One bounded serial quantum. Owner runtime supplies containment and limits.

    Enclosing runtime must enforce actual Job identity, charged inclusive budget,
    CPU/memory/output/freeze limits. guard() is its cooperative yield/deadline
    callback during source hashing, each read chunk and each draw; it does not
    replace those independent hard guards. Two phases use distinct fresh child
    processes and output directories. Neither phase alone grants verified=true.
    No person IDs, rows, individual slopes or prepared human arrays are written.
    """
    core.need(phase in ('execute','verify'),'phase differs')
    core.need(type(max_new_draws) is int and 1<=max_new_draws<=2000,'draw quantum differs')
    definition=bind_config(config,intake);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    code={p.name:source.sha256(p) for p in [Path(__file__),Path(core.__file__),Path(core.original.__file__),Path(source.__file__),Path(secondary.__file__)]}
    binding=digest({'config':config,'intake':intake,'code':code})
    exclusive_json(output/'BINDING.json',{'binding':binding,'config_sha256':digest(config),'code':code,'phase':phase})
    guard()
    if definition['missing']:
        result={'status':'UNSUPPORTED_SOURCE_ITEMS','missing':definition['missing'],'rows_opened':False,
                'binding':binding,'verified':False}
        exclusive_json(output/'ENGINE_RESULT.json',result)
        return result
    frames=source.selected_frames(source_path,config['source_pin'],config['member'],config['card'],config['missing_tokens'],guard)
    if config['member']=='0062':people,counts=source.daily_people(frames,config['missing_tokens'],config['daily_layout'])
    else:people,counts=source.interaction_people(frames,config['member'],config['missing_tokens'])
    kind=definition['kind']
    if kind=='moderation':stats=secondary.moderation_stats(people)
    elif kind=='floor':stats=secondary.floor_stats(people,definition['first'],definition['second'],definition['floor_kind'])
    elif kind=='week':stats=secondary.week_prediction_stats(people,definition['y'])
    else:stats=core.panel_stats(people,definition['x'],definition['y'],minimum=10,require_days=definition['require_days'])
    exclusive_json(output/'SCOPE.json',{'source':counts,'panel':stats.get('excluded',stats.get('counts')),'eligible_people':len(stats['people'])})
    support=core.population_interval_support(stats);names=[]
    try:
        statistic,names=make_statistic(stats,definition);point=statistic(None)
        if isinstance(point,dict) and point['status']=='UNSUPPORTED':
            result={'status':'UNSUPPORTED_RELIABILITY','point':point,'binding':binding,'verified':False}
            exclusive_json(output/'ENGINE_RESULT.json',result);return result
    except core.Unidentified as exc:
        result={'status':'UNSUPPORTED_IDENTIFICATION','reason':str(exc),'binding':binding,'verified':False}
        if not support['minimum_independent_population_met']:
            point_record={'point':None,'names':names,'point_defined':False}
            exclusive_json(output/'POINT.json',point_record)
            result.update(point_record,population_support=support,inference_supported=False,
                          interval=None,draw_count=0,redraws=0,valid_draw_only_interval=False,
                          interval_reason='population interval requires at least two independent people')
            guard()
        exclusive_json(output/'ENGINE_RESULT.json',result);return result
    if not support['minimum_independent_population_met']:
        point_record={'point':point,'names':names,'point_defined':True}
        exclusive_json(output/'POINT.json',point_record)
        result=dict(point_record,status='UNSUPPORTED_POPULATION_INTERVAL',binding=binding,
                    population_support=support,inference_supported=False,interval=None,
                    draw_count=0,redraws=0,valid_draw_only_interval=False,verified=False,
                    reason='population interval requires at least two independent people')
        guard();exclusive_json(output/'ENGINE_RESULT.json',result);return result
    exclusive_json(output/'POINT.json',{'point':point,'names':names})
    journal=DrawJournal(output/'draws',binding);started=len(journal.rows);calls=0
    def progress(row):
        nonlocal calls
        journal.append(row);calls+=1;guard()
        if calls>=max_new_draws and row['draw']<1999:raise Pause('bounded draw quantum complete')
    try:
        boot=core.bootstrap(stats,statistic,config['seed'],progress=progress,prior=journal.rows)
    except Pause:
        journal.flush()
        return {'status':'PAUSED','completed_draws':len(journal.rows),'new_draws':len(journal.rows)-started,
                'binding':binding,'verified':False}
    finally:journal.flush()
    core.need(len(journal.rows)==2000,'incomplete draws cannot finish')
    result={'status':'ENGINE_COMPLETE','binding':binding,'point':point,'names':names,'draw_count':2000,
            'draw_sha256':digest(journal.rows),'invalid_draws':boot['invalid_draws'],'interval':boot['interval'],
            'redraws':0,'valid_draw_only_interval':False,'verified':False}
    if definition['kind'] in ('dial','floor'):
        result['reading']='INTERVAL_UNAVAILABLE' if boot['interval'] is None else core.dial_reading(*boot['interval'][0])
    elif config['panel']=='primary_ab':result['both_point_contrasts_at_bar']=all(x>=.05 for x in point)
    guard();exclusive_json(output/'ENGINE_RESULT.json',result);return result


def compare_fresh_phases(execute,verify):
    """Called only after runtime independently proves BOTH children exited.

    This numerical comparison does not authenticate native identities or publish
    COMPLETE.json. The enclosing qualified runtime must do those checks itself.
    """
    roots=[Path(execute),Path(verify)];bindings=[read_json(p/'BINDING.json') for p in roots]
    core.need(bindings[0]['phase']=='execute' and bindings[1]['phase']=='verify','fresh phase roles differ')
    core.need(bindings[0]['binding']==bindings[1]['binding'],'fresh replay binding differs')
    results=[read_json(p/'ENGINE_RESULT.json') for p in roots]
    core.need(results[0]==results[1],'fresh replay result mismatch')
    result=results[0];core.need(result['verified'] is False,'kernel must not self-verify')
    core.need(result['binding']==bindings[0]['binding'],'terminal result binding differs')
    if result['status']!='UNSUPPORTED_SOURCE_ITEMS':
        core.need(read_json(roots[0]/'SCOPE.json')==read_json(roots[1]/'SCOPE.json'),'source coverage replay differs')
    if 'population_support' in result:
        support=result['population_support']
        n=support.get('eligible_people')
        core.need(type(n) is int and 0<=n<2 and support=={
            'eligible_people':n,'minimum_independent_people':2,'minimum_independent_population_met':False},
            'unsupported population support differs')
        core.need(result['status'] in ('UNSUPPORTED_POPULATION_INTERVAL','UNSUPPORTED_IDENTIFICATION')
                  and result.get('inference_supported') is False and result.get('interval') is None
                  and result.get('draw_count')==0 and result.get('redraws')==0
                  and result.get('valid_draw_only_interval') is False,'unsupported population inference differs')
        expected_defined=result['status']=='UNSUPPORTED_POPULATION_INTERVAL'
        core.need(result.get('point_defined') is expected_defined,'unsupported point definition differs')
        if not expected_defined:core.need(result['point'] is None,'undefined population point differs')
        for root in roots:
            core.need(read_json(root/'SCOPE.json')['eligible_people']==n,'population support differs from scope')
            core.need(read_json(root/'POINT.json')=={k:result[k] for k in ('point','names','point_defined')},
                      'population point receipt differs')
            core.need(not (root/'draws').exists(),'unsupported population must not have draw journal')
    elif result['status']=='UNSUPPORTED_POPULATION_INTERVAL':
        raise ValueError('unsupported population support absent')
    if result['status']=='ENGINE_COMPLETE':
        for root in roots:
            core.need(read_json(root/'POINT.json')=={k:result[k] for k in ('point','names')},
                      'complete point receipt differs')
            journal=DrawJournal(root/'draws',result['binding'])
            core.need(len(journal.rows)==2000 and digest(journal.rows)==result['draw_sha256'],'replay draw proof differs')
    else:core.need(result['status'] in ('UNSUPPORTED_SOURCE_ITEMS','UNSUPPORTED_RELIABILITY','UNSUPPORTED_IDENTIFICATION','UNSUPPORTED_POPULATION_INTERVAL'),'unfinished engine result')
    return {'status':'NUMERICAL_REPLAY_MATCH','binding':result['binding'],'engine_result_sha256':digest(result),
            'native_exit_and_containment_proof':'REQUIRED_FROM_ENCLOSING_RUNTIME','verified':False}
