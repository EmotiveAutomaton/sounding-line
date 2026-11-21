"""Three fixed wave-two jobs. All memberships remain inside the sealed process."""
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import defaultdict
import signal
import analysis_v1 as analysis
import aggregate_register_v1 as register
import mi_source_contract_v1 as contract
import argument_bank,argument_panel,daily_bank
from sealed_io_v1 import selected_columns
from science_entry import inspect_tables,read_available,MAX_PRIVATE_BYTES,MAX_SECONDS
from table_support import required_columns,supported_columns,EXTRAS
from joined_source import take_snapshot,resolve_wave
from family_draws import family_index
from panels import plan
from bm_numeric import numerical_outputs
from independent_release import Entry,decide,MISSING,BELOW
from week6_sealed_support_v1 import write_tables,SealedFailure


def original(paths,measured,selections):
    tables={'M2':read_available(paths,selections,measured)}
    return tables


def run_layout(mount,source_map,job,out):
    if job not in ('main','nt1','d5') or resolve_wave(mount,source_map)!='M2':raise SealedFailure(11,'Required joined source unavailable')
    size=sum(x['bytes'] for x in source_map['M2'].values())
    if size>MAX_PRIVATE_BYTES:raise SealedFailure(14,'Source exceeds read limit')
    with TemporaryDirectory(prefix='bm-') as tmp:
        wave,paths=take_snapshot(mount,Path(tmp),source_map,size)
        if wave!='M2' or set(paths)!={'diary','survey'}:raise SealedFailure(11,'Joined source roles missing')
        selections={role:set(selected_columns('M2_'+part,contract.fields)) for role,part in [('diary','P2'),('survey','P1')]}
        for branch in EXTRAS:
            for role,cols in required_columns('M2',branch).items():selections[role].update(cols)
        selections={k:sorted(v) for k,v in selections.items()}
        _,measured,sources=inspect_tables({'M2':paths},{'M2':selections},'M2')
        source=sources['M2']['diary']
        if 'M2ID' not in measured['M2']['diary']:
            import pyreadstat
            try:
                id_frame,_=pyreadstat.read_sav(str(paths['diary']),usecols=['M2ID'])
            except (OSError,ValueError,RuntimeError,pyreadstat.ReadstatError):
                raise SealedFailure(11,'Diary identification unavailable') from None
            if 'M2ID' in id_frame and id_frame.empty:raise SealedFailure(12,'Empty identified diary')
            raise SealedFailure(11,'Diary identification unavailable')
        if len(source)<11:raise SealedFailure(12,'Fewer than eleven diary people')
        enabled=set(supported_columns(measured,'M2'))
        branches=tuple(k for k in register.BRANCHES if k in enabled)
        branches_all=(*register.BRANCHES,'NT1.s','D5.s','counts')
        ids={k:i for i,k in enumerate(branches_all,1)}
        catalog={k:None for k in branches_all}
        native={}
        def group(k,tag,people,related=()):
            if catalog[k] is None:catalog[k]=[]
            people=frozenset(people)
            marker=len(catalog[k])+1
            catalog[k].append(Entry(dict(row_key=marker,n=len(people)),people,tuple(frozenset(g) for g in related)))
            native[k,tag]=marker
        # Construct the same cross-job roster before fitting any selected branch.
        counts={}
        if branches:
            raw=original(paths,measured['M2'],selections);replay=original(paths,measured['M2'],selections)
            panels,counts=plan(raw,'M2',False,branches,measured)
            check,other_counts=plan(replay,'M2',True,branches,measured)
            if counts!=other_counts:raise SealedFailure(14,'Population replay mismatch')
            # The original registered counts table includes only groups with
            # at least eleven people. Its numeric codes and memberships survive
            # the subsequent cross-table complement review unchanged.
            catalog['counts']=[]
            for ix,name in enumerate(register.count_names(),1):
                if name in counts and len(counts[name])>=11:group('counts',ix,counts[name])
        results={}
        for k in branches:
            people,other=panels[k],check[k]
            if [p['id'] for p in people]!=[p['id'] for p in other]:raise SealedFailure(14,'Roster replay differs')
            contributors,required=analysis.groups_for(people,k)
            if (contributors,required)!=analysis.groups_for(other,k):raise SealedFailure(14,'Membership replay differs')
            actual=contributors.intersection(*required)
            results[k]=(people,other,contributors,required)
            for ix in range(1,len(register.columns(k))+1):group(k,ix,actual)
        daily=arg=arg_data=None
        if 'NT1.s' in enabled:
            daily=daily_bank.plan(paths);group('NT1.s','exposed',daily['exposed'])
            if daily['panel'] is not None:
                group('NT1.s','model',daily['panel']['ids'])
        if 'D5.s' in enabled:
            arg=argument_panel.support_plan(paths)
            support,_=argument_panel.support_summary(arg)
            for j,g in enumerate(support,1):group('D5.s',('support',j),g)
            arg_data=argument_panel.outcome_plan(paths,arg)
            cohorts,margins=argument_bank.contributors(arg_data[0])
            for j,g in cohorts.items():group('D5.s',('comparison',j),g,margins if j==argument_bank.ALL_REPORTS else ())
            for j,g in enumerate(margins,1):group('D5.s',('margin',j),g)
        selection=[(ids[k],'t'+str(ids[k]),catalog[k]) for k in branches_all]
        survey=sources['M2']['survey']
        approved,status=decide(selection,source,[survey] if len(survey)>=11 else [])
        def permits(k,tag):
            return native.get((k,tag)) in {v['row_key'] for v in approved.get('t'+str(ids[k]),())}
        families=family_index(paths['survey']) if 'M2FAMNUM' in measured['M2']['survey'] else None
        independent=family_index(paths['survey']) if families is not None else None
        if independent!=families:raise SealedFailure(14,'Family linkage replay differs')
        data=defaultdict(list)
        selected=(*register.BRANCHES,'counts') if job=='main' else ('NT1.s',) if job=='nt1' else ('D5.s',)
        def send(k,name,tag,row):
            if permits(k,tag):
                entry=catalog[k][native[k,tag]-1]
                if row['n']!=len(entry.people):raise SealedFailure(14,'Numeric result lost its roster')
                data[name].append(row)
        if job=='main':
            for ix,name in enumerate(register.count_names(),1):
                if name in counts:send('counts','counts',ix,dict(count_group=ix,n=len(counts[name])))
            keep={k:v for k,v in results.items() if 't'+str(ids[k]) in approved}
            if keep:
                for name,rows in numerical_outputs(keep,families,independent).items():
                    for row in rows:
                        k=register.BRANCHES[row['branch']-1]
                        send(k,name,row['parameter'],row)
        elif job=='nt1' and 't'+str(ids['NT1.s']) in approved:
            for name,rows in daily_bank.run(daily,families,independent).items():
                for row in rows:send('NT1.s',name,'exposed' if name=='daily_exposure' else 'model',row)
        elif job=='d5' and 't'+str(ids['D5.s']) in approved:
            for name,rows in argument_bank.run(arg,*arg_data,families,independent).items():
                for row in rows:
                    if name=='argument_support':tag=('support',row['group'])
                    elif name=='argument_report_people':tag=('margin',row['resolution'])
                    elif name=='argument_reading':
                        if not all(permits('D5.s',k) for k in [('support',1),('comparison',1),('comparison',2)]):continue
                        tag=('comparison',1)
                    else:tag=('comparison',row['comparison'])
                    send('D5.s',name,tag,row)
        data['table_status']=[s for s in status if s['table'] in {ids[k] for k in selected}]
        write_tables(out,data)


def main(source_map,job):
    import os,warnings
    if os.name=='posix':
        import resource
        resource.setrlimit(resource.RLIMIT_CPU,(MAX_SECONDS,MAX_SECONDS));signal.alarm(MAX_SECONDS)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        try:run_layout(Path('/data'),source_map,job,Path('/out'));return 0
        except SealedFailure as exc:return exc.code
        except Exception:return 14

