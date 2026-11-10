"""TR5 timed survival using R1 physical insertions and unchanged menu matches.

DESIGN CHECK: LESSONS 2--5/CONTROLS, 2026-11-07. Full transforms, not
raw insert lengths, define accepted atoms. Future deletions cannot alter earlier
run bins. Only uniquely canonical menu associations feed the original matcher;
noncanonical physical records remain separate and never overwrite each other.
"""
from types import FunctionType,SimpleNamespace
from runners.stage9.coauthor import units,text_of,delta_ops
from . import week3_trust_inputs as original
from . import week5_bk_outcome_source as shared


def history(events,timeline,canonical,certified):
    proofs={s['origin']:s for s in certified}
    if len(proofs)!=len(certified):raise ValueError('Duplicate physical insertion')
    doc=units(events[0]['currentDoc']);owners=[None]*len(doc);records={};serial=0
    for ordinal,event in enumerate(events):
        ops=delta_ops(event.get('textDelta'))
        if not ops:continue
        user=event.get('eventSource')=='user';before=text_of(doc);prior=owners
        out=[];labels=[];position=0;removed=set();first={}
        for op in ops:
            if 'insert' in op:
                for char in op['insert']:out.extend(units(char));labels.extend([None]*len(units(char)))
            else:
                n=op.get('retain',op.get('delete'))
                if type(n) is not int or n<0 or position+n>len(doc):raise ValueError('Invalid timed survival UTF16 boundary')
                if 'retain' in op:out.extend(doc[position:position+n]);labels.extend(owners[position:position+n])
                else:
                    gone=set(owners[position:position+n])-{None};removed|=gone
                    for tag in gone:first.setdefault(tag[0],len(out))
                position+=n
        out.extend(doc[position:]);labels.extend(owners[position:]);doc=out;owners=labels
        if ordinal in proofs:
            proof=proofs[ordinal]
            if user or not before.endswith('\n') or text_of(doc)!=before[:-1]+proof['text']+'\n':raise ValueError('R1 physical append disagrees with raw transform')
            newlabels=[];atoms=[]
            for char in proof['text']:
                tag=(ordinal,serial);serial+=1;atoms.append(tag);newlabels.extend([tag]*len(units(char)))
            if len(atoms)!=proof['original_codepoints']:raise ValueError('R1 original atom count differs')
            owners=prior[:-1]+newlabels+prior[-1:]
            if len(owners)!=len(doc):raise ValueError('Timed semantic provenance length differs')
            records[ordinal]=dict(proof,retention=[[ordinal,len(atoms)]],removed=set(),failure_position=None,failure_removed=None)
        if user:
            for key in {tag[0] for tag in removed}:
                row=records[key];row['removed'].update(tag for tag in removed if tag[0]==key)
                row['retention'].append([ordinal,row['original_codepoints']-len(row['removed'])])
                if ordinal==row['failure_ordinal']:row['failure_position']=first[key];row['failure_removed']=len(row['removed'])
    if text_of(doc)!=timeline['final_document'] or set(records)!=set(proofs):raise ValueError('Timed survival complete source coverage differs')
    projected={}
    for physical,row in records.items():
        if row['retention'][-1][1]!=row['retained_codepoints']:raise ValueError('Timed survival differs from complete R1 ledger')
        row.pop('removed');row['physical_origin']=physical
        # Only canonical association enters original menu-keyed run history.
        # Repeated, noncanonical menu origins stay physically distinct.
        key=row['menu_origin'] if row['canonical'] else 'physical:'+str(physical)
        if key in projected:raise ValueError('Canonical menu maps to multiple accepted insertions')
        if row['canonical']:row['origin']=row['menu_origin']
        projected[key]=row
    return projected


def prepare(args,spans,card):
    fn=FunctionType(original.prepare_session.__code__,dict(original.__dict__,history=lambda e,t,c:history(e,t,c,spans)))
    value=fn(**args)
    value['r1_audit']=dict(physical_insertions=len(spans),canonical=sum(s['canonical'] for s in spans),comparator_unsupported=sum(not s['comparator_supported'] for s in spans))
    return value


def configuration(config):
    if config.get('card')!='TR5-inputs':raise ValueError('TR5 source card required')
    value=shared.configuration(dict(config,card='FR1-inputs'));value['card']='TR5-inputs';return value


def load(inputs,config):
    configuration(config)
    return shared.load(inputs,dict(config,card='FR1-inputs'))


def run(output,inputs,config,verifying=False):
    fn=FunctionType(shared.run.__code__,dict(shared.__dict__,configuration=configuration,load=load,prepare=prepare,
        fr=SimpleNamespace(assemble=original.assemble)))
    return fn(output,inputs,config,verifying)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
