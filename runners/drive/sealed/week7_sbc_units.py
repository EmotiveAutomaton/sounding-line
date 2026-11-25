"""Select timed, single-speaker Santa Barbara laughter and same-room speech references."""
from collections import Counter, defaultdict
from dataclasses import dataclass
import re

import numpy as np

from runners.drive.cards.week7_lgh1_sound_v1 import _bursts, _pitch_and_fraction


BULLET = re.compile(r"\x15(\d+)_(\d+)\x15")
MARK = re.compile(r"(?<![\w@])(?:&=laugh(?:s|ter|ing)?|\(\(\s*laugh(?:s|ter|ing)?\s*\)\)|@+)(?![\w:@])", re.I)
OVERLAP = re.compile(r"⌈|⌉|⌊|⌋|\+<|\[\s*[<>]\d*\s*\]")
PUNCT = re.compile(r"[\s.,!?…:;∝∞↑↓↗↘→≈≋]+")
NON_SPEECH = re.compile(r"&=|\(\(|\[=!|☺|Ἡ|\b(?:xxx|yyy|www)\b|\b0\b", re.I)


@dataclass(frozen=True)
class Unit:
    actor: str
    span: tuple | None
    kind: str
    overlap: bool


def parse(text):
    tiers = []
    active = False
    for line in text.splitlines():
        if line.startswith("*"):
            label, sep, content = line.partition(":")
            if not sep:
                raise ValueError("Invalid CHAT main tier")
            tiers.append([label[1:].strip(),content])
            active = True
        elif active and line[:1] in ("\t"," "):
            tiers[-1][1] += " " + line.strip()
        else:
            active = False
    for actor, content in tiers:
        times = BULLET.findall(content)
        span = None
        if len(times)==1:
            start,end = map(int,times[0])
            if start < end:
                span = (start/1000.,end/1000.)
        cleaned = BULLET.sub("",content)
        marked = MARK.search(cleaned)
        if marked:
            rest = MARK.sub("",OVERLAP.sub("",cleaned))
            kind = "mixed" if PUNCT.sub("",rest) else "laugh"
        elif "Ἡ" in cleaned:
            kind = "mixed"
        elif "@" in cleaned or NON_SPEECH.search(cleaned) or not re.search(r"[^\W\d_]",cleaned):
            kind = "other"
        else:
            kind = "speech"
        yield Unit(actor,span,kind,bool(OVERLAP.search(cleaned)))


def select(units, speaker_keys, duration):
    """Unknown tiers can disqualify overlap. A missing voice clock cannot certify isolation."""
    units = list(units)
    totals = defaultdict(Counter)
    marks, speech, eligible = [], [], []
    references = defaultdict(list)
    bad_clock = any(u.span is None or u.span[1] > duration for u in units)
    timed = sorted((u for u in units if u.span is not None),key=lambda u:u.span)
    collisions = set()
    active = []
    for u in timed:
        active = [v for v in active if v.span[1]>u.span[0]]
        for v in active:
            if v.actor!=u.actor:
                collisions.update([v,u])
        active.append(u)
    for u in units:
        person = speaker_keys.get(u.actor)
        s = totals[person]
        is_mark = u.kind in ("laugh","mixed")
        if is_mark:
            s["marked_units"] += 1
        if u.span is None or u.span[1]>duration:
            if is_mark:s["untimed_or_outside"] += 1
            continue
        start,end=u.span
        if person is None:
            if is_mark:s["unattributed"] += 1
            continue
        event=dict(speaker=person,start=start,end=end)
        if u.kind in ("speech","mixed"):
            speech.append(event)
        if u.kind=="mixed":
            s["mixed"] += 1
        elif u.kind=="laugh":
            marks.append(dict(**event,label="vocal"))
            clean = not (bad_clock or u.overlap or u in collisions)
            eligible.append(clean)
            s["eligible" if clean else "clock_or_overlap"] += 1
        elif u.kind=="speech" and not (bad_clock or u.overlap or u in collisions):
            references[person].append(u.span)
    return marks,eligible,speech,references,totals


def room_samples(wav,span):
    rate=wav.getframerate()
    start,end=(round(rate*t) for t in span)
    if start<0 or end>wav.getnframes() or start>=end or wav.getsampwidth()!=2 or wav.getcomptype()!="NONE" or wav.getnchannels() not in (1,2):
        raise ValueError("Unbound PCM interval")
    wav.setpos(start)
    values=np.frombuffer(wav.readframes(end-start),dtype="<i2")
    if values.size!=(end-start)*wav.getnchannels():
        raise ValueError("Short recording")
    return values.reshape(-1,wav.getnchannels()).mean(axis=1)/32768.


def five_measures(samples,rate,unit_length,reference_pitch):
    pitches, fraction=_pitch_and_fraction(samples,rate)
    relative=float(12*np.log2(np.median(pitches)/reference_pitch)) if len(pitches) and reference_pitch else np.nan
    spread=float(np.ptp(np.quantile(12*np.log2(pitches),[.25,.75]))) if len(pitches) else np.nan
    return [unit_length,_bursts(samples,rate),fraction,relative,spread]


def reference_pitches(wav, references):
    """Pool voiced frames by bound person inside this recording without joining waveforms."""
    baselines = {}
    for person, spans in references.items():
        voiced = []
        for span in spans:
            pitch, _ = _pitch_and_fraction(room_samples(wav, span), wav.getframerate())
            if len(pitch):
                voiced.append(pitch)
        if voiced:
            baselines[person] = float(np.median(np.concatenate(voiced)))
    return baselines

