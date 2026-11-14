"""CP1 qualified-source consumer with sealed conversation and bootstrap blocks.

DESIGN CHECK: no text, provider, model or unreviewed marker substitution. A real
manual instrument receipt and full source replay precede a human analysis.
Conversation resampling preserves all pairs; every shuffled reply carries its
markers and edit count. Undefined slopes remain unsupported. See CP1_TWO_DAY_V1.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import os
import numpy as np
from . import week5_cp_statistics_v2 as stats
from . import week5_rf_cp_source_v1 as source
from . import week5_rf_cp_instrument_v1 as instrument
from . import week5_rf_cp_markers_v1 as markers

BANK_BLOCK=64
DRAW_BLOCK=20
MODULE='runners.drive.cards.week5_cp_analysis_v2'


class YieldRequested(Exception):
    pass


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def native(root, expected_module, expected_complete, required):
    root=Path(root); complete=read(root/'COMPLETE.json'); plan=read(root/'PLAN.json')
    verified=read(root/'VERIFIED.json')
    if source.sha(root/'COMPLETE.json')!=expected_complete:
        raise ValueError('Native completion identity changed')
    if complete.get('status')!='COMPLETE' or complete.get('fresh_process_verified') is not True or verified.get('verified') is not True:
        raise ValueError('Incomplete native qualification')
    if plan.get('module')!=expected_module:raise ValueError('Native producer identity changed')
    for name in ('PLAN.json','VERIFIED.json',*required):
        if complete['outputs'].get(name)!=source.sha(root/name):
            raise ValueError('Native output identity changed')
    return root/'output'


def load_source(inputs,config):
    # Revalidate the frozen manual decision's source, sample, identities and labels.
    summary,sample,labels=instrument.load(inputs,config)
    if config['family']!='CP1':raise ValueError('Wrong analysis family')
    gate_output=native(inputs['instrument_native_root'],
        'runners.drive.cards.week5_rf_cp_instrument_v1',config['instrument_native_complete_sha256'],
        ('output/INSTRUMENT.json',))
    gate=read(gate_output/'INSTRUMENT.json')
    expected=markers.instrument_gate(summary,sample,labels)
    if gate.get('admitted') is not True or gate.get('scientific_admission') is not False:
        raise ValueError('Lexical instrument did not pass its complete manual gate')
    if gate['details']!=expected['details'] or expected['admitted'] is not True:
        raise ValueError('Instrument decision does not match frozen manual labels')
    if gate['source_native_complete_sha256']!=config['source_native_complete_sha256'] or gate['annotations_sha256']!=config['annotations_sha256']:
        raise ValueError('Instrument/source/manual decision binding mismatch')
    output=Path(inputs['source_native_root'])/'output'
    completion=read(output/'SOURCE_COMPLETE.json')
    rows={}; source_refusals=0
    for name,pin in sorted(completion['blocks'].items()):
        if source.sha(output/name)!=pin:raise ValueError('Source block identity changed')
        for row in source.read_chunk(output/name)['rows']:
            if row.get('refused'):
                source_refusals+=1;continue
            if row['id'] in rows:raise ValueError('Duplicate source utterance')
            rows[row['id']]=row
    return rows,source_refusals


def pairs_from_rows(rows,view='all'):
    if view not in stats.VIEWS:raise ValueError('Unknown CP1 view')
    counts=Counter();groups=defaultdict(list)
    for key in sorted(rows):
        reply=rows[key];parent_key=reply['reply_to']
        if parent_key is None:counts['root']+=1;continue
        counts['reply_opportunities']+=1
        parent=rows.get(parent_key)
        if parent is None:counts['missing_parent']+=1;continue
        if parent['conversation']!=reply['conversation']:
            counts['different_conversation']+=1;continue
        if parent_key==key:counts['self_edge']+=1;continue
        if parent['speaker']==reply['speaker']:counts['same_speaker']+=1;continue
        if min(parent['markers']['tokens'],reply['markers']['tokens'])<10:
            counts['short_pair']+=1;continue
        role=f"admin-{int(parent['is_admin'])}{int(reply['is_admin'])}"
        if view!='all' and view!=role:counts['other_admin_role']+=1;continue
        def rate(item,family):return 100.0*item['markers']['counts'][family]/item['markers']['tokens']
        groups[reply['conversation']].append({'id':key,'parent_id':parent_key,
            'parent_speaker':parent['speaker'],'reply_speaker':reply['speaker'],
            'admin_role':role,'parent_assertion':rate(parent,'assertion'),
            'parent_warmth':rate(parent,'warmth'),'reply_warmth':rate(reply,'warmth'),
            'reply_deference':rate(reply,'deference'),'reply_assertion':rate(reply,'assertion'),
            'parent_edit_count':parent['edit_count'],'reply_edit_count':reply['edit_count']})
        counts['eligible_pairs']+=1
    errors=sum(counts[k] for k in ('missing_parent','different_conversation','self_edge'))
    counts['pair_join_errors']=errors
    counts['conversations']=len(groups)
    counts['variable_parent_assertion_conversations']=sum(
        len({r['parent_assertion'] for r in rs})>1 for rs in groups.values())
    counts['variable_reply_conversations']=sum(
        any(len({r[k] for r in rs})>1 for k in ('reply_deference','reply_assertion')) for rs in groups.values())
    result={'counts':dict(sorted(counts.items())),
        'pair_collection_gate':errors<=.01*counts['reply_opportunities'],
        'below_floor':len(groups)<20,'edit_count_clock_qualified':False,
        'admin_role_clock':'source utterance is-admin; speaker-level flag retained only in source',
        'within_conversation_exchange_possible':any(len(v)>1 for v in groups.values()),
        'record_kind':'run','theory_tags':['H15-T4'],'scientific_admission':False}
    return [(k,groups[k]) for k in sorted(groups)],result


def binding(inputs,config,groups,support):
    sample=config.get('whole_conversation_sample')
    if sample is not None:
        if not isinstance(sample,dict) or sample.get('authorization')!='measured_amendment_E' or not sample.get('cost_receipt_sha256'):
            raise ValueError('A sample needs a measured cost route and explicit frozen size')
        size=sample.get('size')
        if type(size) is not int or not 20<=size<=len(groups):raise ValueError('Sample below floor or outside population')
        path=Path(inputs['sample_cost_receipt'])
        if source.sha(path)!=sample['cost_receipt_sha256']:raise ValueError('Sample cost receipt changed')
        # This validates the explicit owner-reviewed frozen size; it does not infer it.
        selected=sorted(groups,key=lambda x:hashlib.sha256(('CP1|20261102|'+x[0]).encode()).digest())[:size]
        groups=sorted(selected)
    science={k:v for k,v in config.items() if k not in ('max_new_bank_blocks','max_new_draw_blocks')}
    value={'schema':'CP1-ANALYSIS-2','config':science,'module_sha256':source.sha(__file__),
        'statistics_sha256':source.sha(stats.__file__),'source_sha256':source.sha(source.__file__),
        'instrument_sha256':source.sha(instrument.__file__),'markers_sha256':source.sha(markers.__file__),
        'pairs_sha256':hashlib.sha256(source.canonical(groups)).hexdigest(),
        'support_sha256':hashlib.sha256(source.canonical(support)).hexdigest(),
        'population_conversations':support['counts']['conversations'],'selected_conversations':len(groups),
        'permutations':stats.PERMUTATIONS,'draws':stats.BOOTSTRAPS,'bank_block':BANK_BLOCK,'draw_block':DRAW_BLOCK,
        'null_seed':stats.NULL_SEED,'bootstrap_seed':stats.BOOT_SEED,'view':config.get('view','all')}
    return value,groups


def check_yield(output):
    output=Path(output)
    if any((base/'YIELD_REQUEST.json').exists() for base in (output,output.parent,output.parent.parent)):
        raise YieldRequested()


def write_bank(path,array,identity):
    path=Path(path);temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    if path.exists():raise ValueError('Unsealed bank output already exists')
    with temp.open('xb') as stream:np.save(stream,array,allow_pickle=False)
    os.replace(temp,path)
    source.write_equal(path.with_suffix('.seal.json'),dict(identity,sha256=source.sha(path),shape=list(array.shape)))


def load_bank(path,identity):
    seal=read(path.with_suffix('.seal.json'))
    if any(seal.get(k)!=v for k,v in identity.items()) or source.sha(path)!=seal['sha256']:
        raise ValueError('Sealed permutation-bank provenance changed')
    value=np.load(path,mmap_mode='r',allow_pickle=False)
    if list(value.shape)!=seal['shape'] or value.dtype!=np.float64:raise ValueError('Permutation bank shape or dtype changed')
    return value


def aggregate(banks,weights,check):
    # A batch of whole-conversation weighted sums. No model/draw changes for cost.
    totals=np.zeros((len(weights),201,34),dtype=np.float64);offset=0
    for array in banks:
        check();count=len(array)
        totals+=np.einsum('bc,crk->brk',weights[:,offset:offset+count],array,optimize=False)
        offset+=count
    if offset!=weights.shape[1]:raise ValueError('Incomplete conversation bank')
    return totals


def compare_metrics(expected,actual,tolerance=2e-8):
    for key in stats.KEYS:
        left,right=expected[key],actual[key]
        if (left is None)!=(right is None):raise ValueError('Independent support verdict differs')
        if left is not None and abs(left-right)>tolerance:raise ValueError('Independent mathematical replay differs')


def produce(output,inputs,config,reference=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    try:
        check_yield(output)
        rows,refusals=load_source(inputs,config)
        groups,support=pairs_from_rows(rows,config.get('view','all'));del rows
        support['source_refusals']=refusals;support['by_construction']=bool(config.get('constructed_fixture'))
        bind,groups=binding(inputs,config,groups,support)
        source.write_equal(output/'BINDING.json',bind);source.write_equal(output/'PAIR_SUPPORT.json',support)
        if not support['pair_collection_gate']:raise ValueError('Reply-pair collection refusals exceed one percent')
        pin=source.sha(output/'BINDING.json');banks=[];new=0
        for start in range(0,len(groups),BANK_BLOCK):
            check_yield(output);stop=min(start+BANK_BLOCK,len(groups));path=output/f'bank-{start:07d}.npy'
            identity={'binding_sha256':pin,'start':start,'stop':stop,
                'conversations_sha256':hashlib.sha256(source.canonical([g[0] for g in groups[start:stop]])).hexdigest()}
            if path.exists():value=load_bank(path,identity)
            else:
                if new>=config.get('max_new_bank_blocks',10**9):raise YieldRequested()
                value=np.stack([stats.conversation_bank(stats.pair_array(rs),key,bind['view'],lambda:check_yield(output))
                    for key,rs in groups[start:stop]])
                write_bank(path,value,identity);new+=1
                value=load_bank(path,identity)
            if value.shape!=(stop-start,201,34):raise ValueError('Bank population changed')
            banks.append(value)
        source.write_equal(output/'BANK_COMPLETE.json',{'binding_sha256':pin,
            'blocks':{p.name:source.sha(p) for p in sorted(output.glob('bank-*.npy'))}})
        if not groups:
            point={key:None for key in stats.KEYS};draws=[]
        else:
            total=aggregate(banks,np.ones((1,len(groups))),lambda:check_yield(output))[0]
            point=stats.evaluate(total)
            if reference:compare_metrics(point,stats.evaluate_reference(total))
            source.write_equal(output/'POINT.json',point);draws=[];new=0
            for start in range(0,stats.BOOTSTRAPS if len(groups)>=20 else 0,DRAW_BLOCK):
                check_yield(output);stop=min(start+DRAW_BLOCK,stats.BOOTSTRAPS);path=output/f'draw-{start:04d}.json'
                if path.exists():
                    block=read(path)
                    seal=read(path.with_suffix('.seal.json'))
                    if seal.get('sha256')!=source.sha(path):raise ValueError('Bootstrap block seal changed')
                    if block['binding_sha256']!=pin or block['indices']!=list(range(start,stop)):
                        raise ValueError('Global bootstrap indices or source changed')
                else:
                    if new>=config.get('max_new_draw_blocks',10**9):raise YieldRequested()
                    weights=np.stack([stats.draw_counts(len(groups),index,bind['view']) for index in range(start,stop)])
                    totals=aggregate(banks,weights,lambda:check_yield(output));values=[]
                    for total in totals:
                        check_yield(output);value=stats.evaluate(total)
                        if reference:compare_metrics(value,stats.evaluate_reference(total))
                        values.append(value)
                    block={'binding_sha256':pin,'indices':list(range(start,stop)),'values':values}
                    source.write_equal(path,block);source.write_equal(path.with_suffix('.seal.json'),{'sha256':source.sha(path)})
                    new+=1
                draws.extend(block['values'])
        result={'schema':'CP1-RESULT-2','view':bind['view'],'binding_sha256':pin,
            'population_conversations':bind['population_conversations'],'selected_conversations':len(groups),
            'pairs':sum(len(rs) for _,rs in groups),'sample_scoped':config.get('whole_conversation_sample') is not None,
            'uncertainty':stats.uncertainty(point,draws,below_floor=len(groups)<20),
            'case_check':{'within_conversation_exchange_possible':support['within_conversation_exchange_possible'],
                'variable_parent_assertion_conversations':support['counts'].get('variable_parent_assertion_conversations',0)},
            'point':point,'bootstrap_draws':len(draws),'permutations':stats.PERMUTATIONS,
            'record_kind':'claim' if bind['view']=='all' else 'texture','theory_tags':['H15-T4'],
            'by_construction':bool(config.get('constructed_fixture')),'edit_count_clock_qualified':False,
            'activation':[{'channel':'relative standing','setpoint':'unmeasured',
                'what_moved':'observed lexical assertion of parent','action':'lexical deference or assertion of reply',
                'observation':'reply relation, utterance admin flag, retrospective edit count',
                'says_nothing_about':'felt emotion, causal control, relationship-wide standing or mood'}],
            'scientific_admission':False,'export_ex6_authorized':False}
        if not support['within_conversation_exchange_possible'] or not support['counts'].get('variable_parent_assertion_conversations'):
            result['primary_case_status']='design_cannot_test_within_conversation_contrast'
        else:result['primary_case_status']='case_present_not_a_scientific_verdict'
        source.write_equal(output/'RESULT.json',result)
        source.write_equal(output/'ANALYSIS_COMPLETE.json',{'binding_sha256':pin,'result_sha256':source.sha(output/'RESULT.json'),
            'bank_complete_sha256':source.sha(output/'BANK_COMPLETE.json'),
            'draws':{p.name:source.sha(p) for p in sorted(output.glob('draw-*.json')) if '.seal.' not in p.name}})
        return {'status':'complete','scientific_admission':False,'result_sha256':source.sha(output/'RESULT.json')}
    except YieldRequested:
        return {'status':'yielded','reason':'sealed_CP1_checkpoint_or_requested_quantum','scientific_admission':False}


def execute(output,inputs,config):
    return produce(output,inputs,config)


def verify(output,inputs,config):
    output=Path(output)
    if not (output/'ANALYSIS_COMPLETE.json').exists():raise ValueError('Incomplete CP1 analysis cannot verify')
    replay=output/'independent-replay';result=produce(replay,inputs,config,reference=True)
    if result['status']=='yielded':return dict(result,verified=False)
    original=read(output/'ANALYSIS_COMPLETE.json')
    for name in ('BINDING.json','PAIR_SUPPORT.json','BANK_COMPLETE.json','RESULT.json','ANALYSIS_COMPLETE.json',*original['draws']):
        if (output/name).read_bytes()!=(replay/name).read_bytes():raise ValueError('Full CP1 independent replay differs')
    bank=read(output/'BANK_COMPLETE.json')
    for name,pin in bank['blocks'].items():
        if source.sha(output/name)!=pin or source.sha(replay/name)!=pin:raise ValueError('Full conversation permutation replay differs')
    return {'verified':True,'all_conversations_permutations_and_2000_global_draws_replayed':True,
        'independent_centered_slope_and_lstsq_checked':True,'scientific_admission':False}
