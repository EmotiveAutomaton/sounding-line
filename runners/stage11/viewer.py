"""Private, self-contained contribution map; retained forecasts, no new calls."""
import argparse
from .core import *
from .report import attempt, reparse, audit_event


def cases(root):
    rows=read(root/'COHORT.json')['evaluation']; eligible=[]
    # Only inspect a complete registered tranche for case selection.
    for tranche in ('initial','extension'):
        own=[r for r in rows if r['tranche']==tranche]
        if own and all((attempt(root,'evaluation',r,v,a)/'ATTEMPT.json').exists() for r in own for v in VIEWS for a in ARMS):
            eligible.extend(own)
            break  # Freeze illustration eligibility to the first complete tranche.
    if not eligible: raise ValueError('no complete tranche available for example selection')
    material=[]
    for r in eligible:
        forecasts={v:{a:reparse(attempt(root,'evaluation',r,v,a),r['views'][v],a)['forecast'] for a in ARMS} for v in VIEWS}
        f=forecasts['alternatives']['account'];p=f['probabilities'] if f else None
        correct=p is not None and ACTIONS[max(range(4),key=lambda i:p[i])]==r['truth']
        material.append(dict(row=r,forecasts=forecasts,correct=correct,confidence=max(p) if p else 0))
    material.sort(key=lambda x:digest(['stage11-examples',x['row']['key']]))
    chosen=[];coverage={}
    predicates=[('correct',lambda x:x['correct']),('confident_error',lambda x:not x['correct'] and x['confidence']>=.7),
                ('ambiguity',lambda x:x['row']['truth'] in ('dismiss','ignore')),
                ('deleted_or_unlocated',lambda x:x['row']['event']['verified_insertion'] and not x['row']['event']['terminal_spans'])]
    for name,predicate in predicates:
        hits=[x for x in material if predicate(x) and x not in chosen]
        coverage[name]=bool(hits)
        if hits:
            fresh=[x for x in hits if x['row']['writer'] not in {s['row']['writer'] for s in chosen}]
            chosen.append((fresh or hits)[0])
    for x in material:
        if len(chosen)>=6:break
        if x not in chosen and x['row']['writer'] not in {s['row']['writer'] for s in chosen}:chosen.append(x)
    for x in material:
        if len(chosen)>=6:break
        if x not in chosen: chosen.append(x)
    # Six examples must retain at least four writers where the pool permits it.
    for candidate in material:
        if len({x['row']['writer'] for x in chosen})>=min(4,len({x['row']['writer'] for x in material})): break
        if candidate['row']['writer'] in {x['row']['writer'] for x in chosen}: continue
        counts=Counter(x['row']['writer'] for x in chosen)
        replace=next((i for i in reversed(range(len(chosen))) if counts[chosen[i]['row']['writer']]>1),None)
        if replace is not None: chosen[replace]=candidate
    coverage={name:any(predicate(x) for x in chosen) for name,predicate in predicates}
    out=[]
    for index,x in enumerate(chosen):
        r=x['row']; audits={v:[audit_event(e,r) for e in (x['forecasts'][v]['account'] or {}).get('events',[])] for v in VIEWS}
        out.append(dict(name='Case '+str(index+1),artifact=r['views']['artifact']['episode_end_document'],
                        views=r['views'],forecasts=x['forecasts'],audit=audits,
                        reveal=dict(handling=r['truth'],episode_ordinal=r['event']['ordinal'],cutoff_ordinal=r['event']['cutoff_ordinal'],
                                    verified_insertion=r['event']['verified_insertion'],spans=r['event']['terminal_spans'],
                                    review='unknown',endorsement='unknown',
                                    missing_span='No surviving insertion span. This is not evidence of little human contribution.'),
                        purpose='Not established by these records.',
                        person='Recorded choices can demonstrate situated handling. Habits, values, awareness and depth of review remain unresolved.'))
    return dict(cases=out,coverage=coverage,writers=len({x['row']['writer'] for x in chosen}),
                rule='First complete registered tranche only. Stable hash order: an available correct, confidence >= 0.7 error, dismissal/ignore ambiguity, and deleted insertion; prefer new writers, fill to six, enforce four writers where available. Missing types are disclosed. Selection does not alter scoring.')


