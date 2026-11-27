import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from uuid import UUID
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

from runners.drive.sealed import week7_cad2_original as original
from runners.drive.sealed.week7_cad2_build import package
from tests.test_week7_sealed_sound_words import word_fixture, gate


def invented_archive(mount):
    members = []
    source = word_fixture()
    archive = mount/'cad2-aws2020.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
        for i, call in enumerate(source):
            turn = call['turns'][0]
            speaker = turn['speaker']
            items = []
            for j, word in enumerate(turn['words']):
                if j and (j % 7 == 0 or j % 9 == 2):
                    items.append(dict(type='punctuation', alternatives=[dict(content='.' if j%7==0 else ',')]))
                items.append(dict(type='pronunciation', start_time=str(word['start']), end_time=str(word['end']),
                                  alternatives=[dict(content=word['token'])]))
            metadata = dict(createdAt=1600000000000+1000*call['start'], speakers=[
                dict(channel=side,user_id=p,files=[dict(startTimeOffset=0,stopTimeOffset=100000)])
                for side,p in [('L',speaker),('R',f'listener-{i}')]])
            words = dict(results=dict(channel_labels=dict(channels=[dict(channel_label='ch_0',items=items)])))
            for kind, data in [(original.META,json.dumps(metadata)),(original.WORDS,json.dumps(words)),
                               (original.TURNS,f'turn_id,speaker,start,stop,questions,end_question\n0,{speaker},0,100,0,0\n')]:
                name = f'{UUID(int=i+1)}/{kind}'
                raw = data.encode()
                members.append(dict(path=name, bytes=len(raw), sha256=sha256(raw).hexdigest()))
                z.writestr(name,raw)
    def pin(path):
        return (path.stat().st_size, sha256(path.read_bytes()).hexdigest())
    size, digest = pin(archive)
    manifest = mount/'MANIFEST.json'
    manifest.write_text(json.dumps(dict(alias='candor-cad2-aws2020', conversations=len(source),
        provider_original_sha256=original.NATIVE, archive=archive.name, archive_bytes=size,
        archive_sha256=digest, members=members)), 'utf8')
    return {p.name:pin(p) for p in (archive, manifest)},len(source),6


def test_pinned_package_replays_then_rejects_changed_bytes(tmp_path):
    mount=tmp_path/'data'
    out=tmp_path/'out'
    mount.mkdir()
    out.mkdir()
    args=invented_archive(mount)
    job=tmp_path/'job'
    package(job,fixture=args)
    command=[sys.executable,'-I','-B',str(job/'run.py'),str(mount),str(out)]
    subprocess.run(command,check=True)
    gate(out)
    with (out/'support.csv').open() as f:
        support=list(csv.DictReader(f))
    assert [(int(r['n']),int(r['evaluation_words'])) for r in support]==[(18,18*2*35)]
    with (out/'timing.csv').open() as f:
        fitted=list(csv.DictReader(f))
    assert {1,2} <= {int(r['measure']) for r in fitted}
    with (mount/'MANIFEST.json').open('ab') as f:
        f.write(b' ')
    bad=tmp_path/'refused'
    bad.mkdir()
    assert subprocess.run(command[:-1]+[str(bad)]).returncode==11
    assert not list(bad.iterdir())


def test_ambiguous_words_break_a_pause_and_overlapping_words_start_a_fresh_sequence():
    def word(t):
        return dict(type='pronunciation',start_time=t,end_time=t+.2,alternatives=[dict(content='example')])
    data=dict(results=dict(channel_labels=dict(channels=[dict(channel_label='ch_0',items=[
        word(1),word(2),word(3),word(3.1),word(4)])])))
    spans='turn_id,speaker,start,stop\n0,p,0,5\n1,p,1.9,2.4\n'
    turns=original.turns_for_call(data,spans,{'ch_0':'p','ch_1':'q'},5)
    assert [[w['start'] for w in t['words']] for t in turns]==[[1],[3],[3.1,4]]
    with pytest.raises(original.SealedFailure):
        original.turns_for_call(data,spans+'0,p,0,5\n',{'ch_0':'p'},5)
