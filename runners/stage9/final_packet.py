"""B04: evidence-bound manual synthesis after the original final audit.

DESIGN CHECK: B03/B04/X11/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: changed evidence, omitted work, incomplete B03, substituted claims or a
post-selected illustration policy refuse scientific closure. ALTERNATIVE: an
explicit operator review binds the complete original audit and committed evidence
to one immutable packet. Known omissions/substitutions must refuse; unchanged
reentry must retain every byte. Bands: discarded pilot packet, audited scientific
packet or refusal. Writing a packet is not internal write-through, delivery,
curator ratification or authorization to choose or execute another stage.
"""
from .live_status import read as read_status
import argparse
from pathlib import Path
import time

from . import packet_review
from .closure_ledger import snapshot
from .common import REPO, ROOT, Units, closure, digest, file_hash, freeze, read
from .confirmation_summary import arguments
from .queue import DISPOSITIONS, inside, validate_manifest, verify_committed, verify_disposition, verify_execution, writer
from .revision_predictions import finish, reentry, sources
from .training_jobs import cell_identity

MODULE = 'runners.stage9.final_packet'


def context(manifest_path, queue_path, own_cell, directory, review_path, scope):
    plan = read(manifest_path); validate_manifest(plan)
    own = plan['jobs'][-1]; prior = {j['id']: j for j in plan['jobs'][:-1]}
    if (own['module'] != MODULE or digest({'manifest_sha256': digest(plan), 'job': own}) != own_cell
            or (REPO / own['produces']).resolve() != directory / 'COMPLETE.json'
            or any((REPO / arguments(own, key)).resolve() != value for key, value in
                   [('--output', directory), ('--manifest', manifest_path), ('--queue', queue_path), ('--review', review_path)])
            or arguments(own, '--scope') != scope):
        raise ValueError('packet must use its exact original final job, paths and scope')
    state = read_status(queue_path / 'STATUS.json')
    if (read(queue_path / 'MANIFEST.json') != plan or state['manifest_sha256'] != digest(plan)
            or set(state['jobs']) != {j['id'] for j in plan['jobs']}):
        raise ValueError('packet requires the complete original queue')
    audits = [j for j in prior.values() if j['module'] == 'runners.stage9.closure_ledger']
    if len(audits) != 1 or audits[0] is not plan['jobs'][-2]:
        raise ValueError('one actual final ledger must immediately precede the packet')
    for key, job in prior.items():
        status = state['jobs'][key]
        if status['status'] == 'COMPLETE':
            verify_committed(queue_path, job, plan, digest(plan))
            done = read(REPO / job['produces'])
            if 'outputs' in done and done['outputs'] != closure([REPO / p for p in done['outputs']['files']]):
                raise ValueError('committed evidence output closure changed')
        elif status['status'] in ('FAILED', 'NOT_RUN'):
            verify_disposition(queue_path, job, status)
        else:
            raise ValueError('packet cannot close on unfinished preceding work')
    audit = audits[0]
    if state['jobs'][audit['id']]['status'] != 'COMPLETE':
        raise ValueError('final audit did not complete')
    audit_path = (REPO / audit['produces']).parent; done = read(audit_path / 'COMPLETE.json')
    audit_cell = digest({'manifest_sha256': digest(plan), 'job': audit})
    ledger = snapshot(manifest_path, queue_path, audit_cell)
    fresh = audit_path / 'fresh-process'; config = read(fresh / 'CONFIG.json')
    execution = verify_execution(fresh / 'EXECUTION.json', config['cell_identity'], plan, audit)
    reproduction = read(audit_path / 'REPRODUCTION.json')
    if (read(audit_path / 'LEDGER.json') != ledger or read(fresh / 'RESULT.json') != ledger
            or reproduction['ledger_sha256'] != digest(ledger)
            or reproduction['execution_sha256'] != file_hash(fresh / 'EXECUTION.json')
            or reproduction['fresh_process'] != read(fresh / 'READY.json')['process']
            or reproduction['loaded_source_files'] != len(execution['loaded_project_sources'])):
        raise ValueError('original separate-process audit no longer reproduces')
    # The scheduler still updates the active reporter's heartbeat. Retain only
    # prior terminal states here; their complete attempt costs are in the ledger.
    return {'plan': plan, 'state': {'jobs': {key: state['jobs'][key] for key in prior}}, 'prior': prior, 'ledger': ledger,
            'audit_done': done, 'audit_path': audit_path, 'audit_cell': audit_cell}


