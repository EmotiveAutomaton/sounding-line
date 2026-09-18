"""Local common-form illustration viewer; no model call or unfinished result reads.

DESIGN CHECK: LESSONS 3-5. NULL: revealing records never replaces prior forecasts,
and passage selection cannot hide unlocated claims. ALTERNATIVE: a located claim
follows its anchor while evidence, alternatives and uncertainty remain inspectable.
The setup fixture is explicitly constructed, not scientific evidence.
"""
import argparse
from pathlib import Path
from .common import PRIVATE,canonical,freeze
from .construct import twins

TEMPLATE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sounding Line — contribution map</title><style>
body{margin:2rem auto;padding:0 1rem;max-width:1150px;background:#f4f2ec;color:#203b40;font:17px/1.5 system-ui}h1{font:42px Georgia}h2{font:26px Georgia}button,select{font:inherit;padding:.5rem;border:1px solid #7b9696;border-radius:5px;background:white;color:#203b40}button{cursor:pointer}main{display:grid;grid-template-columns:1.1fr 1fr;gap:1rem}section,article{padding:1rem;background:white;border:1px solid #d5dddd;border-radius:6px;margin:.7rem 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.4 monospace}.passage{display:inline;text-align:left;white-space:pre-wrap;margin:.2rem}.selected{outline:3px solid #238e96}.note{color:#50666a}details{margin:1rem 0}@media(max-width:760px){main{display:block}}
</style><h1>What choices remain visible?</h1><p id="scope"></p><label>Illustration <select id="case"></select></label> <button id="reveal">Reveal witnessed process</button>
<main><div><section><h2>Artifact</h2><div id="artifact"></div></section><section><h2>Evidence supplied</h2><pre id="evidence"></pre></section><section id="record" hidden><h2>Witnessed process facts</h2><pre id="truth"></pre></section></div>
<div><section><h2>Likely production steps</h2><div id="claims"></div><details><summary>Original blind forecast — retained after reveal</summary><pre id="prior"></pre></details></section><section><h2>Possible immediate aims</h2><div id="aims"></div></section><section><h2>What might this imply about the maker?</h2><div id="maker"></div></section></div></main>
<section><h2>Two cases to examine</h2><p>In the formatting illustration, what consequential human choice could remain invisible even if every recorded edit is recovered?</p><p>When the inserted fragment is completely removed, what should an account preserve about the choice to reject it?</p><details><summary>Answer bank — possible interpretations, after the questions</summary><p>Formatting might express a considered stylistic choice or a routine cleanup; the log alone does not settle that. Removal is witnessed, while its purpose and the writer's understanding remain unresolved. These are questions for the curator, not answers inferred from telemetry.</p></details></section>
<script type="application/json" id="data">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent),el=id=>document.getElementById(id);let revealed=false,selected=null;
function node(tag,text){const n=document.createElement(tag);n.textContent=text;return n}
data.cases.forEach((c,i)=>{const o=node('option',c.name);o.value=i;el('case').append(o)});
function show(){const c=data.cases[Number(el('case').value)||0];el('scope').textContent=data.scope;el('record').hidden=!revealed;el('reveal').textContent=revealed?'Hide witnessed process':'Reveal witnessed process';el('artifact').replaceChildren();
c.evidence.anchors.forEach(a=>{const b=node('button',c.evidence.endpoint.slice(a.start,a.end));b.className='passage'+(selected===a.id?' selected':'');b.onclick=()=>{selected=a.id;show()};el('artifact').append(b)});
el('evidence').textContent=JSON.stringify(c.evidence,null,2);el('truth').textContent=JSON.stringify(c.observed,null,2);el('prior').textContent=JSON.stringify(c.prior,null,2);el('claims').replaceChildren();
c.claims.forEach(claim=>{if(selected&&claim.span_ids.length&&!claim.span_ids.includes(selected))return;const box=node('article','');box.append(node('strong',claim.title),node('p','Evidence: '+claim.evidence),node('p','Alternative: '+claim.alternative),node('p','Uncertainty: '+claim.uncertainty));if(!claim.span_ids.length)box.append(node('p','Unlocated hypothesis — remains visible for every passage.'));el('claims').append(box)});
el('aims').textContent=c.aims;el('maker').textContent=c.maker;
}
el('case').onchange=()=>{selected=null;revealed=false;show()};el('reveal').onclick=()=>{revealed=!revealed;show()};show();
</script></html>'''


def preview(root=PRIVATE):
    rows=twins()[:12];cases=[]
    for i,row in enumerate(rows):
        cases.append(dict(name=f'Constructed illustration {i+1}',evidence=row['views']['artifact'],observed=row['target'],
            prior={'status':'No model forecast attached; constructed setup fixture only'},
            claims=[dict(title='Several production histories remain possible',span_ids=[],evidence='The endpoint alone; no process record has been revealed',
                         alternative='A writer could type the same words or select an offered fragment',uncertainty='Unresolved before the discriminating observation')],
            aims='Evidence: only recorded operations. Alternative aims remain possible. Uncertainty: current evidence does not identify the immediate aim.',
            maker='Evidence: a short recorded interval. Alternatives: different skills and priorities can produce the same interval. Uncertainty: values, expertise and understanding remain unresolved.'))
    value=dict(scope='Constructed setup preview. Twelve executed illustrations; no human performance result or contribution percentage.',
               selection='First construction family, all six transformations and both executed histories; fixed before scientific outcomes',cases=cases)
    freeze(root/'S5/PREVIEW-CASES.json',value)
    content=TEMPLATE.replace('__DATA__',canonical(value).replace('<','\\u003c'))
    output=root/'S5/contribution-map-preview.html';output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists() and output.read_text(encoding='utf-8')!=content:raise ValueError('immutable viewer preview changed')
    output.write_text(content,encoding='utf-8',newline='\n');return dict(path=str(output),cases=len(cases),scope=value['scope'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=PRIVATE);a=p.parse_args();print(preview(a.root))
