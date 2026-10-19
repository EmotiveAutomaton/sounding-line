import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import engine_signatures as card
from runners.drive.cards.timing_p6 import gzread
from runners.stage14.common import read, filehash


def span(text,a,b):
    return dict(codepoints=[a,b],utf8=[len(text[:a].encode()),len(text[:b].encode())],
        utf16=[len(text[:a].encode('utf-16-le'))//2,len(text[:b].encode('utf-16-le'))//2],exact=text[a:b])


def fixture(kind='planted',writers=24):
    documents=[];exports=[]
    for w in range(writers):
        for p in range(3):
            for repeat in range(2):
                phrases=[f'signal{w:02d}a',f'signal{w:02d}b'] if kind=='planted' else [f'prompt{p}a',f'prompt{p}b'] if kind=='prompt' else ['samealpha','samebeta']
                paragraph=' '.join(phrases)+'.';text=paragraph+'\n\n'+paragraph
                keys=dict(writer=f'w{w:02d}',session=f'w{w:02d}-p{p}-r{repeat}',prompt=f'p{p}')
                doc=dict(keys=keys,text=text,textSha256=hashlib.sha256(text.encode()).hexdigest(),variant='final-document',provenance=[])
                ps=[]
                for phrase in phrases:
                    a=text.index(phrase);b=text.index(phrase,len(paragraph))
                    ps.append(dict(span=span(text,a,a+len(phrase)),departure=1.,recurring=True,
                        sectionSupport=2,paragraphSupport=2,occurrences=[dict(region=f'r{n}',section=f's{n}',span=span(text,start,start+len(phrase))) for n,start in enumerate((a,b))]))
                values=dict(status='complete',keys=keys,textSha256=doc['textSha256'],inputRecordSha256=card.digest(doc),
                    departurePhrases=ps,habits=dict(raw=dict(words=4,quotedWords=0)))
                documents.append(doc);exports.append(values)
    return dict(documents=documents,exports=exports)


def rows(kind='planted'):
    f=fixture(kind);return card.population(f['documents'],f['exports'])


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True),encoding='utf8');return str(path)


def test_planted_recurrence_is_exact_and_control_is_not_the_signal():
    summary,detail=card.analyze(rows(),card.CONFIG)
    assert summary['primary']['effect']==5000
    assert summary['primary']['ci_low']==summary['primary']['ci_high']==5000
    assert summary['paired_fake_writer_contrast']['ci_low']>0
    assert summary['state']=='positive' and not summary['reassignment_reference']['biased']
    assert summary['support']['matched_signatures']==288 and summary['support']['matched_writers']==24
    assert all(set(r['own'])=={5000} and set(r['other'])=={0} for r in detail['source_rates'])


@pytest.mark.parametrize('kind',['null','prompt'])
def test_shared_and_prompt_only_phrases_have_exact_zero(kind):
    summary,detail=card.analyze(rows(kind),card.CONFIG)
    assert summary['primary']['effect']==0 and summary['state']=='null'
    assert summary['reassignment_reference']['mean']==0 and not summary['reassignment_reference']['biased']
    assert not np.any(detail['writer_means_by_assignment'])


def test_literal_matching_overlap_punctuation_and_unicode():
    assert card.matching('banana BANANA','ana')==4
    assert card.matching('A  B; a b. a-b','a b')==1
    assert card.matching('Stra\u00dfe STRASSE','stra\u00dfe')==1
    assert card.matching('\U0001f642 Cat cAt','cat')==2
    with pytest.raises(ValueError):card.matching('x','')


def test_exact_prompt_weighting_has_scalar_oracle():
    r=[dict(writer=w,session=str(i),prompt=p,words=n,text=t,signatures=['x'] if i==0 else []) for i,(w,p,n,t) in enumerate([
        ('a','source',2,'x x'),('a','p',10,'x'),('a','q',20,'x x x x'),('b','p',100,'x '*20),('b','q',10,'x')])]
    labels=np.array([x['writer'] for x in r]);counts=np.array([[card.matching(x['text'],'x') for x in r]])
    v,own,other=card.evaluate(r,labels,card.targets(r,labels),counts,{'x':0},[0])
    assert own[0][0]==pytest.approx(10000*5/30)
    assert other[0][0]==pytest.approx(10000*(10*20/100+20*1/10)/30)
    assert v[0]==pytest.approx(10000/30)


