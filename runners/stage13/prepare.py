"""Freeze source capsules and explicitly reviewed complete-block declarations.

DESIGN CHECK: LESSONS 3-5. NULL: changed sources or reused names refuse. ALTERNATIVE:
source IDs determine blocks before predictions; reserve producers need a sealed
selection. The explicit roster is not an automatic translator of the TODO file.
"""
from pathlib import Path
import argparse
from .common import RAW,REPO,read,freeze,filehash,digest
from .queue import topological


def capsule(raw,name):
    root=raw/'source_bundles'/name
    files=list((REPO/'runners/stage13').glob('*.py'))
    pins={}
    for p in files:
        dest=root/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.read_bytes()!=p.read_bytes():raise ValueError('capsule changed')
        if not dest.exists():dest.write_bytes(p.read_bytes())
        pins[str(dest.relative_to(REPO))]=filehash(dest)
    init=root/'runners/__init__.py'
    if not init.exists():init.write_text('',encoding='utf-8')
    pins[str(init.relative_to(REPO))]=filehash(init)
    for folder in ('runners/stage9','runners/stage11','runners/stage11_1','runners/stage12'):
        for p in (REPO/folder).glob('*.py'):pins[str(p.relative_to(REPO))]=filehash(p)
    for p in ('runners/run_queue.py','runners/queue_status.py','soundingline/completion.py','tools/codex_common.py'):
        if (REPO/p).exists():pins[p]=filehash(REPO/p)
    return str(root.relative_to(raw)),pins


