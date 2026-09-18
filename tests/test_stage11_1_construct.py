from runners.stage11_1.construct import twins


def test_all_executed_twins_share_all_blind_fields_but_not_source():
    rows=twins();assert len(rows)==48
    for a,b in zip(rows[::2],rows[1::2]):
        assert a['views']==b['views']
        assert a['observations']['insertion']['source']!=b['observations']['insertion']['source']
        assert a['cues']['misleading']==b['cues']['true']
        assert a['target']['facts'][1]['actor']=='model'
        assert b['target']['facts'][1]['actor']=='unknown'
