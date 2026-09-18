// Execute the actual generated UI script against a tiny DOM fixture.
// This verifies state/reveal logic, not browser layout or accessibility.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.style={};this.dataset={};this.value='0';this.hidden=false;this.textContent='';}
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=items;}
}
const elements={};
for(const id of ['data','case','view','record','reveal','text','forecast','events','purpose','person','evidence','selection','truth'])elements[id]=new Element('div');
elements.data.textContent=html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1];
elements.view.value='artifact';
const document={getElementById:id=>elements[id],querySelector:s=>elements[s.slice(1)],createElement:tag=>new Element(tag)};
const script=html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
vm.runInNewContext(script,{document});
assert.equal(elements.record.hidden,true);
assert(elements.forecast.children.length>0);
elements.reveal.onclick();assert.equal(elements.record.hidden,false);
if(html.includes('review_summary')){
  assert(elements.truth.children.some(c=>c.textContent.includes('selection')||c.textContent.includes('closure')));
  assert(elements.events.children.some(c=>c.children.some(n=>n.textContent.startsWith('Operation: '))));
}
elements.case.value='1';elements.case.onchange();assert.equal(elements.record.hidden,true);
elements.text.children[0].onclick();assert(elements.text.children[0].className.includes('selected'));
elements.view.value='alternatives';elements.view.onchange();assert.equal(elements.record.hidden,true);
assert(elements.evidence.textContent.includes('pre_menu_document'));
assert(elements.person.textContent.includes('unresolved'));
if(process.argv.includes('--check-unlocated')){
  const cases=JSON.parse(elements.data.textContent).cases;
  let checked=0;
  cases.forEach((c,ci)=>{
    for(const view of ['artifact','alternatives']){
      elements.case.value=String(ci);elements.case.onchange();
      elements.view.value=view;elements.view.onchange();
      const events=(c.forecasts[view].account||{}).events||[];
      const expected=events.filter(e=>!e.quote||!c.artifact.includes(e.quote));
      const passages=elements.text.children.length;
      for(let pi=0;pi<passages;pi++){
        elements.text.children[pi].onclick();
        for(const event of expected){
          assert(elements.events.children.some(box=>
            box.children.some(n=>n.textContent===event.actor+' · '+event.operation)&&
            (!event.quote||box.children.some(n=>n.textContent.includes(event.quote)))),
            `${c.name}/${view}: unlocated ${event.operation} disappeared after passage selection`);
          checked++;
        }
      }
    }
  });
  assert(checked>0);
  console.log(`PASS: ${checked} unlocated-event visibility checks across every case, view and passage.`);
}
console.log('PASS: forecasts visible, records hidden until reveal, case/view reset, passage selection, evidence tiers. Visual layout untested.');