def test_fixed_same_rows_and_prompt_rosters_survive_all_reassignments():
    r=rows();aa=card.assignments(r,200,20261018)
    for a in aa:
        for prompt in ('p0','p1','p2'):
            assert sorted(a[i] for i,x in enumerate(r) if x['prompt']==prompt)==sorted(x['writer'] for x in r if x['prompt']==prompt)
    summary,detail=card.analyze(list(reversed(r)),card.CONFIG)
    baseline,original=card.analyze(r,card.CONFIG)
    assert (summary,detail)==(baseline,original)


def test_missing_matches_are_not_zero_and_population_is_explicit():
    r=rows();r=[x for x in r if x['writer']!='w00' or x['prompt']=='p0']
    summary,detail=card.analyze(r,card.CONFIG)
    assert summary['support']['dropped_documents']>0
    assert any(x['status']=='unsupported-matched-prompt-roster' for x in detail['dispositions'])
    thin=card.analyze(r,dict(card.CONFIG,min_signatures=100000))[0]
    assert thin['state']=='unsupported' and 'primary' not in thin


def test_denominator_gap_is_unsupported_without_imputation():
    r=rows()
    for x in r:
        if x['prompt']=='p1':x['words']=0
    summary,_=card.analyze(r,card.CONFIG)
    # Source prompt p1 is excluded from its own target pools; its 48 source
    # documents still have positive denominators on p0/p2. The other96 do not.
    assert summary['state']=='unsupported' and summary['support']['matched_documents']==48


@pytest.mark.parametrize('mutation',['identity','span','recurring','paragraphs','nan','duplicate','words','too-many'])
def test_source_identity_and_support_refuse_corruption(mutation):
    f=fixture();v=f['exports'][0];p=v['departurePhrases'][0]
    if mutation=='identity':v['inputRecordSha256']='0'*64
    elif mutation=='span':p['span']['utf8'][1]+=1
    elif mutation=='recurring':p['recurring']=False
    elif mutation=='paragraphs':p['paragraphSupport']=3
    elif mutation=='nan':p['departure']=float('nan')
    elif mutation=='duplicate':f['documents'].append(f['documents'][0]);f['exports'].append(f['exports'][0])
    elif mutation=='words':v['habits']['raw']['words']=-1
    else:v['departurePhrases']=v['departurePhrases']*8
    with pytest.raises(ValueError):card.population(f['documents'],f['exports'])


def test_paragraph_support_and_deduplication_match_declared_question():
    f=fixture();v=f['exports'][0]
    for p in v['departurePhrases']:
        for o in p['occurrences']:o['section']='one-section'
        p['sectionSupport']=1;p['recurring']=False
    v['departurePhrases'].append(copy.deepcopy(v['departurePhrases'][0]))
    assert len(card.population(f['documents'],f['exports'])[0]['signatures'])==2


def test_biased_and_negative_control_boundaries():
    assert card.reference([1,1,1],2)['biased']
    assert card.reference([-1,-1,-1],2)['biased']
    assert not card.reference([0,0,0],0)['biased']
    assert card.interval(np.array([-1.,-2.,-3.]),2000,7)['state']=='negative'
    with pytest.raises(ValueError):card.reference([0,float('nan')],1)


def test_serialized_handler_fresh_process_and_immutable_reentry(tmp_path):
    inputs=dict(fixture=save(tmp_path/'fixture.json',fixture()))
    output=tmp_path/'output';summary=card.execute(output,inputs,card.CONSTRUCTED)
    hashes=read(output/'TIMING_BINDINGS.json')['outputs']
    script='from runners.drive.cards import engine_signatures as c; import json,sys; assert c.verify(sys.argv[1],json.loads(sys.argv[2]),c.CONSTRUCTED)["verified"]'
    env=dict(os.environ,PYTHONHASHSEED='983')
    subprocess.run([sys.executable,'-X','utf8','-B','-c',script,str(output),json.dumps(inputs)],env=env,check=True,timeout=120)
    assert card.execute(output,inputs,card.CONSTRUCTED)==summary
    assert hashes=={n:filehash(output/n) for n in hashes}
    bad=read(output/'SUMMARY.json');bad['state']='null';save(output/'SUMMARY.json',bad)
    with pytest.raises(ValueError):card.verify(output,inputs,card.CONSTRUCTED)


def test_changed_inputs_and_scope_refused(tmp_path):
    inputs=dict(fixture=save(tmp_path/'fixture.json',fixture()))
    output=tmp_path/'out';card.execute(output,inputs,card.CONSTRUCTED)
    save(Path(inputs['fixture']),fixture('null'))
    with pytest.raises(ValueError):card.verify(output,inputs,card.CONSTRUCTED)
    with pytest.raises(ValueError):card.load(inputs,dict(card.CONSTRUCTED,permutations=1))
    with pytest.raises(ValueError):card.load(inputs,card.CONFIG)