def evidence_map(review, ctx, queue_path):
    pointers = review.get('evidence')
    if not isinstance(pointers, dict) or not pointers:
        raise ValueError('manual packet needs named original evidence')
    for name, pointer in pointers.items():
        packet_review.text(name)
        if not isinstance(pointer, dict) or set(pointer) != {'job', 'path', 'sha256'} or pointer['job'] not in ctx['prior']:
            raise ValueError('packet evidence must name an original preceding producer')
        job = ctx['prior'][pointer['job']]; state = ctx['state']['jobs'][job['id']]
        path = inside(REPO / pointer['path'])
        if state['status'] == 'COMPLETE':
            produce = (REPO / job['produces']).resolve(); done = read(produce)
            allowed = {produce} | {(REPO / p).resolve() for p in done.get('outputs', {}).get('files', {})}
        else:
            allowed = {(queue_path / state['disposition_path']).resolve()}
        if path not in allowed or not path.is_file() or file_hash(path) != pointer['sha256']:
            raise ValueError('packet evidence is absent, changed or outside its original committed producer')
    return pointers


def scientific_gate(review, ctx):
    if review['scope'] == 'pilot':
        return
    ledger = ctx['ledger']; coverage = ledger['coverage_audit']
    if (ctx['audit_done'].get('final_b03_complete') is not True or ledger['remaining_validation']
            or not coverage.get('all_commissioned_cards_mapped') or not coverage.get('all_commissioned_attacks_mapped')
            or ledger.get('public_claims') != review['claims']):
        raise ValueError('scientific packet requires complete B03 and the exact audited public claim roster')


def run(directory, manifest_path, queue_path, review_path, scope):
    start, cpu = time.monotonic(), time.process_time()
    directory, manifest_path, queue_path, review_path = map(inside, (directory, manifest_path, queue_path, review_path))
    if (scope not in ('pilot', 'scientific') or not directory.is_relative_to(ROOT / 'private' / ('final-packet-' + scope))
            or read(manifest_path)['kind'] != ('prelaunch_rehearsal' if scope == 'pilot' else 'science')):
        raise ValueError('packet output differs from its declared scope')
    with writer(directory):
        cell = cell_identity(); ctx = context(manifest_path, queue_path, cell, directory, review_path, scope)
        review = read(review_path); evidence = evidence_map(review, ctx, queue_path)
        packet = packet_review.validate(review, ctx['plan'], evidence, file_hash(ctx['audit_path'] / 'COMPLETE.json'))
        scientific_gate(review, ctx)
        packet.update(audit_cell=ctx['audit_cell'], audit_ledger_sha256=digest(ctx['ledger']),
            coverage=ctx['ledger']['coverage_audit'], resources=ctx['ledger']['resources'],
            execution_jobs=ctx['ledger']['jobs'], disposition_registry=dict(DISPOSITIONS),
            internal_write_through_verified=False, owner_delivery_verified=False, next_stage_authorized=False)
        identity = {'cell_identity': cell, 'operation': 'final-manual-packet-v1', 'scope': scope,
            'source': sources(), 'manifest_sha256': digest(ctx['plan']), 'review_sha256': file_hash(review_path),
            'packet_sha256': digest(packet)}
        Units(directory, identity); old = reentry(directory, identity)
        if old is not None:
            return old
        freeze(directory / 'PACKET.json', packet)
        rendered = packet_review.render(packet); path = directory / 'PACKET.md'
        if path.exists():
            if path.read_bytes() != rendered.encode('utf-8'):
                raise ValueError('partial packet prose changed')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as handle: handle.write(rendered)
        # Catch evidence mutation while rendering; no source material or reader is executed.
        if context(manifest_path, queue_path, cell, directory, review_path, scope) != ctx or read(review_path) != review:
            raise ValueError('packet inputs changed during rendering')
        evidence_map(review, ctx, queue_path)
        return finish(directory, identity, start, cpu, ['PACKET.json', 'PACKET.md'],
            packet_written=True, final_b04_complete=False, internal_write_through_verified=False,
            owner_delivery_verified=False, next_stage_authorized=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('output', 'manifest', 'queue', 'review'): parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args(); run(args.output, args.manifest, args.queue, args.review, args.scope)
