// Actual generated script, minimal DOM: state/content checks, not visual layout QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8');
class Element{constructor(){this.children=[];this.value='0';this.hidden=false;this.textContent=''}append(...n){this.children.push(...n)}replaceChildren(...n){this.children=n}}
const elements={};for(const id of ['data','scope','case','reveal','artifact','evidence','record','truth','prior','claims','aims','maker'])elements[id]=new Element();
elements.data.textContent=html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1];
const script=html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
vm.runInNewContext(script,{document:{getElementById:id=>elements[id],createElement:()=>new Element()}});
const cases=JSON.parse(elements.data.textContent).cases;let assertions=0;
for(let i=0;i<cases.length;i++){
 elements.case.value=String(i);elements.case.onchange();assert(elements.record.hidden);const prior=elements.prior.textContent;
 elements.reveal.onclick();assert(!elements.record.hidden);assert.equal(elements.prior.textContent,prior);
 for(const button of [...elements.artifact.children]){button.onclick();assert(elements.claims.children.some(c=>c.children.some(n=>n.textContent.startsWith('Unlocated hypothesis'))));assert.equal(elements.prior.textContent,prior);assertions+=2}
 assert(elements.aims.textContent.includes('Uncertainty'));assert(elements.maker.textContent.includes('Uncertainty'));assertions+=5;
}
console.log(`PASS: ${assertions} assertions; ${cases.length} constructed cases, reveal preserves prior, unlocated claims persist. Visual layout untested.`);
