"""Constructed five-site EX5 export; no source archive or outside copy."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import shutil
import xml.etree.ElementTree as ET
from . import week5_ex5_v1 as study


def xml_row(**values):
    return ET.tostring(ET.Element('row', {k: str(v) for k, v in values.items()}), encoding='utf-8', xml_declaration=False)+b'\n'


def sources(root, per_site=401, deficient=False):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    salt = root/'constructed_salt.bin'; salt.write_bytes(b'x'*32); infos = []
    for number, site in enumerate(study.SITES):
        count = 399 if deficient and number == 0 else per_site
        path = root/(site+'.xml')
        with path.open('wb') as stream:
            stream.write(b'<?xml version="1.0" encoding="utf-8"?>\n<posts>\n')
            for q in range(count):
                public = q*4+1
                stream.write(xml_row(Id=public, PostTypeId=1, AcceptedAnswerId=public+2, OwnerUserId=10,
                    CreationDate='2020-01-01T00:00:00.000', Score=q, Title='Constructed question',
                    Body='<p>'+'word '*100+'</p><pre><code>x &lt; y</code></pre>'))
                for order in range(3):
                    stream.write(xml_row(Id=public+1+order, PostTypeId=2, ParentId=public, OwnerUserId=20+order,
                        CreationDate=f'2020-01-01T00:00:0{order+1}.000', Score=3-order,
                        Body='<p>Constructed answer.</p>'))
            stream.write(b'</posts>\n')
        infos.append({'site': site, 'xml': str(path.resolve()), 'xml_sha256': study.io.sha(path),
            'bytes': path.stat().st_size, 'salt': str(salt.resolve()), 'salt_sha256': study.io.sha(salt),
            'source_complete': 'constructed-complete-'+site, 'archive_sha256': 'constructed-'+site})
    return infos


@contextmanager
def source_boundary(infos):
    original = study.authenticate
    try:
        def load(inputs, stop):
            for info in infos:
                assert study.io.sha(info['xml']) == info['xml_sha256']
                assert study.io.sha(info['salt']) == info['salt_sha256']
            return infos
        study.authenticate = load
        yield
    finally:
        study.authenticate = original


def chain(output, deficient=False):
    output = Path(output); infos = sources(output/'inputs', deficient=deficient)
    first = output/'pilot'; continuation = output/'continuation'
    small = {'max_new_draws': 1, 'max_wall_seconds': 160}
    full = {'max_new_draws': 10000, 'max_wall_seconds': 160}
    with source_boundary(infos):
        pause = study.execute(first, {}, small)
        assert pause['status'] == 'yielded' and pause['verified'] is False
        original_members = {p.relative_to(first).as_posix(): study.io.sha(p) for p in first.rglob('*') if p.is_file()}
        shutil.copytree(first, continuation)
        done = study.execute(continuation, {}, full)
        assert done['complete_export'] is (not deficient)
        assert study.verify(continuation, {}, small)['verified'] is False
        assert study.verify(continuation, {}, full)['verified'] is True
    assert all(study.io.sha(first/n) == v for n, v in original_members.items())
    if not deficient:
        records = study.seal.read(continuation/'bundle/QUESTIONS.json')
        assert len(records) == 2000
        for site in study.SITES:
            # Independent expected hash ranks, from literal question row ordinals.
            expected = sorted(range(401), key=lambda q: hashlib.sha256(f'EX5|20261112|{site}|{q*4+1}'.encode()).hexdigest())[:400]
            assert [r['question_id'] for r in records if r['site'] == site] == [str(q*4+1) for q in expected]
        assert all(len(r['answers']) == 3 and [a['accepted'] for a in r['answers']] == [False, True, False] for r in records)
        assert all(r['code_block_codepoint_lengths'] == [5] for r in records)
        forbidden = {'owner', 'OwnerUserId', 'author', 'editor', 'user_id', 'prolific_id'}
        assert all(not forbidden & set(r) and all(not forbidden & set(a) for a in r['answers']) for r in records)
    else:
        assert done['status'] == 'unsupported' and not (continuation/'bundle').exists()
    proof = {'passed': True, 'complete_export': not deficient, 'independent_full_parse_and_bundle_replay': True,
        'immutable_pilot_copy_and_reentry': True, 'fixed_expected_selection': not deficient,
        'record_kind': 'run', 'theory_tags': [], 'by_construction': True, 'activation': []}
    study.io.write_json(output/'FIXTURE.json', proof); return proof
