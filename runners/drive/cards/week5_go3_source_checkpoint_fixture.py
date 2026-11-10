"""Separate native processes qualify exact GO3 XML and in-post checkpoints."""
from pathlib import Path
import argparse,json,subprocess,sys,shutil,time,math
import xml.etree.ElementTree as ET
import py7zr
import pyarrow.parquet as pq
from . import week5_go3_source_checkpointed as source

core=source.core


def tree(root):return {p.relative_to(root).as_posix():core.sha(p) for p in root.rglob('*') if p.is_file()}


def child(root,phase):
    bundle=json.loads((root/'INPUTS.json').read_text('utf8'));inputs=bundle['inputs']
    source.base.ARCHIVES['writers']=bundle['archive_sha256'];source.base.LICENSE_SHA=core.sha(inputs['license'])
    cfg=dict(phase='prepare',site='writers',max_wall_seconds=300)
    if phase=='pilot':
        value=source.execute(root/'pilot',inputs,cfg)
        snap=json.loads((root/'pilot/SNAPSHOT.json').read_text('utf8'))
        total=sum((root/'pilot/xml'/name).stat().st_size for name in source.integrity.TARGETS)
        assert value['status']=='yielded' and sum(snap['state']['bytes'])==math.ceil(.05*total)
        assert not (root/'pilot/SOURCE.json').exists()
    elif phase=='projection':
        source.requested=lambda out:(Path(out)/'parts/0000000.parquet').exists()
        value=source.execute(root/'projection',inputs,cfg)
        state=json.loads((root/'projection/SNAPSHOT.json').read_text('utf8'))['state']
        assert value['status']=='yielded' and state['projected_history_rows']==source.PROJECTION_BATCH
        assert state['previous'] and not state['projection_complete']
    elif phase=='finish':
        value=source.execute(root/'complete',inputs,cfg)
        assert value.get('status')!='yielded'
        original=source.base.project_site(Path(inputs['archive']),Path(inputs['salt']).read_bytes(),'writers',root/'original')
        assert value['counts']==original['counts'] and value['retained_edits']==original['retained_edits']
        assert pq.read_table(root/'complete/edits.parquet').equals(pq.read_table(root/'original/edits.parquet'))
    elif phase=='verify-pilot':
        value=source.verify(root/'complete',inputs,cfg)
        assert value.get('status')=='yielded' and value['verified'] is False
    elif phase=='verify-finish':
        value=source.verify(root/'verified',inputs,cfg)
        assert value['verified'] is True
        assert pq.read_table(root/'verified/edits.parquet').equals(pq.read_table(root/'original/edits.parquet'))
    elif phase=='tamper':
        path=root/'tampered/projection.sqlite'
        with path.open('ab') as f:f.write(b'changed snapshot')
        try:source.execute(root/'tampered',inputs,cfg)
        except ValueError as exc:assert 'snapshot changed' in str(exc)
        else:raise AssertionError('Changed stopped database accepted')
        value=dict(refused=True)
    else:raise ValueError(phase)
    core.write(root/(phase+'.json'),dict(result=value,python_cpu_seconds=time.process_time()))


def main(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False);members=root/'members';members.mkdir()
    posts=ET.Element('posts');ET.SubElement(posts,'row',Id='1',OwnerUserId='a')
    history=ET.Element('posthistory')
    for i in range(3100):
        kind=2 if i==0 else 1 if i==1 else 3 if i==2 else 4 if i%7==0 else 6 if i%11==0 else 5
        attrs=dict(Id=str(i),PostId='1',PostHistoryTypeId=str(kind),CreationDate=f'2020-01-01T00:{i//60:02d}:{i%60:02d}',Text='body '+str(i),Comment='fix grammar')
        if i%13:attrs['UserId']='a' if i%2 else 'b'
        ET.SubElement(history,'row',**attrs)
    (members/'Posts.xml').write_bytes(ET.tostring(posts));(members/'PostHistory.xml').write_bytes(ET.tostring(history))
    archive=root/'fixture.7z'
    with py7zr.SevenZipFile(archive,'w') as z:
        for name in source.integrity.TARGETS:z.write(members/name,arcname=name)
    (root/'salt').write_bytes(b'j'*32);(root/'license.txt').write_text('Constructed only',encoding='utf8')
    core.write(root/'INPUTS.json',dict(archive_sha256=core.sha(archive),inputs=dict(archive=str(archive),salt=str(root/'salt'),license=str(root/'license.txt'))))
    def run(phase):
        result=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_go3_source_checkpoint_fixture',str(root),'--phase',phase],capture_output=True,timeout=180)
        (root/(phase+'.stdout.log')).write_bytes(result.stdout);(root/(phase+'.stderr.log')).write_bytes(result.stderr)
        if result.returncode:raise ValueError('Native fixture phase failed: '+phase+'; stderr retained')
    run('pilot');before=tree(root/'pilot');shutil.copytree(root/'pilot',root/'projection')
    run('projection');assert tree(root/'pilot')==before
    stopped=tree(root/'projection');shutil.copytree(root/'projection',root/'complete')
    run('finish');assert tree(root/'projection')==stopped
    run('verify-pilot');before_verify=tree(root/'complete');shutil.copytree(root/'complete',root/'verified')
    run('verify-finish');assert tree(root/'complete')==before_verify
    shutil.copytree(root/'pilot',root/'tampered');run('tamper')
    proofs=[json.loads((root/(p+'.json')).read_text('utf8')) for p in ('pilot','projection','finish','verify-pilot','verify-finish','tamper')]
    core.write(root/'FIXTURE.json',dict(verified=True,constructed_only=True,actual_native_processes=6,
        first_exact_five_percent_xml_bytes=True,split_xml_row_retained=True,inside_post_projection_pause=True,
        all_original_rows_and_dispositions_exact=True,independent_source_pilot_then_full_replay=True,
        immutable_predecessors=True,changed_database_refused=True,native_python_cpu_seconds=sum(p['python_cpu_seconds'] for p in proofs),
        source_sha256=core.sha(source.__file__),fixture_sha256=core.sha(__file__),human_prefix_not_run=True))
    print(json.dumps(dict(verified=True,receipt=str(root/'FIXTURE.json'))))


if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--phase');args=parser.parse_args()
    with threadpool_limits(limits=2):
        if args.phase:child(Path(args.output),args.phase)
        else:main(Path(args.output))
