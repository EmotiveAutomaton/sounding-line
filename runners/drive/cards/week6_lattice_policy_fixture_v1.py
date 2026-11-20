"""Constructed mixed-ledger cases and native evidence for Round 29 admissions."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from . import week6_lattice_policy_v1 as policy
from . import week6_limits_extension_v2 as limits
from .batch_runtime import check_files, filehash, read

EXPECTED = (
    'original_kp1_only', 'sibling_card', 'sibling_budget', 'sibling_science',
    'wrong_source', 'wrong_runner', 'no_authority', 'old_plan', 'original_campaign',
    'original_family_readers', 'only_packet_additions', 'actual_shared_charges',
    'campaign_limits_supplement', 'spent_family_stops', 'prior_carry', 'la_keeps_card_cap',
    'ld4_exact_bound', 'LD1_shared_key', 'LD2_shared_key', 'LD3_shared_key',
    'LD4_shared_key', 'LB1_shared_key', 'LB2_shared_key', 'LB3_shared_key',
    'LB4_shared_key', 'LB5_shared_key', 'LB6_shared_key', 'LA6_paid_from_la',
    'LA7_paid_from_la', 'LA8_paid_from_la', 'unrelated_family', 'writing_surrogate',
    'ledger_includes_source_failed_paused_coordination', 'ledger_cap_includes_prep_and_replay',
    'unbound_receipt', 'diary_extension',
)


def run_cases(directory):
    cases = []

    def check(name, value):
        if value is not True:
            raise AssertionError(name)
        cases.append(name)

    def rejects(name, operation):
        try:
            operation()
        except (ValueError, KeyError):
            cases.append(name)
            return
        raise AssertionError(name)

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf8') as stream:
            json.dump(value, stream)

    authority = dict(policy.AUTHORITY_PINS)
    scope = dict(lattice_card='KP1', lattice_policy_version=policy.VERSION, budget_key='KP1',
                 family='KP', module=policy.KP_MODULE, config={'card': 'KP1'},
                 inputs={'data_access': 'original-D33-only'}, pins=authority)
    check('original_kp1_only', policy.review_plan_scope(scope) == ('KP', 90000))
    for name, edits in (('sibling_card', {'lattice_card':'KP2'}), ('sibling_budget', {'budget_key':'KP3'}),
                        ('sibling_science', {'config': {'card':'KP3'}}), ('wrong_runner', {'module':'other'}),
                        ('wrong_source', {'inputs': {'data_access':'other'}}), ('no_authority', {'pins':{}}),
                        ('old_plan', {'lattice_policy_version':'old'})):
        rejects(name, lambda: policy.review_plan_scope(dict(scope, **edits)))
    check('original_campaign', policy.CEILING == 6000000)
    check('original_family_readers', tuple(policy.FAMILY_CEILINGS[x] for x in ('KP','ES','LA')) ==
          (20000, 100000, 450000))
    check('only_packet_additions', policy.FAMILY_ADDITIONS == {'KP':70000,'ES':400000,'LA':60000})
    room = policy.room_from_charges
    check('actual_shared_charges', room('KP',90000,0,5187.140625,{'KP':10759.59375}) == 79240.40625)
    check('campaign_limits_supplement', room('KP',90000,0,0,{'KP':5000,'CH':5994500}) == 500)
    check('spent_family_stops', room('ES',20000,0,0,{'ES':500000}) == 0)
    check('prior_carry', room('ES',10000,2000,350,{'ES':500}) == 7650)
    check('la_keeps_card_cap', room('LA',6000,0,5000,{'LA':480000}) == 1000)
    check('ld4_exact_bound', policy.card_identity('LD4') == ('ES','ES-LD4',10000))
    for card in sorted(policy.DIARY):
        check(card+'_shared_key', policy.card_identity(card) == ('ES','ES-'+card,10000 if card=='LD4' else 20000))
    for card in sorted(policy.LAUGHTER):
        check(card+'_paid_from_la', policy.card_identity(card) == ('LA',card,None))
    rejects('unrelated_family', lambda: policy.card_identity('CH14'))
    rejects('writing_surrogate', lambda: policy.card_identity('KP1b'))
    with TemporaryDirectory(dir=directory) as scratch:
        root = Path(scratch)
        for key, family, ceiling, prep in [('KP1','KP',20000,80), ('KP2','KP',20000,10),
                                          ('ES-LD4','ES',10000,12)]:
            row = dict(campaign='S15-WEEK6',key=key,family=family,revision=1,previous_sha256=None,
                       owner_reviewed=True,ceiling_cpu_seconds=ceiling,prior_campaign_cpu_seconds=0,
                       preparation_cpu_seconds=prep,evidence_pins=authority)
            if key != 'KP2':
                policy.review_budget_scope(row)
            limits.validate_prospective_revision(root,row)
            write(root/'_budgets'/(key+'-r0001.json'),row)
        for key, terminal, used in [('KP1','PAUSED',1700), ('KP2','FAILED',180), ('ES-LD4','COMPLETE',260)]:
            attempt = root/(key+'-attempt')
            write(attempt/'PLAN.json',dict(campaign='S15-WEEK6',family='ES' if key=='ES-LD4' else 'KP',budget_key=key))
            (attempt/'ATTEMPT.claim').touch()
            write(attempt/(terminal+'.json'),{'cpu_seconds':used})
        def bound(key, card, fam):
            receipt = root/'_budgets'/(key+'-r0001.json')
            digest = filehash(receipt)
            return dict(scope,budget_key=key,lattice_card=card,family=fam,budget_receipt=str(receipt),
                        budget_receipt_sha256=digest,pins={**authority,str(receipt):digest})
        kp = bound('KP1','KP1','KP')
        check('ledger_includes_source_failed_paused_coordination',
              policy.available(kp,root) == 90000-(80+10+1700+180+60))
        check('ledger_cap_includes_prep_and_replay', policy.available(bound('ES-LD4','LD4','ES'),root) == 9698)
        rejects('unbound_receipt', lambda: policy.available(dict(kp,budget_receipt_sha256='bad'),root))
        rejects('diary_extension', lambda: policy.review_budget_scope(dict(row,extension={'mode':'s4_double'})))
    return cases


def qualified_native(path):
    from .week6_transition_services_v4 import regular, require_exited
    from .week6_lattice_launch_v1 import MODULES
    from runners.theory_days.launch import closure
    path = regular(Path(path).resolve())
    q = read(path)
    prep = read(path.parent/'PLAN.json')
    if not (path.name=='COMPLETE.json' and q.get('status')=='COMPLETE' and q.get('error') is None
            and q.get('constructed_only') is True and q.get('lease_released') is True
            and q.get('cases')==len(EXPECTED) and prep.get('expected_cases')==len(EXPECTED)
            and prep.get('schema')=='WEEK6_LATTICE_POLICY_QUALIFICATION_V1'
            and prep.get('cost_allocation')=={'KP1':1.0} and prep['source_pins']==q['source_pins']
            and q.get('outputs')):
        raise ValueError('Different or incomplete lattice policy qualification')
    here = policy.REPO/'.agent-state/drive-20261115/full-week-extension/continuous-build-20261120/kp-delivery'
    required = set(closure([*MODULES,'runners.drive.cards.week6_lattice_policy_fixture_v1']))
    required.update({here/'qualify.py',here/'test_lattice_policy.py'})
    if any(q['source_pins'].get(str(p.resolve()))!=filehash(p) for p in required):
        raise ValueError('Lattice qualification source differs')
    check_files(q['source_pins'])
    check_files(q['outputs'])
    if q['outputs'].get(str(path.parent/'PLAN.json'))!=filehash(path.parent/'PLAN.json'):
        raise ValueError('Qualification plan is unbound')
    if not 0 < policy.finite(q['job_usage']['cpu_seconds']) <= policy.finite(q['cpu_seconds']) <= prep['max_cpu_seconds']:
        raise ValueError('Constructed CPU ceiling exceeded')
    require_exited(prep['owner'])
    require_exited(read(path.parent/'CHILD.json')['native'])
    return q
