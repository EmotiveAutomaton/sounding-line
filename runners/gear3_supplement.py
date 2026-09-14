"""The owner's single, payload-bound context supplement; no general retry bypass.

DESIGN CHECK: LESSONS sections 3-5, G3-V6 and owner approval G3R1.7.
Under NULL and ALTERNATIVE, only the approved two original context calls may
consume this exception. Changed payload, money, duration, ownership or a second
invocation refuses before dispatch. Original failed work and costs stay intact.
Successful transport alone never admits a scientific comparison.
"""
import hashlib
import json
from pathlib import Path
import zipfile

from .stage10.contracts import digest

AUTHORIZATION_PATH = 'results/gear3/G3-S10-READER-1/CONTEXT_SUPPLEMENT_AUTHORIZATION.json'
AUTHORIZATION_SHA256 = '6bae0c032956f21c3242a5bf0368ec0f74921ec3281869086dd406ee19f5360a'


def authorization(repo=None):
    repo = Path(__file__).resolve().parents[1] if repo is None else Path(repo)
    raw = (repo / AUTHORIZATION_PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest() != AUTHORIZATION_SHA256:
        raise ValueError('scoped supplement authorization changed or is absent')
    return json.loads(raw)


def verify_payload(repo, bundle, job):
    approved = authorization(repo)
    if (hashlib.sha256(bundle.read_bytes()).hexdigest() != approved['bundle_sha256']
            or digest(job) != approved['job_sha256'] or job['mode'] != 'science'
            or job['blocks'] != ['blocks/' + approved['block'] + '.json']):
        raise ValueError('supplement payload differs from the approved context checks')
    with zipfile.ZipFile(bundle) as archive:
        block = json.loads(archive.read(job['blocks'][0]))
    if (digest(block) != approved['block_sha256'] or block['node'] != 'P'
            or len(block['units']) != approved['units']
            or {u['model'] for u in block['units']} != set(approved['models'])
            or any(u['arm'] != 'R0' for u in block['units'])
            or len({u['task_id'] for u in block['units']}) != 1):
        raise ValueError('supplement must retain both original context units')
    return approved


def verify_reservation(data, approved, *, invocation, node, command, profile,
                       seconds, overhead_cents, cost, approval, cache, recovery_of):
    if approved != authorization():
        raise ValueError('supplement lacks the exact owner authorization')
    expected_profile = {'job_sha256': approved['job_sha256'], 'image': approved['image'],
                        'startup_seconds': approved['startup_seconds']}
    if (invocation != approved['invocation'] or node != approved['node']
            or command != ['runners/gear3.py', 'round1', approved['bundle_sha256']]
            or any(profile.get(k) != v for k, v in expected_profile.items())
            or seconds != approved['seconds'] or overhead_cents != approved['overhead_cents']
            or cost != approved['reservation_cap_cents'] or cache or recovery_of is not None
            or approval != approved['owner_instruction']):
        raise ValueError('reservation differs from the approved scoped supplement')
    parents = [r for r in data['runs'] if r.get('campaign_id') == approved['campaign']
               and r.get('invocation_id') == approved['original_invocation']]
    if (len(parents) != 1 or parents[0]['status'] != 'FAILED'
            or parents[0].get('owner_ended') is not True or parents[0]['node'] != 'P'
            or parents[0].get('recovery_of') is not None
            or parents[0]['command'] != ['runners/gear3.py', 'round1', approved['original_bundle_sha256']]
            or parents[0]['profile'].get('job_sha256') != approved['original_job_sha256']
            or parents[0]['profile'].get('image') != approved['image']):
        raise ValueError('supplement requires the original failed pilot and ended owner')
    if any(r.get('supplement_authorization', {}).get('authorization_id') == approved['authorization_id']
           for r in data['runs']):
        raise ValueError('the one authorized supplement already has a reservation')
