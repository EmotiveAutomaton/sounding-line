"""Write a reviewed Week 8 finding through its scientific and operational records.

The caller supplies reviewed public wording and a table already cleared for release.
Raw source data and undisclosed cells never enter this module.
"""
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runners.stage14.common import atomic, filehash, read
from tools import record_views as views

STAGE = ROOT/'results/phase_2_4_stage_15'
PUBLIC = STAGE/'WEEK8'
STATE = ROOT/'.agent-state/drive-20261127/week8'


def write(path, text):
    data = text.encode('utf8')
    if not path.exists() or path.read_bytes()!=data:
        views.atomic(path, data)


def add(path, key, text, *, front=False, heading=None):
    old = path.read_text('utf8') if path.exists() else (heading or '')+'\n'
    if key in old:
        return
    if front:
        first, tail = old.split('\n',1)
        result = first+'\n\n'+text+'\n'
        if tail.strip():
            result += '\n'+tail.lstrip('\n')
    else:
        separator='\n' if text.startswith('|') and old.rstrip().endswith('|') else '\n\n'
        result = old.rstrip()+separator+text+'\n'
    write(path,result)


def rebind(ledger):
    cache = {}
    references = list(views.bindings(ledger))
    for ref in references:
        name = ref['file']
        if name not in cache:
            p=ROOT/name
            lines=p.read_text('utf8').splitlines()
            lookup={}
            for i,line in enumerate(lines,1):
                if line.startswith('#'):
                    lookup.setdefault(line,[]).append(i)
            cache[name] = (lines,lookup,filehash(p))
        lines,lookup,digest = cache[name]
        at=ref['line']
        anchor=ref['anchor']
        if not 0<at<=len(lines) or anchor not in lines[at-1]:
            hits=lookup.get(anchor) or [i for i,line in enumerate(lines,1) if anchor in line]
            if len(hits)!=1:
                raise ValueError('Ambiguous evidence anchor in '+name+': '+anchor)
            ref['line']=hits[0]
        ref['source_sha256']=digest
    ledger['source_anchors_checked']=len(references)