TEMPLATE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sounding Line · Contribution map</title><style>
:root{font-family:system-ui;color:#192a38;background:#f1f3f3}body{margin:0}header{background:#17303f;color:white;padding:25px 4vw}h1{font-size:27px;margin:0 0 8px}p{line-height:1.5}main{padding:22px 4vw}button,select{padding:9px 12px;border:1px solid #92a3ad;border-radius:6px;background:white;color:#17303f;cursor:pointer;margin:4px}button:hover{background:#e9f0f5}.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px}.layout{display:grid;grid-template-columns:minmax(300px,1fr) minmax(360px,1.15fr);gap:24px;margin-top:20px}.card{background:white;border-radius:10px;padding:20px;border:1px solid #d8e0e4;margin-bottom:14px}h2{font-size:19px;margin:0 0 12px}h3{font-size:16px}.passage{white-space:pre-wrap;display:block;width:100%;text-align:left;line-height:1.65;border:0;border-left:3px solid transparent;font-family:Georgia,serif;font-size:17px}.passage.selected{border-color:#c7783d;background:#f8efe6}.event{border-left:4px solid #827aa8;padding:9px;margin:10px 0;background:#f4f2f9}.event[data-op=edit]{border-color:#237b7a}.event[data-op=select]{border-color:#be753d}.uncertain{border-left-style:dashed;opacity:.78}.badge{display:inline-block;border:1px solid currentColor;padding:2px 6px;border-radius:4px;font-size:12px}.supported{color:#147047}.contradicted{color:#a32f32}.unresolved{color:#676176}.small{font-size:13px;color:#536774}.prob{display:grid;grid-template-columns:100px 1fr 48px;align-items:center;gap:9px;margin:7px 0}.bar{height:9px;background:#dce3e7}.bar span{display:block;height:9px;background:#37647e}pre{white-space:pre-wrap;word-break:break-word;font-size:13px}#record[hidden]{display:none}details{margin-top:12px}@media(max-width:800px){.layout{grid-template-columns:1fr}}
</style><header><h1>Who did what here?</h1><div>Possible creation history · Immediate purpose · What the evidence warrants about the person</div></header>
<main><div class="toolbar"><label>Case <select id="case"></select></label><label>Evidence <select id="view"><option value="artifact">Episode-end artifact</option><option value="alternatives">Artifact and available alternatives</option></select></label><button id="reveal">Reveal recorded handling</button></div>
<p class="small">Private research example. Forecasts are elicited and uncalibrated. Color denotes operation; borders denote support; dashed, faint cards denote unresolved history, never absent contribution. Overlapping hypotheses are allowed. Click a passage to inspect linked claims.</p>
<div class="layout"><div><section class="card"><h2>Episode-end text</h2><div id="text"></div></section><section class="card" id="record" hidden><h2>Recorded evidence</h2><div id="truth"></div></section><details class="card"><summary>Permitted evidence and example selection</summary><pre id="evidence"></pre><p id="selection"></p></details></div>
<div><section class="card"><h2>1 · Possible creation history</h2><div id="forecast"></div><div id="events"></div></section><section class="card"><h2>2 · Possible immediate purpose</h2><p id="purpose"></p></section><section class="card"><h2>3 · What this suggests about the person</h2><p id="person"></p></section></div></div></main>
<script type="application/json" id="data">__DATA__</script><script>
const data=JSON.parse(document.querySelector('#data').textContent),el=id=>document.getElementById(id);let revealed=false,selected='';
function node(tag,text,cls){const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n}
data.cases.forEach((c,i)=>{const o=node('option',c.name);o.value=i;el('case').append(o)});
function show(){const c=data.cases[+el('case').value],v=el('view').value;el('record').hidden=!revealed;el('reveal').textContent=revealed?'Hide recorded handling':'Reveal recorded handling';el('text').replaceChildren();
c.artifact.split(/(\\n\\s*\\n)/).filter(t=>t.trim()).forEach(t=>{const b=node('button',t,'passage'+(selected===t?' selected':''));b.onclick=()=>{selected=t;show()};el('text').append(b)});
el('forecast').replaceChildren();['direct','account'].forEach(a=>{el('forecast').append(node('h3',a==='direct'?'Direct reader':'Contribution account'));const f=c.forecasts[v][a];if(!f){el('forecast').append(node('p','Invalid forecast retained in scoring.'));return}f.probabilities.forEach((p,i)=>{const row=node('div','','prob');row.append(node('span',['Unedited','Edited','Dismissed','Left'][i]));const bar=node('div','','bar'),fill=node('span','');fill.style.width=(p*100)+'%';bar.append(fill);row.append(bar,node('span',(100*p).toFixed(1)+'%'));el('forecast').append(row)});el('forecast').append(node('p',f.explanation,'small'))});
el('events').replaceChildren();const events=(c.forecasts[v].account||{}).events||[];let shown=0;events.forEach((e,i)=>{if(selected&&e.quote&&!selected.includes(e.quote))return;shown++;const audit=c.audit[v][i],box=node('div','','event'+(!revealed||audit.record_relation==='unresolved'?' uncertain':''));box.dataset.op=e.operation.toLowerCase();box.append(node('strong',e.actor+' · '+e.operation),node('p',e.quote?'Text: “'+e.quote+'”':'No located supporting passage.','small'),node('p','Competing history: '+e.alternative,'small'),node('p','Dependencies: '+e.depends_on+' · Missing evidence: '+e.missing_evidence,'small'));if(revealed){box.append(node('span',audit.record_relation,'badge '+audit.record_relation),node('p','Quote match: '+audit.quote_match+'. A quote match alone is not semantic proof.','small'))}else box.append(node('span','Unverified hypothesis','badge'));el('events').append(box)});if(!shown)el('events').append(node('p','No account event is located in this passage. This says nothing about its contribution.'));
el('purpose').textContent=c.purpose;el('person').textContent=c.person;el('evidence').textContent=JSON.stringify(c.views[v],null,2);el('selection').textContent=data.rule+' Writers: '+data.writers+'. Coverage: '+JSON.stringify(data.coverage);el('truth').replaceChildren(node('p','Recorded handling: '+c.reveal.handling),node('pre',JSON.stringify(c.reveal,null,2)));if(revealed)el('truth').append(node('p','Compare the handling probabilities above with this record. Selection does not establish review or endorsement.'));
}
el('case').onchange=()=>{revealed=false;selected='';show()};el('view').onchange=()=>{revealed=false;show()};el('reveal').onclick=()=>{revealed=!revealed;show()};show();
</script></html>'''


def build(root=PRIVATE):
    result=cases(root);freeze(root/'VIEWER_CASES.json',result)
    content=TEMPLATE.replace('__DATA__',canonical(result).replace('<','\\u003c'))
    path=root/'contribution-map.html'
    if path.exists() and path.read_text(encoding='utf-8')!=content: raise ValueError('viewer evidence changed')
    path.write_text(content,encoding='utf-8',newline='\n')
    return dict(path=str(path),cases=len(result['cases']),writers=result['writers'],coverage=result['coverage'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=PRIVATE);args=parser.parse_args();print(build(args.root))
