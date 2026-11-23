import json
from datetime import timedelta

from runners.drive.cards import week7_gear as gear


def test_companion_slot_survives_week_six_freeze(tmp_path):
    path = tmp_path / 'lease'
    freeze = gear.resources.FREEZE
    start = freeze - timedelta(minutes=15)
    path.write_text(json.dumps({'created_at': start.isoformat(),
                                'expires_at': (start + timedelta(hours=12)).isoformat()}))
    assert gear.shared_slot_limit(freeze, path) == 7
    assert gear.shared_slot_limit(gear.resources.DRAIN, path) == 7
    assert gear.shared_slot_limit(start + timedelta(hours=6), path) == 8
