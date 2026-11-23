"""Run LGH1 from original meeting annotations and assigned microphones in memory."""
from collections import Counter, defaultdict
import csv
import io
import wave
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np
from . import week7_ami_channels as ami
from . import week7_icsi_recordings as icsi
from ..sealed.week7_lgh1 import FEATURES, evaluate, heldout_facts
from .week6_sealed_support_v1 import SealedFailure


def ami_transcript(bundle, meeting, assignments, channels, people):
    marks, speech, references, files = [], [], {}, {}
    counts = Counter()
    for relative in channels:
        _, agent = assignments[relative]
        person = people[meeting,agent]
        if not person or person in files:
            raise ValueError('Ambiguous within-meeting assignment')
        files[person] = relative
        values = ami.intervals(bundle,meeting,agent)
        if values is None:
            raise ValueError('Missing AMI annotation stream')
        laughs,words,untimed = values
        counts['untimed_marks'] += untimed
        marks.extend(dict(speaker=person,start=a,end=b,label='vocal') for a,b in laughs)
        speech.extend(dict(speaker=person,start=a,end=b) for a,b in words)
        references[person]=words
    return files, marks, speech, references, {}, counts


def analyze(corpus, archive, inventory, audio_root, decoder, out, progress):
    counts = Counter()
    mixed = defaultdict(Counter)
    features, metadata = [], []
    with ZipFile(archive) as bundle:
        if corpus=='ICSI':
            roster=icsi.editions(bundle)
        elif corpus=='AMI':
            assignments=ami.channel_map(archive)
            roster=ami.complete_meetings(assignments,inventory)
            root=ET.fromstring(bundle.read('corpusResources/meetings.xml'))
            # Opaque source membership only, for whole-person group disclosure.
            people={(m.get('observation'),s.get('nxt_agent')):s.get('global_name')
                    for m in root.findall('meeting') for s in m.findall('speaker')}
        else:
            raise ValueError('Unknown meeting corpus')
        if not roster:
            raise ValueError('No complete meetings')
        for meeting in sorted(roster):
            if corpus=='ICSI':
                channels,marks,speech,reference,shares,support=icsi.transcript(bundle.read(roster[meeting]))
                files={person:f'{meeting}/{channel}.sph' for person,channel in channels.items()}
            else:
                files,marks,speech,reference,shares,support=ami_transcript(
                    bundle,meeting,assignments,roster[meeting],people)
            if any(name not in inventory for name in files.values()):
                raise ValueError('Assigned source channel missing from frozen inventory')
            for person,tally in shares.items():
                mixed[person].update(tally)
            counts.update(support)
            by_person=defaultdict(list)
            for i,event in enumerate(marks):
                by_person[event['speaker']].append((i,event))
            measured={}
            lengths=[]
            for person,relative in files.items():
                path=audio_root/relative
                if corpus=='ICSI':
                    audio,rate=icsi.decode_sphere(path,inventory[relative],decoder)
                else:
                    ami.verified_channel(path,inventory[relative])
                    with wave.open(str(path)) as wav:
                        if wav.getsampwidth()!=2:
                            raise ValueError('Unsupported AMI sample width')
                        rate=wav.getframerate()
                        audio=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2')
                        if len(audio)!=wav.getnframes():
                            raise ValueError('Truncated AMI waveform')
                lengths.append(len(audio)/rate)
                indices=by_person[person]
                if indices:
                    stream=icsi.channel_features(audio,rate,reference.get(person,[]),[v for _,v in indices])
                    for (i,_),values in zip(indices,stream,strict=True):
                        if values is not None:
                            measured[i]=[values[k] for k in FEATURES]
                        else:
                            counts['invalid_audio_interval']+=1
                del audio
                counts['verified_channels']+=1
            if measured:
                facts=heldout_facts(meeting,speech,marks,0.,min(lengths),{})
                if len(facts)!=len(marks):
                    raise ValueError('Annotation and held-out fact orders differ')
                for i in sorted(measured):
                    features.append(measured[i])
                    metadata.append(facts[i])
            counts['meetings']+=1
            progress(dict(meetings=counts['meetings'],total_meetings=len(roster),
                          channels=counts['verified_channels']))
    out.mkdir(exist_ok=True)
    if corpus=='ICSI':
        csv_text=io.StringIO(newline='')
        writer=csv.writer(csv_text,lineterminator='\n')
        writer.writerow(['mixed_share'])
        for fraction in sorted(row['mixed']/row['marks'] for row in mixed.values() if row['marks']):
            writer.writerow([fraction])
        counts['people_without_laughter_marks']=sum(not x['marks'] for x in mixed.values())
        (out/'mixed_share_anonymous.csv').write_text(csv_text.getvalue(),encoding='ascii')
    counts['measured_intervals']=len(features)
    counts['complete_six_measures']=int(np.isfinite(np.asarray(features,dtype=float)).all(1).sum()) if features else 0
    tables=out/'group_tables'
    tables.mkdir()
    table_receipt=None
    try:
        if not features:
            raise SealedFailure(12,'no measured intervals')
        table_receipt=evaluate(features,metadata,tables)
        disposition='aggregate tables'
    except SealedFailure as exc:
        if exc.code!=12:
            raise
        disposition='group comparisons unavailable: '+str(exc)
    return dict(counts=dict(counts),disposition=disposition,tables=table_receipt,
                duration='annotated utterance length' if corpus=='ICSI' else 'timed annotated laugh length',
                limit=icsi.LIMIT if corpus=='ICSI' else 'Only completely delivered meetings in the frozen snapshot.')