def land(*, card, stem, title, body, receipt, evidence, theory_anchor, theory_note,
         after_anchor, afterword, opposition, outcome, rival, scope, next_step, return_line, progress=None):
    PUBLIC.mkdir(parents=True,exist_ok=True)
    ident=evidence['id']
    if set(evidence)!=set('id date question data estimate interval bar verdict limit claims family'.split()):
        raise ValueError('Incomplete evidence ledger record')
    stamp=receipt['terminal_at']
    topic=', '.join(evidence['claims'])
    tag='(test, '+ident+')'
    withheld = outcome == 'void'
    kind = 'run' if withheld or progress is not None else 'claim'
    control = 'no releasable result' if withheld else 'passes'
    if withheld and (evidence['estimate'] is not None or evidence['interval'] is not None or opposition):
        raise ValueError('A void disposition cannot contain scientific estimates or opposition')
    if receipt.get('restricted'):
        raise ValueError('Restricted data require a separate internal filing')
    views.mark_pending(ROOT,ident)
    write(PUBLIC/(stem+'.md'),'# '+title+'\n\n'+body.rstrip()+'\n')
    atomic(PUBLIC/(stem+'.json'),dict(receipt,id=ident,card=card,full_write_through=True,record_kind=kind,scientific_admission=kind=='claim',theory_tags=evidence['claims'],activation=[]))
    theory=ROOT/'docs/theory/THREE_COGNITIVE_LAYERS.md'
    source=theory.read_text('utf8')
    if kind == 'claim' and tag not in source:
        anchor,=[l for l in source.splitlines() if l.startswith('| **'+theory_anchor+'** |')]
        if source.count(after_anchor)!=1:
            raise ValueError('Afterword anchor missing or ambiguous')
        changed=source.replace(anchor+'\n',anchor+'\n|   | | '+theory_note+' '+tag+' |\n',1)
        changed=changed.replace(after_anchor,afterword+' '+tag+'\n\n'+after_anchor,1)
        if [x for x in source.splitlines() if x.lstrip().startswith('>')]!=[x for x in changed.splitlines() if x.lstrip().startswith('>')]:
            raise ValueError('Quotation changed')
        write(theory,changed)
    findings=ROOT/'FINDINGS.md'
    reference = 'The exit code and disclosure decision are filed in the ' if withheld else 'The full comparison, original-source replay and limits are filed in the '
    if progress is not None:
        reference = 'The source check, original-source replay and scope are filed in the '
    add(findings,'### '+ident,'### '+ident+'\n\n'+evidence['question']+'\n\n'+evidence['data']+' '+afterword+'\n\n'+
        reference+'[study return](results/phase_2_4_stage_15/WEEK8/'+stem+'.md).\n\n'+
        '**Curator roll-up.** '+topic+'. '+evidence['verdict']+' '+evidence['limit']+' '+next_step,front=True)
    add(ROOT/'TODO.md',ident,'- [x] '+ident+'. '+evidence['verdict']+(' '+progress if progress else ''),front=True)
    tools=ROOT/'docs/TOOLS.md'
    old=tools.read_text('utf8')
    if ident not in old:
        marker,=[l for l in old.splitlines() if l.startswith('## The instrument ledger')]
        write(tools,old.replace(marker+'\n',marker+'\n\n**'+ident+'.** '+receipt['instrument']+' [Return](../results/phase_2_4_stage_15/WEEK8/'+stem+'.md).\n',1))
    detail='WEEK8/'+stem+'.md'
    ledgerfile=STAGE/'CLAIM_LEDGER.json'
    ledger=read(ledgerfile)
    if not any(x['id']==ident for x in ledger['rows']):
        ledger['rows'].append(dict(id=ident,card=card,at=stamp,record_kind=kind,estimand=evidence['question'],
            estimate=evidence['estimate'],outcome=outcome,control_status=control,strongest_rival=rival,scope=evidence['data'],
            scope_qualifiers=scope,pursuit=next_step,warrant=receipt['warrant'],public_wording=evidence['verdict'],detail=detail,
            source=dict(file='FINDINGS.md',line=0,anchor='### '+ident,source_sha256=''),supersedes=[],superseded_by=[],
            correction_class=None,theory_tags=evidence['claims'],theory_claims=evidence['claims'],activation=[],by_construction=False))
    rebind(ledger)
    ledger['at']=stamp
    atomic(ledgerfile,ledger)
    add(STAGE/'CLAIMS.md','| '+ident+' |','| '+ident+' | '+topic+' | '+outcome+' / '+control+' | '+evidence['verdict']+' |')
    evfile=ROOT/'results/EVIDENCE_LEDGER.jsonl'
    existing=[json.loads(l) for l in evfile.read_text('utf8').splitlines() if l.strip()]
    match=[row for row in existing if row['id']==ident]
    if match and match!=[evidence]:
        raise ValueError('Evidence ID already filed differently')
    if not match:
        with evfile.open('a',encoding='utf8',newline='\n') as stream:
            stream.write(json.dumps(evidence,ensure_ascii=False)+'\n')
    for file,heading,line in [('README.md','# Week 8 evidence','['+title+']('+stem+'.md). '+evidence['verdict']),
        ('INDEX.md','# Week 8 results',ident+'. ['+title+']('+stem+'.md).'),
        ('OPS_LOG.md','# Week 8 operating record',stamp+' '+ident+'. '+receipt['operations'])]:
        add(PUBLIC/file,stem if file=='README.md' else ident,line,front=True,heading=heading)
    add(ROOT/'docs/STATE.md',stem,evidence['verdict']+' [Week 8 '+card+' result](../results/phase_2_4_stage_15/'+detail+').',front=True)
    add(STAGE/'README.md','WEEK8/README.md','[Week 8 evidence](WEEK8/README.md) · [Current return](../../docs/exchange/WEEK8_RETURN.md).',front=True)
    index=STATE/'dispositions.json'
    states=read(index)
    disposition = evidence['verdict'] if withheld else title+' filed with its replay.'
    if progress is None:
        states[card]=dict(status='landed',owner='Sounding Line',evidence=disposition,result=return_line,limit=evidence['limit'])
    else:
        states.setdefault(card,{}).update(status='blocked',owner='Sounding Line',evidence=progress)
    atomic(index,states)
    if opposition:
        contrary=STATE/'contrary.json'
        items=read(contrary) if contrary.exists() else []
        if opposition not in items:
            atomic(contrary,[*items,opposition])
    coverage=ROOT/'.agent-state/work-coverage.json'
    work=read(coverage)
    entry,=[v for v in work['work'] if v['card']==card]
    entry.update(state='closed' if progress is None else 'build',evidence=str((PUBLIC/(stem+'.json')).relative_to(ROOT).as_posix()),last_inspection=receipt['terminal_sha256'])
    work['last_reconciled']=datetime.now(timezone.utc).isoformat()
    atomic(coverage,work)
    built=views.run(ROOT,'build')
    if views.run(ROOT,'check')!=built:
        raise ValueError('Generated view validation differs')
    print('Filed',ident)
