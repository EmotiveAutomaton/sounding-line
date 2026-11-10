"""Actual constructed Git copy history, native source/replay and pause proof."""
from pathlib import Path
import json,subprocess,sys
from . import week5_go as core
from . import week5_go_history_h2 as history
from . import week5_go_history_bounded_h2 as bounded


def main(root,phase):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if phase=='fixture':
        repo=root/'repo';repo.mkdir()
        def git(*args):
            p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True)
            if p.returncode:raise ValueError(p.stderr)
            return p.stdout.strip()
        git('init','-q');git('config','user.name','Constructed Fixture');git('config','user.email','fixture@example.invalid')
        text='---\nauthor: Constructed\ntype: Standards Track\n---\n## Motivation\nconstructed goal for tests\n## Specification\n'+('constructed specification line\n'*100)
        a=repo/'eip-1.md';a.write_bytes(text.encode());git('add','eip-1.md');git('commit','-qm','constructed origin')
        b=repo/'eip-2.md';b.write_bytes(a.read_bytes());a.write_bytes(a.read_bytes()+b'origin update\n')
        git('add','eip-1.md','eip-2.md');git('commit','-qm','constructed copy')
        b.write_bytes(text.encode()+b'\nlegacy caf\xe9\n');git('add','eip-2.md');git('commit','-qm','undeclared legacy bytes')
        b.write_bytes(text.encode()+b'\ncoding: latin-1\ncaf\xe9\n');git('add','eip-2.md');git('commit','-qm','declared legacy bytes')
        b.write_bytes((text+'\nmodern caf?\n').encode());git('add','eip-2.md');git('commit','-qm','utf8 successor')
        core.write(root/'documents.json',{'documents':[{'document':'constructed-document','repository':'eips','relative_path':'eip-2.md'}]})
        (root/'salt').write_bytes(b'c'*32)
        core.write(root/'INPUTS.json',{'head':git('rev-parse','HEAD'),'inputs':{'documents':str(root/'documents.json'),'salt':str(root/'salt'),'eips':str(repo)}})
        for operation in ('execute','verify'):
            p=subprocess.run([sys.executable,'-X','utf8','-B','-m',__spec__.name,str(root),operation],capture_output=True,text=True)
            (root/(operation+'.stdout.log')).write_text(p.stdout,encoding='utf8');(root/(operation+'.stderr.log')).write_text(p.stderr,encoding='utf8')
            if p.returncode:raise ValueError('constructed native '+operation+' failed; private stderr retained')
        result=json.loads((root/'run/SOURCE.json').read_text('utf8'))
        assert result['counts']['copy_creation_boundaries']==1 and result['counts']['copy_origin_revisions_excluded']==1
        assert result['counts']['excluded_undeclared_or_unsupported_encoding_versions']==1
        assert result['counts']['explicit_legacy_encoding_versions']==1
        core.write(root/'FIXTURE.json',{'verified':True,'constructed_only':True,'actual_git_copy_boundary':True,
                   'source_projection_fresh_native_replay':True,'pause_resume':True,'counts':result['counts'],
                   'modules':{Path(m.__file__).name:core.sha(m.__file__) for m in (history,bounded)}})
        print(json.dumps({'verified':True,'receipt':str(root/'FIXTURE.json')}));return
    bundle=json.loads((root/'INPUTS.json').read_text('utf8'));core.PINS['eips']=bundle['head'];inputs=bundle['inputs'];out=root/'run'
    if phase=='execute':
        assert bounded.execute(out,inputs,{'phase':'prepare','max_new_documents':0})['status']=='yielded'
        assert not (out/'SOURCE.json').exists()
        bounded.execute(out,inputs,{'phase':'prepare'})
    elif phase=='verify':assert bounded.verify(out,inputs,{'phase':'prepare'})['verified']
    else:raise ValueError('unknown operation')


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
