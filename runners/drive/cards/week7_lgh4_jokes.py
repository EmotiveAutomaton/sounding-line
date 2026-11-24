"""Bind the normalized MRDA j tag to native meeting seconds."""
from bisect import bisect_left
import math
from pathlib import PurePosixPath
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile


def joke_ends(archive):
    ends = {}
    seen = set()
    with ZipFile(archive) as bundle:
        for name in bundle.namelist():
            path = PurePosixPath(name)
            if path.parent.as_posix() != 'ICSI/DialogueActs' or not name.endswith('.dialogue-acts.xml'):
                continue
            meeting = path.name.split('.')[0]
            times = ends.setdefault(meeting, [])
            for row in ET.fromstring(bundle.read(name)):
                if row.tag != 'dialogueact':
                    raise ValueError('Unexpected dialogue-act record')
                tag = row.get('type') or row.attrib['original-type']
                if 'j' not in re.findall(r'[A-Za-z0-9]+', tag):
                    continue
                key = row.attrib['{http://nite.sourceforge.net/}id']
                if key in seen:
                    raise ValueError('Duplicate annotated joke')
                seen.add(key)
                start, end = float(row.attrib['starttime']), float(row.attrib['endtime'])
                if not math.isfinite(end) or not 0 <= start <= end:
                    raise ValueError('Unbound joke clock')
                times.append(end)
    return {meeting: sorted(times) for meeting, times in ends.items()}


def follows_joke(onset, ordered_ends):
    first = bisect_left(ordered_ends, onset - 3)
    return first < len(ordered_ends) and ordered_ends[first] <= onset


