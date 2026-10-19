"""Authenticate EV final-document inputs; no reader or analysis dispatch.

DESIGN CHECK: LESSONS 2-5 read for the October18 EV build. Complete P2/P5/P6
metadata and byte hashes must identify the same session, writer, prompt and
chronology. Raw replay must reconstruct both final text and all P6 occurrences;
P5's source partition must agree. Changed bytes, resealed false content, missing
or repeated units refuse under both null and alternative scientific worlds.
An upstream roster superset is disclosed, never silently added to the cohort.
Constructed source admission is separate from corpus and reader admission.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from .engine_occurrences import final_document, SCORE_FIELDS
from .cards.timing_revision_source import Sources as RevisionSources, INPUTS as REVISION_INPUTS
from .cards.timing_pmap_source import completed, indexed
from .cards.timing_census import read, filehash

INPUTS = REVISION_INPUTS | {'p5_index', 'p5_completion'}


def bound_json(index_path, row):
    """Hash and decode the same bytes, including compressed source records."""
    root = Path(index_path).resolve().parent
    path = (root / row['file']).resolve()
    path.relative_to(root)
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != row['sha256']:
        raise ValueError('source unit hash changed')
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


class Sources:
    def __init__(self, inputs, *, expected_sessions=1399):
        if set(inputs) != INPUTS or type(expected_sessions) is not int or expected_sessions < 1:
            raise ValueError('exact EV source inputs and population required')
        self.inputs = dict(inputs)
        self.revision = RevisionSources({k: inputs[k] for k in REVISION_INPUTS})
        self.root = self.revision.root
        if len(self.revision.p2) != expected_sessions:
            raise ValueError('EV population differs from frozen count')
        completed(inputs['p5_completion'], inputs['p5_index'])
        binding_path = Path(inputs['p5_index']).parent / 'INPUTS.json'
        completed(inputs['p5_completion'], binding_path)
        binding = read(binding_path)
        for p5_key, source_key in (('p2_index', 'session_index'),
                                  ('sessions', 'prepared_sessions'),
                                  ('source_roster', 'raw_roster')):
            if (Path(binding['paths'][p5_key]).resolve() != Path(inputs[source_key]).resolve()
                    or binding['sha256'][p5_key] != filehash(inputs[source_key])):
                raise ValueError('P5 source metadata differs')
        if (Path(binding['paths']['source_root']).resolve() != self.root
                or binding['config']['expected_sessions'] != expected_sessions):
            raise ValueError('P5 source root or population differs')
        self.p5 = indexed(inputs['p5_index'])
        if self.p5.keys() != self.revision.p2.keys():
            raise ValueError('P5 population differs')
        self.population = dict(self.revision.population)
        self.input_hashes = {k: filehash(v) for k, v in sorted(inputs.items()) if k != 'repo_root'}

    def session(self, sid):
        r, i = self.revision, self.inputs
        p2 = bound_json(i['session_index'], r.p2[sid])
        p5 = bound_json(i['p5_index'], self.p5[sid])
        p6 = bound_json(i['p6_index'], r.p6[sid])
        meta, raw = r.meta[sid], r.raw[sid]
        identity = (sid, r.p2[sid]['writer'], p2['prompt'])
        for value in (p2, p5, p6, meta):
            if (value['session'], value['writer'], value['prompt']) != identity:
                raise ValueError('EV source identity differs')
        for value in (p5, p6):
            if (value['timestamp'], value['end_at']) != (meta['timestamp'], meta['end_at']):
                raise ValueError('EV source chronology differs')
        if p5['p2_sha256'] != r.p2[sid]['sha256']:
            raise ValueError('P5/P2 binding differs')
        path = (self.root / raw['path']).resolve()
        path.relative_to(self.root)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if any(h != digest for h in (raw['source_sha256'], p2['source_sha256'],
                                    p5['source_sha256'], r.pins.get(path.relative_to(self.root).as_posix()))):
            raise ValueError('raw EV source differs')
        events = [json.loads(line) for line in data.decode('utf8').splitlines()]
        if any(not SCORE_FIELDS <= word.keys() for word in p6['words']):
            raise ValueError('P6 occurrence lacks frozen score fields')
        final_hash = hashlib.sha256(p2['final_document'].encode('utf8')).hexdigest()
        if p5['final_sha256'] != final_hash:
            raise ValueError('P5 final document differs')
        value = final_document(events, dict(session=sid, writer=identity[1], prompt=identity[2]),
            expected_final=p2['final_document'], expected_p6=p6['words'], p5_sentences=p5['sentences'])
        value['source_hashes'] = dict(raw=digest, p2=r.p2[sid]['sha256'],
                                     p5=self.p5[sid]['sha256'], p6=r.p6[sid]['sha256'])
        value['chronology'] = dict(timestamp=meta['timestamp'], end_at=meta['end_at'])
        value['production_mapping'] = ('authenticated P2/P5/P6 occurrence input; '
            'D33 primary and exporter span joins remain separate')
        return value
