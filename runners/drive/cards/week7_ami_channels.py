"""LGH1 AMI close-talk binding. Only meeting, local channel and annotation times are used."""
import hashlib
from pathlib import Path
import re
import wave
import xml.etree.ElementTree as ET
import zipfile


def channel_map(archive):
    with zipfile.ZipFile(archive) as bundle:
        root=ET.fromstring(bundle.read('corpusResources/meetings.xml'))
    mapping={}
    for meeting in root.findall('meeting'):
        name=meeting.get('observation','')
        if not re.fullmatch(r'[A-Za-z0-9_]+',name):
            raise ValueError('Invalid recording key')
        for speaker in meeting.findall('speaker'):
            number=speaker.get('channel','')
            if not number.isdecimal():continue
            code=speaker.get('nxt_agent','')
            if not re.fullmatch(r'[A-Za-z0-9_]+',code):raise ValueError('Invalid local channel label')
            recording=f'{name}/{name}.Headset-{int(number)}.wav'
            if recording in mapping:raise ValueError('Ambiguous headset assignment')
            mapping[recording]=(name,code)
    return mapping


def verified_channel(path,expected):
    if path.stat().st_size!=expected['bytes']:raise ValueError('Recording length changed')
    with path.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=expected['sha256']:raise ValueError('Recording digest changed')
        stream.seek(0)
        with wave.open(stream) as wav:
            if wav.getnchannels()!=1 or wav.getcomptype()!='NONE' or not 8000<=wav.getframerate()<=96000:
                raise ValueError('Unsupported headset recording')
            return wav.getnframes()/wav.getframerate()


def intervals(bundle,meeting,agent):
    name=f'words/{meeting}.{agent}.words.xml'
    if name not in bundle.namelist():return None
    root=ET.fromstring(bundle.read(name))
    marked=[];speech=[];untimed=0
    for node in root:
        kind=node.tag.split('}')[-1]
        laugh=kind=='vocalsound' and node.get('type')=='laugh'
        if not laugh and kind!='w':continue
        try:start,end=float(node.attrib['starttime']),float(node.attrib['endtime'])
        except (KeyError,TypeError,ValueError):
            untimed+=int(laugh)
            continue
        if not 0<=start<end<float('inf'):
            untimed+=int(laugh)
            continue
        (marked if laugh else speech).append((start,end))
    return marked,speech,untimed


def complete_meetings(mapping,files):
    available=set(files)
    meetings={}
    for relative,(name,agent) in mapping.items():
        meetings.setdefault(name,set()).add(relative)
    return {name:sorted(channels) for name,channels in meetings.items() if channels<=available}
