"""CAD2 original AWS word times on the reviewed private CANDOR projection.

DESIGN CHECK (2026-11-26)
Lessons read: LESSONS §2 on canonical source units, §3 on controls, §5 on frozen inputs.
Gates, null/alternative/direction: under the null and under the alternative the same file hashes,
channel mapping, published turn intervals, and earlier-session cutoff must
hold. A cross-turn gap can increase the estimated effect by adding turn-taking delays.
Treat a missing or ambiguous word as a break, and never interpolate onset.
A session ending exactly at the target start cannot enter its history. The
constructed clock and full-rebuild tests exercise these directions.
Verdict bands per arm, exhaustive: a wholly positive or wholly negative
interval, an interval containing zero, an unidentified fit, or inadequate
speaker support. An integrity failure yields no scientific verdict.
"""
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
from zipfile import ZipFile

from runners.drive.sealed import week7_cad2
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure

META='metadata.json'
WORDS='transcription/transcribe_output.json'
TURNS='transcription/transcript_audiophile.csv'
CALL=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')
NATIVE='c0d1d8619bc1a35d702c99a082b78aef5aa91205b109bcf4004da5bee96877c9'


def require(condition):
    if not condition:
        raise SealedFailure(11,'Source binding differs')


def number(value):
    try:
        value=float(value)
    except (ValueError,TypeError):
        return None
    return value if math.isfinite(value) else None


def clock(metadata):
    start=metadata['createdAt']
    require(type(start) is int and 10**12<=start<10**13)
    speakers=metadata['speakers']
    require(len(speakers)==2 and {s['channel'] for s in speakers}=={'L','R'})
    sides={('ch_0' if s['channel']=='L' else 'ch_1'):s['user_id'] for s in speakers}
    require(all(isinstance(p,str) and p.strip() for p in sides.values()) and len(set(sides.values()))==2)
    ends=[]
    for speaker in speakers:
        require(speaker['files'])
        for f in speaker['files']:
            a,b=number(f['startTimeOffset']),number(f['stopTimeOffset'])
            require(a is not None and b is not None and 0<=a<=b)
            ends.append(b)
    require(max(ends)>0)
    return start/1000,(start+max(ends))/1000,sides


def turns_for_call(document,turn_csv,sides,duration):
    intervals=defaultdict(list)
    ids=set()
    for row in csv.DictReader(io.StringIO(turn_csv)):
        speaker=row['speaker']
        # Some provider rows describe non-speech; they cannot own a word.
        if speaker not in sides.values():
            continue
        a,b=number(row['start']),number(row['stop'])
        if a is None or b is None or not 0<=a<b:
            continue
        tid=row['turn_id']
        require(tid and tid not in ids)
        ids.add(tid)
        intervals[speaker].append((a,b,tid))
    channels=document['results']['channel_labels']['channels']
    labels=[c['channel_label'] for c in channels]
    require(labels and len(set(labels))==len(labels) and set(labels)<=set(sides))
    result=[]
    for channel in channels:
        speaker=sides[channel['channel_label']]
        spans=sorted(intervals[speaker])
        next_span=0
        active=[]
        sequence=None
        prior_id=None
        last_start=-1
        last_end=-1
        punct=False
        sentence=True
        for item in channel['items']:
            kind=item['type']
            content=item['alternatives'][0]['content']
            require(isinstance(content,str) and content.strip())
            if kind=='punctuation':
                punct=True
                sentence=sentence or any(mark in content for mark in '.?!')
                continue
            require(kind=='pronunciation')
            a,b=number(item.get('start_time')),number(item.get('end_time'))
            if a is None or b is None or not 0<=a<b<=duration+1e-6:
                sequence=None
                sentence=True
                punct=False
                continue
            require(a>=last_start)
            last_start=a
            while next_span<len(spans) and spans[next_span][0]<=a:
                active.append(spans[next_span])
                next_span+=1
            active=[s for s in active if s[1]>a]
            matches=[s[2] for s in active if b<=s[1]]
            if len(matches)!=1:
                sequence=None
                sentence=True
                punct=False
                continue
            tid=matches[0]
            if sequence is None or tid!=prior_id or a<last_end:
                sequence=[]
                result.append(dict(speaker=speaker,words=sequence))
                sentence=True
            sequence.append(dict(token=content,start=a,end=b,
                                 sentence_start=int(sentence),after_punctuation=int(punct)))
            prior_id,last_end=tid,b
            sentence=punct=False
    return result


def checked_path(mount,name,pin):
    path=mount/name
    require(not path.is_symlink() and path.is_file() and path.stat().st_size==pin[0])
    digest=sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            digest.update(chunk)
    require(digest.hexdigest()==pin[1])
    return path


def run(mount,out,pins,call_count=1656,draws=2000):
    mount=Path(mount)
    manifest=json.loads(checked_path(mount,'MANIFEST.json',pins['MANIFEST.json']).read_bytes())
    name='cad2-aws2020.zip'
    archive=checked_path(mount,name,pins[name])
    require(manifest['alias']=='candor-cad2-aws2020' and manifest['conversations']==call_count and
            manifest['provider_original_sha256']==NATIVE and manifest['archive']==name and
            [manifest['archive_bytes'],manifest['archive_sha256']]==list(pins[name]))
    members={m['path']:m for m in manifest['members']}
    require(len(members)==3*call_count==len(manifest['members']))
    with ZipFile(archive) as z:
        require(len(z.infolist())==len(members) and set(z.namelist())==set(members))
        calls=set()
        for member in members:
            call,_,kind=member.partition('/')
            require(CALL.fullmatch(call) and kind in (META,WORDS,TURNS))
            calls.add(call)
        require(len(calls)==call_count)
        def get(call,kind):
            key=call+'/'+kind
            m=members[key]
            require(z.getinfo(key).file_size==m['bytes'] and 0<m['bytes']<=64*1024**2)
            data=z.read(key)
            require(sha256(data).hexdigest()==m['sha256'])
            return data
        times={call:clock(json.loads(get(call,META))) for call in sorted(calls)}
        appearances=Counter(p for _,_,sides in times.values() for p in sides.values())
        # 3 training, 1 calibration and 1 test session are necessary in D33.
        # A rarer speaker still contributes words to everyone else's histories.
        eligible={p for p,n in appearances.items() if n>=5}
        def stream():
            for call in sorted(calls,key=lambda c:(times[c][0],c)):
                start,end,sides=times[call]
                turns=turns_for_call(json.loads(get(call,WORDS)),get(call,TURNS).decode('utf-8-sig'),
                                     sides,end-start)
                yield dict(conversation=call,start=start,end=end,turns=turns)
        return week7_cad2.run(stream(),out,draws,chronological_stream=True,keep_rows_for=eligible)