def build(raw=RAW,name='core-v1',admission_only=False):
    root,pins=capsule(raw,name);cards=[]
    def add(id,action,args,requires=(),resource='cpu',wall=3600,kind='producer',gates=()):
        inputs={}
        for key in ('rows','training','development'):
            path=args.get(key)
            if path:inputs[path]=filehash(raw/path)
        for path in args.get('sources',{}).values():inputs[path]=filehash(raw/path)
        extra={}
        if action.startswith('legacy-'):
            from .legacy import OLD
            family={'aries':'LP15','revision':'LP21-revision','realization':'LP18'}[action[7:]]
            for p in sorted((OLD/'jobs').glob(family+'-[0-9][0-9][0-9]-a2/*.json')):extra[str(p.relative_to(REPO))]=filehash(p)
            if action=='legacy-aries':
                p=OLD/'inputs/ARIES-compile/SOURCE_ROWS.json';extra[str(p.relative_to(REPO))]=filehash(p)
        c=dict(id=id,action=action,args=args,requires=list(requires),gates=list(gates),resource=resource,wall_seconds=wall,kind=kind,
            source_pins=dict(pins,**extra),input_pins=inputs,question=action+' under the fixed Stage 13 evidence and deadline contract')
        cards.append(c);return id
    e5=add(name+'-e5-admission','detector-admission',dict(arm='e5'),wall=600,kind='infrastructure')
    lm=add(name+'-lm-admission','detector-admission',dict(arm='gpt2-medium-logrank'),wall=900,kind='infrastructure')
    if not admission_only:
        human_sources={p:f'sources/coauthor-v3-{p}.json' for p in ('train','development','calibration','reserve')}
        add(name+'-B-schola-coupling','schola-coupling',dict(rows='sources/schola-retrospective.json'),wall=3600,kind='consumer')
        for diagnostic in ('aries','revision','realization'):
            add(name+'-D-'+diagnostic,'legacy-'+diagnostic,{},wall=600,kind='consumer')
        rg=add(name+'-readout-admission','readout-admission',{},wall=1800,kind='infrastructure')
        rb=[]
        for part in ('calibration','reserve'):
            rows=sorted(read(raw/human_sources[part]),key=lambda r:digest(['paired-readout',r['key']]))[:8]
            rel=f'blocks/{name}/readout-{part}.json';freeze(raw/rel,rows)
            rb.append(add(name+'-readout-'+part,'readout-batch',dict(rows=rel),requires=[rg],gates=[rg],wall=10800))
        add(name+'-readout-summary','readout-summary',dict(blocks=rb),requires=rb,wall=600,kind='consumer')
        bfit=add(name+'-B-fit','reconstruction-fit',dict(rows=human_sources['train']),wall=600,kind='fit')
        # CoAuthor has one connected group per partition. Fixed-source descriptive
        # blocks remain useful; no population bootstrap or confirmatory claim.
        bblocks=[];cblocks=[];ccal=[]
        for part in ('calibration','development','reserve'):
            rows=read(raw/human_sources[part])
            for i in range(0,len(rows),16):
                rel=f'blocks/{name}/human-{part}-{i//16:03d}.json';freeze(raw/rel,rows[i:i+16])
                b=add(f'{name}-B-{part}-{i//16:03d}','reconstruction-batch',dict(rows=rel,model=bfit),requires=[bfit],wall=3600);bblocks.append(b)
                # Outcome-independent source-hash cap for the costlier readout study.
                selected=sorted(rows[i:i+16],key=lambda r:digest(['C-reader',r['key']]))[:4]
                cr=f'blocks/{name}/context-{part}-{i//16:03d}.json';freeze(raw/cr,selected)
                c=add(f'{name}-C-{part}-{i//16:03d}','context-batch',dict(rows=cr,training=human_sources['train']),requires=[lm],gates=[lm],wall=10800)
                (ccal if part=='calibration' else cblocks).append(c)
        add(name+'-B-summary','reconstruction-summary',dict(blocks=bblocks),requires=bblocks,wall=1800,kind='consumer')
        add(name+'-C-summary','context-summary',dict(blocks=cblocks,calibration=ccal),requires=cblocks+ccal,wall=1800,kind='consumer')
        blocks={};sources={p:f'sources/opai-{p}.json' for p in ('train','development','calibration','reserve')}
        loc=add(name+'-located-fit','located-fit',dict(rows=sources['train']),wall=10800,kind='fit')
        for part in sources:
            rows=read(raw/sources[part]);blocks[part]=[]
            for i in range(0,len(rows),256):
                rel=f'blocks/{name}/opai-{part}-{i//256:03d}.json';freeze(raw/rel,rows[i:i+256])
                deps=[name+'-A-selection'] if part=='reserve' else []
                for arm,gate in [('e5',e5),('gpt2-medium-logrank',lm)]:
                    id=f'{name}-A-{part}-{i//256:03d}-{arm}'
                    add(id,'detector-batch',dict(rows=rel,arm=arm),requires=[gate]+deps,gates=[gate],wall=3600);blocks[part].append(id)
        required=[loc]+[x for part in ('train','development','calibration') for x in blocks[part]]
        add(name+'-A-selection','detector-select',dict(located=loc,sources={p:sources[p] for p in ('train','development','calibration')},blocks={p:blocks[p] for p in ('train','development','calibration')}),requires=required,wall=3600,kind='consumer')
        add(name+'-A-reserve-summary','detector-evaluate',dict(located=loc,rows=sources['reserve'],blocks=blocks['reserve'],selection=name+'-A-selection'),requires=blocks['reserve']+[name+'-A-selection'],wall=3600,kind='consumer')
        add(name+'-roberta-training','roberta-training',dict(training=sources['train'],development=sources['development']),resource='gpu',wall=14400,kind='fit')
        add(name+'-roberta-evaluate','roberta-evaluate',dict(training_job=name+'-roberta-training',sources={p:sources[p] for p in ('development','calibration','reserve')}),requires=[name+'-roberta-training'],resource='gpu',wall=14400,kind='consumer')
        from .gpu import request
        def qeligible(row):
            try:
                for view in ('A','B','C','D'):
                    for arm in ('direct','joint','without-goals','without-execution','equal-direct'):request(row['views'][view],arm)
                return True
            except ValueError:return False
        qpopulation={part:[r for r in read(raw/human_sources[part]) if qeligible(r)] for part in ('development','calibration','reserve')}
        freeze(raw/f'blocks/{name}/qwen-interface-census.json',{p:dict(total=len(read(raw/human_sources[p])),eligible=len(rs),excluded_keys=[r['key'] for r in read(raw/human_sources[p]) if not qeligible(r)],reason='full evidence exceeds conservative native-token input cap') for p,rs in qpopulation.items()})
        qrows=sorted([r for r in read(raw/human_sources['train']) if qeligible(r)],key=lambda r:digest(['qwen-admission',r['key']]))[:3]
        from .reconstruction import admission_fixture
        qrows=[admission_fixture()]+qrows
        qpath=f'blocks/{name}/qwen-admission.json';freeze(raw/qpath,qrows)
        qgate=add(name+'-qwen-admission','qwen-admission',dict(rows=qpath,model=bfit,views=['D'],arms=['direct']),requires=[bfit],resource='gpu',wall=3600,kind='infrastructure')
        qblocks=[]
        for part in ('calibration','reserve'):
            rows=sorted(qpopulation[part],key=lambda r:digest(['Q-core',r['key']]))[:12 if part=='calibration' else 24]
            for i in range(0,len(rows),4):
                rel=f'blocks/{name}/qwen-{part}-{i//4:03d}.json';freeze(raw/rel,rows[i:i+4])
                q=add(f'{name}-Q-{part}-{i//4:03d}','qwen-batch',dict(rows=rel,model=bfit,views=['A','B','C','D']),requires=[qgate,bfit],gates=[qgate],resource='gpu',wall=14400);qblocks.append(q)
        add(name+'-Q-summary','qwen-summary',dict(blocks=qblocks),requires=qblocks+[qgate],gates=[qgate],wall=1800,kind='consumer')
    # Dependency sorting makes reserve selection a predecessor even though declared later.
    lead=[c for c in cards if c['id'] in (name+'-e5-admission',name+'-lm-admission') or '-A-train-000-' in c['id'] or '-A-train-001-' in c['id']]
    cards=topological(lead+[c for c in cards if c not in lead])
    for c in cards:freeze(raw/'manifests'/(c['id']+'.json'),c)
    plan=dict(id=name,cards=[c['id'] for c in cards],manifest_hashes={c['id']:filehash(raw/'manifests'/(c['id']+'.json')) for c in cards},
        source_pins=pins,source_capsule=root,contract_sha256=filehash(raw/'CONTRACT.json'),resource_policy='serial; CPU one thread; GPU held in Gear 1',
        scientific_close='one final packet; queue pass completion is not campaign completion')
    freeze(raw/'plans'/(name+'.json'),plan);return plan



