"""Native tiny 7z source/extraction refusal and full unchanged projection."""
from pathlib import Path
import argparse,json,shutil,time
import xml.etree.ElementTree as ET
import py7zr
from . import week5_go3_source_integrity as safe


def refuse(call,label):
    try:call()
    except ValueError:return
    raise AssertionError(label+' accepted')


def run(output,inputs,config,verifying=False):
    if inputs or config:raise ValueError('Constructed fixture only')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);base=safe.original;core=base.core
    members=root/'members';archive=root/'fixture.7z'
    if not verifying:
        members.mkdir();posts=ET.Element('posts');ET.SubElement(posts,'row',Id='1',OwnerUserId='a')
        history=ET.Element('posthistory')
        values=[(2,'a','old text',''),(5,'a','old text corrected','fix grammar'),
                (5,'b','old text corrected added','added detail'),(5,None,'anonymous changed text','fix spelling')]
        for i,(kind,user,text,comment) in enumerate(values):
            attrs=dict(Id=str(i),PostId='1',PostHistoryTypeId=str(kind),CreationDate=f'2020-01-01T00:00:0{i}',Text=text,Comment=comment)
            if user:attrs['UserId']=user
            ET.SubElement(history,'row',**attrs)
        (members/'Posts.xml').write_bytes(ET.tostring(posts));(members/'PostHistory.xml').write_bytes(ET.tostring(history))
        (members/'Users.xml').write_text('<users>never read this member</users>',encoding='utf8')
        with py7zr.SevenZipFile(archive,'w') as z:
            for name in ('Posts.xml','PostHistory.xml','Users.xml'):z.write(members/name,arcname=name)
        (root/'salt').write_bytes(b's'*32);(root/'license.txt').write_text('Constructed fixture only',encoding='utf8')
    old=(base.ARCHIVES['writers'],base.LICENSE_SHA,safe.execute.__globals__['LICENSE_SHA'])
    base.ARCHIVES['writers']=core.sha(archive);base.LICENSE_SHA=core.sha(root/'license.txt')
    safe.execute.__globals__['LICENSE_SHA']=base.LICENSE_SHA
    args=dict(archive=str(archive),salt=str(root/'salt'),license=str(root/'license.txt'));cfg=dict(phase='prepare',site='writers')
    try:
        if not verifying:
            result=safe.execute(root/'source',args,cfg)
            original=base.execute(root/'original',args,cfg)
            assert result==original
            assert core.sha(root/'source/edits.parquet')==core.sha(root/'original/edits.parquet')
            assert not (root/'source/xml/Users.xml').exists()
            good=root/'source/xml'
            copied=root/'sealed-copy';shutil.copytree(good,copied)
            assert safe.extract(archive,copied)==result['member_sha256']
            for defect in ('truncated','same-size','unsealed','binding','missing'):
                bad=root/defect;shutil.copytree(good,bad)
                target=bad/'Posts.xml'
                if defect=='truncated':target.write_bytes(target.read_bytes()[:-1])
                if defect=='same-size':
                    raw=bytearray(target.read_bytes());raw[-1]^=1;target.write_bytes(raw)
                if defect=='unsealed':(bad/'EXTRACTION.json').unlink()
                if defect=='binding':
                    data=json.loads((bad/'EXTRACTION.json').read_text());data['binding']['archive_sha256']='wrong';core.write(bad/'EXTRACTION.json',data)
                if defect=='missing':target.unlink()
                before={p.name:core.sha(p) for p in bad.iterdir() if p.is_file()}
                refuse(lambda:safe.extract(archive,bad),defect)
                assert before=={p.name:core.sha(p) for p in bad.iterdir() if p.is_file()}
        else:
            fresh=safe.execute(root/'fresh-native-source',args,cfg)
            assert fresh==json.loads((root/'source/SOURCE.json').read_text('utf8'))
            assert core.sha(root/'fresh-native-source/edits.parquet')==core.sha(root/'source/edits.parquet')
        assert safe.verify(root/'source',args,cfg)['verified']
    finally:
        base.ARCHIVES['writers'],base.LICENSE_SHA=old[:2]
        safe.execute.__globals__['LICENSE_SHA']=old[2]
    proof=dict(constructed_only=True,actual_native_7z=True,actual_complete_source_execute_and_fresh_verify=True,
        every_original_projection_row_exact=True,all_member_size_crc_and_sha_verified=True,
        sealed_reentry=True,truncated_same_size_unsealed_wrong_binding_missing_refused=True,
        failed_member_bytes_retained=True,users_member_not_extracted=True,scientific_admission=False)
    if verifying:
        assert json.loads((root/'FIXTURE.json').read_text('utf8'))==proof
        return dict(verified=True,complete_native_source_replay=True)
    core.write(root/'FIXTURE.json',proof);return dict(status='complete',fixture_only=True)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)


if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    began=time.process_time()
    with threadpool_limits(limits=2):value=(verify if args.verify else execute)(Path(args.output),{}, {})
    safe.original.core.write(Path(args.output)/('NATIVE_VERIFY_CPU.json' if args.verify else 'NATIVE_EXECUTE_CPU.json'),dict(cpu_seconds=time.process_time()-began))
    print(json.dumps(value))
