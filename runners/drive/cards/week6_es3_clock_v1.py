"""Prospective ES3 execute/fresh-replay dispatcher over reviewed UTC metadata.

DESIGN CHECK: same source, owner-fixed context calibration, full-person draws,
source exclusions before fit and no verification until every draw is complete.
The enclosing qualified Week6 ES runtime supplies native/resource/cost gates.
"""
from pathlib import Path
import time
try:
    from . import es_core_v1 as core, es_source_v1 as source, es_carry_v1 as carry
    from . import es_handler_v1 as io, week6_es_v1 as base, es_clock_v1 as clock, es_population_guard_v1 as population
except ImportError:
    import es_core_v1 as core
    import es_source_v1 as source
    import es_carry_v1 as carry
    import es_handler_v1 as io
    import week6_es_v1 as base
    import es_clock_v1 as clock
    import es_population_guard_v1 as population


def statistic(stats,panel,weights=None):
    result=carry.estimates(stats,weights)
    if panel=='primary':return carry.primary_statistic(stats,weights)
    if panel.startswith('curve_'):
        index=int(panel.removeprefix('curve_'));core.need(index in range(5),'unknown curve bin')
        value=result['five_bins'][index]
        if value['slopes'] is None:raise core.Unidentified('curve bin lacks within-person support')
        return value['slopes'][0]
    if panel.startswith('shape_'):
        index=int(panel.removeprefix('shape_'));core.need(index in range(5),'unknown shape bin')
        slopes=result['five_bins'][index]['slopes']
        if slopes is None:raise core.Unidentified('shape bin lacks within-person support')
        return [slopes[0]-slopes[1],slopes[0]-slopes[2]]
    raise ValueError('unknown prospective carry panel')


def person_join_dispatch(reactivity_by_person,carry_by_person,weights):
    """Exact declared descriptive join over frozen full-person scalar slopes.

    Caller binds member/source/measure provenance before creating these private
    dictionaries. Explicit complete overlap accounting is returned; IDs and
    individual slopes are never exported. There is no nearest-key matching.
    """
    a,b,coverage=clock.exact_person_join(reactivity_by_person,carry_by_person)
    result=carry.person_coupling(a,b,weights)
    return dict(result,join_coverage=coverage)


def operation(output,inputs,config,phase):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if phase=='verify':core.need((output/'execute'/'ENGINE_RESULT.json').is_file(),'complete execute required before fresh replay')
    intake,panel=base.load(inputs,config)
    core.need(panel['card']=='ES3' and panel['member'] in ('0056','0057'),'carry source differs')
    core.need(panel['draws']==2000 and type(panel['seed']) is int and panel['seed']>=0,'carry draw recipe differs')
    core.need(panel['source_layout_review']['clock_profile']==clock.UTC_PROFILE,'clock evidence not admitted')
    core.need(panel['calibration_scope']==clock.CALIBRATION,'calibration scope differs')
    name=panel['panel'];shape=name.startswith('shape_')
    core.need(name=='primary' or name in [f'{kind}_{i}' for kind in ('curve','shape') for i in range(5)],'unreviewed carry panel')
    core.need(set(config)=={'panel_config','max_new_draws','max_wall_seconds'},'carry operational config differs')
    quantum=config['max_new_draws'];wall=config['max_wall_seconds']
    core.need(type(quantum) is int and 1<=quantum<=2000 and type(wall) in (int,float) and 0<wall<=1500,'carry operational bounds differ')
    if phase=='execute':base.preserve_inherited_yield(output)
    started=time.monotonic();root=output/phase;root.mkdir(exist_ok=True)
    def guard():
        if (output/'YIELD_REQUEST.json').exists() or (output/'STOP_REQUEST.json').exists() or time.monotonic()-started>=wall:
            raise io.Pause('carry cooperative yield')
    files=[Path(m.__file__) for m in (core,source,carry,io,base,clock,population)]+[Path(__file__)]
    binding=io.digest({'panel':panel,'intake':intake,'code':{p.name:source.sha256(p) for p in files}})
    io.exclusive_json(root/'BINDING.json',{'binding':binding,'phase':phase})
    try:
        guard();frames=clock.selected_frames(inputs['source_path'],panel['source_pin'],panel['member'],'carry',guard)
        prepared=clock.prepare_carry(frames,panel['member'],('angry','sad','anxious') if shape else ('angry',),
            panel['missing_tokens'],clock.UTC_PROFILE,clock.CALIBRATION,guard)
        stats=prepared['stats'];io.exclusive_json(root/'SCOPE.json',prepared['source_counts'])
        point=None
        try:
            point=statistic(stats,name)
            population.require_population_interval(stats)
        except core.Unidentified as exc:
            result={'status':'UNSUPPORTED_IDENTIFICATION','reason':str(exc),'point':point,'binding':binding,'verified':False}
            io.exclusive_json(root/'ENGINE_RESULT.json',result)
        else:
            io.exclusive_json(root/'POINT.json',{'point':point})
            journal=io.DrawJournal(root/'draws',binding);calls=0
            def progress(row):
                nonlocal calls
                journal.append(row);calls+=1;guard()
                if calls>=quantum and row['draw']<1999:raise io.Pause('carry draw quantum')
            try:boot=population.bootstrap(stats,lambda w:statistic(stats,name,w),panel['seed'],progress=progress,prior=journal.rows)
            finally:journal.flush()
            result={'status':'ENGINE_COMPLETE','binding':binding,'point':point,'draw_count':2000,
                'draw_sha256':io.digest(journal.rows),'invalid_draws':boot['invalid_draws'],'interval':boot['interval'],
                'redraws':0,'valid_draw_only_interval':False,'verified':False}
            guard();io.exclusive_json(root/'ENGINE_RESULT.json',result)
    except io.Pause:return {'status':'yielded','verified':False,'operation':phase,'scientific_result_complete':False}
    if phase=='execute':return {'status':'computed','verified':False,'engine':result,'requires_fresh_replay':True}
    proof=io.compare_fresh_phases(output/'execute',output/'verify')
    return {'status':'verified','verified':True,'numerical_replay':proof,'native_proof_required_from_runtime':True}


def execute(output,inputs,config):return operation(output,inputs,config,'execute')
def verify(output,inputs,config):return operation(output,inputs,config,'verify')
