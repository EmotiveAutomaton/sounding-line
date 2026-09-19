// Execute the shipped local page, including all readers, reveals and selections.
// This validates UI state and text binding; it is not visual browser QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8');
const encoded=html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1];
const data=JSON.parse(encoded),script=html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
class Element {constructor(){this.children=[];this.value='';this.hidden=false;this.textContent='';this.className=''}append(...n){this.children.push(...n)}replaceChildren(...n){this.children=n}}
function harness(payload){const elements={};for(const match of html.matchAll(/id="([^"]+)"/g))elements[match[1]]=new Element();elements.data.textContent=JSON.stringify(payload);vm.runInNewContext(script,{document:{getElementById:id=>{assert(elements[id],id);return elements[id]},createElement:()=>new Element()}});return elements}
let checks=0;function check(value){assert(value);checks++}function equal(a,b){assert.deepStrictEqual(a,b);checks++}
function text(n){return n.textContent+' '+n.children.map(text).join(' ')}
const e=harness(data);check(data.cases.length>=8&&data.cases.length<=12);
for(let i=0;i<data.cases.length;i++)for(const method of ['alignment','direct','review','account']){
 const c=data.cases[i];e.case.value=String(i);e.case.onchange();e.method.value=method;e.method.onchange();
 check(e.facts.hidden);const prior=e.prior.textContent;equal(JSON.parse(prior),c.forecasts.artifact[method]);
 equal(e.artifact.children.map(x=>x.textContent).join(''),c.views.artifact.endpoint);
 for(const action of ['before','alternatives','reset']){
  e[action].onclick();equal(e.prior.textContent,prior);check(e.facts.hidden);
  const current=JSON.parse(e.current.textContent);const expected=action==='before'?(c.assisted[method]?.after||null):c.forecasts[action==='alternatives'?'alternatives':'artifact'][method];
  equal(current.forecast,expected);
  if(action==='before'){
   equal(e.pairbox.hidden,!c.assisted[method]);
   if(c.assisted[method])equal(JSON.parse(e.pair.textContent).blind,c.assisted[method].blind);
   else check(e.availability.textContent.includes('No forecast'));
  }
  for(const button of [...e.artifact.children]){
   button.onclick();equal(e.prior.textContent,prior);check(text(e.claims).includes('Unlocated hypothesis'));
   if(expected)for(const f of expected.facts.filter(f=>!f.span_ids.length))check(text(e.claims).includes(f.slot.replaceAll('_',' ')+':'));
  }
  e.clear.onclick();e.trace.onclick();check(!e.facts.hidden);equal(JSON.parse(e.truth.textContent),c.observed);equal(e.prior.textContent,prior);e.trace.onclick();check(e.facts.hidden);
 }
}
// Known rendering hazard: Python anchors use Unicode codepoints, JS slice uses UTF-16.
const fixture=structuredClone(data);fixture.cases=[structuredClone(data.cases[0])];const f=fixture.cases[0];
f.categories=['formatting-only change','substantial human continuation'];f.views.artifact.endpoint='A😀B';f.views.artifact.anchors=[{id:'a000',start:0,end:2},{id:'a001',start:2,end:3}];
const u=harness(fixture);equal(u.artifact.children.map(x=>x.textContent),['A😀','B']);
check(html.indexOf('id="question2"')<html.indexOf('Answer bank'));check(!encoded.includes('<script'));
console.log(JSON.stringify({status:'PASS',checks,cases:data.cases.length,readers:4,reveals:3,unicode_codepoints:true,visual_qa:'not performed'}));
