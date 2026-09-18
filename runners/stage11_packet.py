"""Finalize a terminal Stage 11 producer without any model calls.

DESIGN CHECK: complete tranches are compared separately; partials remain
dispositions. Raw semantic replay precedes all public aggregates. Failure,
invalidity and zero-probability losses are retained. No source text is exported.
"""
from collections import Counter
import argparse
from runners.stage11.core import *
from runners.stage11.report import analyze
from runners.stage11.viewer import build


def packet(root=PRIVATE, destination=ROOT):
    if not (root/'COMPLETE.json').exists(): raise ValueError('scientific producer is not terminal')
    result=analyze(root)
    assert analyze(root,False)==result
    contract=read(root/'CONTRACT.json'); prepared=read(root/'PREPARED.json')
    calls=list((root/'calls').rglob('REQUEST.json'));attempts=list((root/'calls').rglob('ATTEMPT.json'))
    statuses=Counter()
    for p in attempts: statuses[(p.parent.parent.name,read(p)['status'])]+=1
    service=sum(read(p.with_name('END.json'))['charged_seconds'] if p.with_name('END.json').exists() else read(p)['reservation_seconds']
                for p in (root/'blocks').glob('*/START.json'))
    integrity=dict(requests=len(calls),retained_attempts=len(attempts),service_seconds=service,
                   within_caps=len(calls)<=contract['total_calls'] and service<=contract['gpu_seconds'],
                   dispositions=[dict(phase=k[0],status=k[1],count=n) for k,n in sorted(statuses.items())],
                   contract=contract,preparation=prepared,
                   semantic_replay=True,comparison_digest=digest(result),
                   source_exclusions=len(read(root/'SOURCE.json')['exclusions']),
                   source_archive='private raw source logs; inherited source identity and exclusions retained')
    if not integrity['within_caps']: raise ValueError('campaign ceiling exceeded')
    try: viewer=build(root)
    except ValueError as exc: viewer=dict(status='UNAVAILABLE',reason=str(exc))
    freeze(destination/'COMPARISONS.json',result);freeze(destination/'INTEGRITY.json',integrity)
    synthetic=bool(attempts) and all(read(p).get('fake') for p in attempts)
    lines=['# Stage 11: retrospective contribution comparison','',
           'SYNTHETIC REHEARSAL ONLY; no scientific evidence.' if synthetic else 'Complete registered human-data tranches; descriptive evidence.', '',
           'Question: does a bounded contribution account recover recorded suggestion handling better than direct reading of the same evidence?',
           '', 'The two evidence views and registered tranches remain separate. Writers are weighted equally after their episodes are averaged. '
           'Half multiclass Brier loss is probability error; lower is better. Accuracy selects the largest probability. Log loss is infinite '
           'when the observed outcome receives zero probability. Invalid forecasts retain Brier loss one and accuracy zero.', '',
           '| Tranche | Evidence | Reader | Episodes | Writers | Components | Brier loss | Accuracy | Log loss | Invalids |',
           '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in result['cells']:
        fmt=lambda x:format(x,'.6f') if isinstance(x,float) else str(x)
        lines.append('| '+' | '.join(fmt(c[k]) for k in ('tranche','view','arm','episodes','writers','components','brier','accuracy','log_loss','invalid_count'))+' |')
    lines += ['', 'The primary observed differences are contribution account minus direct Brier loss; negative favors the account.']
    for c in result['paired']:lines.append(f"- {c['tranche']}, {c['view']}: {c['account_minus_direct_brier']:+.6f}.")
    lines += ['', 'These exposed records provide descriptive comparisons, not fresh human confirmation. Connected dependence components and '
              'observed writer/prompt spreads are in COMPARISONS.json; no population confidence interval is asserted. Handling accuracy '
              'does not validate the account’s goals, dependencies, review claims or values.', '',
              f"Retained requests: {len(calls)}. Charged GPU service: {service/3600:.3f} hours. Preparation, phase dispositions, tokens, latency, "
              'raw-response replay and caps are in INTEGRITY.json and COMPARISONS.json. All original failures remain private.', '',
              'Local contribution viewer: `raw/contribution-map.html`. Its example-selection rule and missing case types are disclosed in the page. '
              'The operation audit is descriptive; unrecognized or unobservable claims remain unresolved. Visual browser QA remains pending if no connected browser is available.', '',
              'Replay without model calls: `python -B -m runners.stage11.run report --verify`.',
              'Build this packet: `python -B -m runners.stage11_packet`.', '',
              'Scientific interpretation and the full theory/FINDINGS landing are a subsequent operator review.']
    text='\n'.join(lines)+'\n';path=destination/'REPORT.md'
    if path.exists() and path.read_text(encoding='utf-8')!=text: raise ValueError('final report changed')
    path.write_text(text,encoding='utf-8',newline='\n')
    freeze(destination/'PACKET_READY.json',dict(status='READY_FOR_OPERATOR_REVIEW',comparison_digest=digest(result),viewer=viewer))
    return dict(status='READY_FOR_OPERATOR_REVIEW',complete_cells=len(result['cells']))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=PRIVATE)
    parser.add_argument('--destination',type=Path,default=ROOT);args=parser.parse_args()
    print(packet(args.root,args.destination))
