"""Constructed local Git history and complete single-author texture proof."""
from pathlib import Path
import argparse,json,subprocess,time,shutil
import numpy as np
from . import week5_go as core
from . import week5_go_history_bounded_h2 as original
from . import week5_go2_authorship_bounded as bounded
from . import week5_go2_single_author as analysis


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture only')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);repo=root/'repo'
    def git(*args):
        result=subprocess.run(['git','-C',str(repo),*args],capture_output=True,check=True)
        return result.stdout.decode('utf8').strip()
    if not verifying:
        repo.mkdir();git('init','-q');git('config','user.name','Constructed Fixture');git('config','user.email','fixture@example.invalid')
        for version in range(8):
            for index in (1,2):
                author='Constructed One, Constructed Two' if index==2 and version==4 else 'Constructed One'
                goal='old alpha purpose' if version<4 else 'new beta purpose'
                text=f'---\nauthor: {author}\ntype: Standards Track\n---\n## Motivation\n{goal}\n## Specification\n'
                text+='\n'.join('body added '+str(i) for i in range(version+1))
                (repo/f'eip-{index}.md').write_bytes(text.encode())
            git('add','eip-1.md','eip-2.md');git('commit','-qm',f'constructed version {version}')
        (root/'salt').write_bytes(b'f'*32)
        core.write(root/'documents.json',dict(documents=[dict(document=str(i),repository='eips',relative_path=f'eip-{i}.md') for i in (1,2)]))
    head=git('rev-parse','HEAD');old_pin=core.PINS['eips'];core.PINS['eips']=head
    args=dict(documents=str(root/'documents.json'),eips=str(repo),salt=str(root/'salt'))
    try:
        if not verifying:
            paused=bounded.execute(root/'pilot',args,dict(phase='prepare',max_new_documents=1))
            assert paused['status']=='yielded' and paused['documents_complete']==1
            before={p.relative_to(root/'pilot').as_posix():core.sha(p) for p in (root/'pilot').rglob('*') if p.is_file()}
            shutil.copytree(root/'pilot',root/'source')
            bounded.execute(root/'source',args,dict(phase='prepare',max_new_documents=1))
            assert before=={p.relative_to(root/'pilot').as_posix():core.sha(p) for p in (root/'pilot').rglob('*') if p.is_file()}
            original.execute(root/'original',args,dict(phase='prepare'))
        else:
            fresh=root/'fresh-native-source'
            bounded.execute(fresh,args,dict(phase='prepare'))
            for name in ('SOURCE.json','anchors.json','first-drafts.json'):
                assert core.sha(fresh/name)==core.sha(root/'source'/name)
            for p in (fresh/'document-parts').glob('*/SEAL.json'):
                assert core.sha(p)==core.sha(root/'source'/p.relative_to(fresh))
        assert bounded.verify(root/'source',args,dict(phase='prepare'))['verified']
        actual=json.loads((root/'source/anchors.json').read_text('utf8'))['anchors']
        legacy=json.loads((root/'original/anchors.json').read_text('utf8'))['anchors']
        assert [{k:v for k,v in row.items() if k!='historical_multi_author'} for row in actual]==legacy
        assert len(actual)==2 and [r['historical_multi_author'] for r in actual]==[False,True]
        receipt=json.loads((root/'source/SOURCE.json').read_text('utf8'))
        assert receipt['counts']['documents_any_eligible_multi_author']==1
        assert receipt['counts']['documents_with_eligible_authorship']==2
        current=json.loads((root/'source/first-drafts.json').read_text('utf8'))['documents']
        assert all(r['multi_author'] is False for r in current)
        old_vector=analysis.vector_bank
        try:
            for sign in (-1,0,1):
                anchors=[]
                for i in range(120):
                    anchors.append(dict(author=str(i%30),document=str(i),old_goal='old',new_goal='new',before=['before']*3,
                        after=['excluded' if i>=100 else 'after']*3,three_each=True,historical_multi_author=i>=100))
                path=root/f'constructed-{sign}.json';core.write(path,dict(anchors=anchors))
                def vectors(texts,*unused,s=sign):
                    assert 'excluded' not in texts
                    mapping={'old':[1.,0.,0.],'new':[0.,1.,0.],'before':[0.,0.,1.],
                             'after':([0.,1.,0.] if s>0 else [1.,0.,0.] if s<0 else [0.,0.,1.])}
                    return np.array([mapping[text] for text in texts])
                analysis.vector_bank=vectors
                out=root/f'analysis-{sign}';data=dict(anchors=str(path),encoder_manifest='constructed-unused')
                value=analysis.execute(out,data,dict(draws=200))
                assert value['anchors']==100 and value['multi_author_history_anchors_excluded']==20
                assert abs(value['after_minus_before']-sign)<1e-12
                assert analysis.verify(out,data,dict(draws=200))['verified']
        finally:analysis.vector_bank=old_vector
    finally:core.PINS['eips']=old_pin
    proof=dict(constructed_only=True,actual_local_git_history=True,current_and_first_headers_insufficient_case=True,
        historical_multi_author_detected=True,all_original_h2_anchor_fields_exact=True,document_pause_and_immutable_copy=True,
        complete_fresh_source_replay=True,signed_negative_exact_null_consumer=True,all200_draws_replayed=True,
        source_documents=2,numerical_anchors=120,excluded_numerical_anchors=20,encoder_vectors_constructed=True,
        scientific_admission=False)
    if verifying:
        assert json.loads((root/'FIXTURE.json').read_text('utf8'))==proof
        return dict(verified=True,complete_native_handler_replay=True)
    core.write(root/'FIXTURE.json',proof);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    began=time.process_time()
    with threadpool_limits(limits=2):value=(verify if args.verify else execute)(Path(args.output),{}, {})
    core.write(Path(args.output)/('NATIVE_VERIFY_CPU.json' if args.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