def extension(raw=RAW,core='core-v1',name='reserve-extension-v1'):
    parent=read(raw/'plans'/(core+'.json'));cards=[];rows=read(raw/'sources/opai-conditional-reserve.json');pins=parent['source_pins']
    for i in range(0,len(rows),256):
        rel=f'blocks/{name}/opai-{i//256:03d}.json';freeze(raw/rel,rows[i:i+256])
        for arm,gate in [('e5',core+'-e5-admission'),('gpt2-medium-logrank',core+'-lm-admission')]:
            cards.append(dict(id=f'{name}-{i//256:03d}-{arm}',action='detector-batch',args=dict(rows=rel,arm=arm),requires=[gate,core+'-A-reserve-summary'],gates=[gate],resource='cpu',wall_seconds=3600,kind='producer',source_pins=pins,input_pins={rel:filehash(raw/rel)},question='Predeclared additional untouched source components under fixed selection; run only with full-family time admission'))
    ids=[c['id'] for c in cards]
    rel='sources/opai-conditional-reserve.json'
    cards.append(dict(id=name+'-summary',action='detector-evaluate',args=dict(located=core+'-located-fit',rows=rel,blocks=ids,selection=core+'-A-selection'),requires=ids+[core+'-A-selection',core+'-located-fit'],gates=[],resource='cpu',wall_seconds=3600,kind='consumer',source_pins=pins,input_pins={rel:filehash(raw/rel)},question='Whole additional source replication under unchanged models, margins and calibration; no sign-based stopping'))
    for c in cards:freeze(raw/'manifests'/(c['id']+'.json'),c)
    plan=dict(id=name,cards=[c['id'] for c in cards],manifest_hashes={c['id']:filehash(raw/'manifests'/(c['id']+'.json')) for c in cards},source_pins=pins,source_capsule=parent['source_capsule'],contract_sha256=parent['contract_sha256'],conditional=True,requires_operator_time_admission=True,minimum_whole_family_seconds=45*3600,admission_basis='re-estimate from actual whole core rates at health checkpoint; no new authorization needed within Gear 1 and fixed contract')
    freeze(raw/'plans'/(name+'.json'),plan);return plan

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--name',default='core-v1');p.add_argument('--admission-only',action='store_true');a=p.parse_args();plan=build(name=a.name,admission_only=a.admission_only);print('prepared',len(plan['cards']),'cards')
