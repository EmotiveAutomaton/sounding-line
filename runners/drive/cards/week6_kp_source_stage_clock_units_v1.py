"""Additive authenticated KP projection stage; no source selection or fit change.

DESIGN CHECK: LESSONS2/3/5. Preserve all original joined rows, frozen fit and
exclusions. Exact byte/source/qualification mismatch refuses under every outcome.
The constructed branch is explicit and cannot be consumed as a human capsule.
"""
from pathlib import Path
import gzip
import hashlib
import json
from . import week6_kp_source_clock_units_v1 as original
from . import week6_kp_fixture_source_v1 as fixture
from .timing_d33_supported_stats import NAMES

SCHEMA='KP_SEALED_JOINED_SOURCE_V1'
MAX_JSON_BYTES=512*1024**2
DECISIONS={'frozen_fit':'exact_joint_D33_including_donor',
           'continuation':'total_personal_surprisal',
           'window':'logged_delta_strict_order_ambiguous_excluded',
           'deletion':'user_contiguous_codepoint_delete_any_provenance'}


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def immutable(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('Immutable KP source stage differs')
    else:
        with path.open('xb') as stream:stream.write(data)


def qualification(inputs,config):
    path=Path(inputs['qualification_complete'])
    if original.digest(path)!=config.get('qualification_complete_sha256'):
        raise ValueError('KP original qualification pin differs')
    proof=original.read(path)
    if not (proof.get('status')=='COMPLETE' and proof.get('qualification_status')=='passed'
            and proof.get('expected_cases')==24 and proof.get('verified_cases')==24
            and proof.get('constructed_only') is True):
        raise ValueError('Full original24-case native qualification required')
    return proof


def validate(corpus,kind):
    if set(corpus)!={'rows','frozen_fit','coverage','dispositions','source_completion_sha256'}:
        raise ValueError('Original joined-corpus schema differs')
    rows=corpus['rows'];keys=[(r['session'],r['index']) for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate original evaluation row')
    if rows!=sorted(rows,key=lambda r:(r['writer'],r['session'],r['index'])):
        raise ValueError('Original canonical joined order differs')
    needed=set(NAMES)-{'intercept'}|{'writer','session','index','log_pause',
            'kp1_exclusions','continuation_exclusions','kp3_exclusions'}
    if any(not needed<=set(row) for row in rows):raise ValueError('Missing original fields')
    if kind=='constructed-literal-walsh-v1':
        if corpus!=fixture.corpus():raise ValueError('Literal constructed source changed')
    elif kind!='authenticated-D33':raise ValueError('Unreviewed source kind')
    canonical(corpus)
    return corpus


def project(inputs,config):
    if config.get('owner_reviewed') is not True or config.get('source_decisions')!=DECISIONS:
        raise ValueError('Owner source-stage review/decisions required')
    qualification(inputs,config)
    kind=config.get('source_kind')
    if kind=='constructed-literal-walsh-v1':
        if inputs.get('data_access')!='constructed-fixture-only' or config.get('fixture_only') is not True:
            raise ValueError('Explicit constructed-only source stage required')
        corpus=fixture.corpus()
    elif kind=='authenticated-D33':
        if config.get('fixture_only') is not False or inputs.get('data_access')!='original-D33-only':
            raise ValueError('Real and constructed source modes differ')
        if original.digest(inputs['d33_completion'])!=inputs['d33_completion_sha256']:
            raise ValueError('Original D33 completion pin differs')
        corpus=original.load_authenticated(inputs,decisions=DECISIONS)
    else:raise ValueError('Unknown source-stage mode')
    return validate(corpus,kind)


def execute(output,inputs,config):
    output=Path(output);corpus=project(inputs,config);payload=canonical(corpus)
    if len(payload)>MAX_JSON_BYTES:raise ValueError('Sealed projection exceeds byte bound')
    packed=gzip.compress(payload,mtime=0)
    seal=dict(schema=SCHEMA,source_kind=config['source_kind'],source_decisions=DECISIONS,
        metadata_resolution=original.metadata_resolution(),
        corpus_sha256=hashlib.sha256(packed).hexdigest(),json_sha256=hashlib.sha256(payload).hexdigest(),
        json_bytes=len(payload),rows=len(corpus['rows']),
        source_completion_sha256=corpus['source_completion_sha256'],
        module_pins={str(Path(x).resolve()):original.digest(x)
            for x in (__file__,original.__file__,fixture.__file__)})
    immutable(output/'BINDING.json',canonical(dict(inputs=inputs,config=config)))
    immutable(output/'CORPUS.json.gz',packed);immutable(output/'SEAL.json',canonical(seal))
    return dict(status='complete',source_kind=config['source_kind'],rows=len(corpus['rows']),
                capsule='CORPUS.json.gz',seal='SEAL.json',scientific_admission=False)


def verify(output,inputs,config):
    output=Path(output)
    if original.read(output/'BINDING.json')!=dict(inputs=inputs,config=config):
        raise ValueError('Source-stage replay binding differs')
    replay=output/'fresh-source-replay';execute(replay,inputs,config)
    for name in ('BINDING.json','CORPUS.json.gz','SEAL.json'):
        if original.digest(output/name)!=original.digest(replay/name):
            raise ValueError('Complete source projection replay differs: '+name)
    return dict(verified=True,full_independent_source_projection=True,
                source_kind=config['source_kind'],scientific_admission=False)
