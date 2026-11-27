"""Reconstruct previously disclosed conversation cohorts inside the sealed job."""
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure
from runners.drive.sealed import week8_lkg1 as liking
from runners.drive.sealed import week8_lkg2 as standing


def conversation_rosters(projection, config):
    frame,census = standing.fields(projection,config)
    panel,universe,known = liking.project(frame,config['previous'])
    # LKG2 released only measure 11. Reproduce the membership of its mean
    # reciprocal standing difference before considering a new disclosure.
    keys = ['conversation_id','user_id','partner_id']
    own = frame[keys+['you_think_my_status']]
    partner = frame[keys+['i_think_your_status']]
    joined = own.merge(partner,left_on=keys,right_on=[keys[0],keys[2],keys[1]],
                       suffixes=('_self','_partner'),validate='one_to_one')
    eligible = joined.dropna(subset=['you_think_my_status','i_think_your_status'])
    eligible = eligible.rename(columns={'conversation_id':'conversation','user_id_self':'person'})
    roster = frozenset(panel.merge(eligible,on=['conversation','person'],validate='one_to_one').person)
    if len(roster)!=config['standing_people'] or not roster<=universe:
        raise SealedFailure(14,'Previously released standing cohort could not be reconstructed')
    return universe,[*known,*census,roster]
