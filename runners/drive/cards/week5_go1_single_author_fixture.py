"""Complete native single-author grid-cell proof with known signed banks."""
from pathlib import Path
import argparse,json,time
import numpy as np
from . import week5_go1_single_author as cell
from .week5_at_scoring import digest
from .week5_at_scoring_v4 import NUMERICAL_SPEC


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture only')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);base=cell.base;write=base.core.write
    rows=[dict(repository='eips',type='Standards Track',category='Core',author=str(i),document=str(i),
               motivation=f'goal {i}',rest=f'rest {i}',multi_author=i>=60) for i in range(70)]
    docs=root/'documents.json';write(docs,dict(documents=rows))
    manifest=root/'model.json';model=dict(model='constructed',revision='fixed',files={});write(manifest,model)
    encoder=root/'encoder.json';write(encoder,dict(constructed=True));selection=root/'selection'
    write(selection/'output/RESULT.json',dict(card='AT2',selection_admissible=True,selected_model='constructed'))
    write(selection/'output/READER_BINDING.json',dict(model='constructed',revision='fixed',manifest_sha256=digest(model),numerical_spec=NUMERICAL_SPEC))
    write(selection/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(selection).as_posix():base.core.sha(p) for p in (selection/'output').glob('*.json')}))
    args=dict(documents=str(docs),model_manifest=str(manifest),at2_selection=str(selection),encoder_manifest=str(encoder))
    selected,roster=cell.prepared_rows(args,{})
    assert len(selected)==len(roster)==60 and all(len(a['candidates'])==50 for a in roster)
    assert all(not r['multi_author'] for r in selected)
    old=(base.core.lexical_scores,base.lm_scores,base.vector_bank)
    def bank(actual,allocation,correct):
        assert actual==selected and allocation==roster
        scores=np.zeros((60,50))
        for i,a in enumerate(allocation):
            target=a['truth_position'] if correct(i) else (a['truth_position']+1)%50
            scores[i,target]=1.
        return scores
    def lexical(actual,allocation,*unused):return bank(actual,allocation,lambda i:i%2==0)
    def vector_bank(texts,*unused):
        assert len(texts)==120
        return np.concatenate([np.eye(60),np.eye(60)],axis=0)
    base.core.lexical_scores=lexical;base.vector_bank=vector_bank
    try:
        for sign in (-1,0,1):
            folder=root/f'sign-{sign}'
            base.lm_scores=lambda actual,allocation,*unused,s=sign:bank(actual,allocation,lambda i:s>0 or (s==0 and i%2==0))
            banks={}
            for name in ('tfidf','encoder','language_model'):
                out=folder/name;cfg=dict(phase='GO1-score',reader=name,context_length=1024)
                value=cell.execute(out,args,cfg)
                assert value['source_exposure']['multi_author_excluded']==10
                assert cell.verify(out,args,cfg)['verified'];banks[name]=str(out)
            collected=folder/'collected';cfg=dict(phase='GO1-collect',draws=200)
            value=cell.execute(collected,{**args,'readers':banks},cfg)
            assert value['draws']==200 and value['authors']==60 and value['documents']==60
            assert abs(value['gain_over_lexical']['language_model']['estimate']-.5*sign)<1e-12
            assert cell.verify(collected,{**args,'readers':banks},cfg)['verified']
        missing=[dict(r) for r in rows];missing[0].pop('multi_author');write(docs,dict(documents=missing))
        try:
            try:cell.prepared_rows(args,{})
            except ValueError:pass
            else:raise AssertionError('Unknown author multiplicity accepted')
        finally:write(docs,dict(documents=rows))
    finally:base.core.lexical_scores,base.lm_scores,base.vector_bank=old
    proof=dict(constructed_only=True,verified_filter_before_roster=True,source_documents=70,single_author_documents=60,
        excluded_multi_author_documents=10,all_three_complete_banks=True,positive_negative_exact_null=True,
        distractors=49,cluster_draws=200,independent_full_replay=True,missing_authorship_flag_refused=True,
        reader_values='constructed known-answer scores; numerical model primitive separately qualified',scientific_admission=False)
    if verifying:
        assert json.loads((root/'FIXTURE.json').read_text('utf8'))==proof
        return dict(verified=True,complete_native_handler_replay=True)
    write(root/'FIXTURE.json',proof);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    began=time.process_time()
    with threadpool_limits(limits=2):value=(verify if args.verify else execute)(Path(args.output),{}, {})
    cell.base.core.write(Path(args.output)/('NATIVE_VERIFY_CPU.json' if args.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
