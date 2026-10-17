from runners.drive.cards.batch_runtime_v2 import yield_reason
from runners.stage14.common import atomic


def test_forecast_yield_and_ratified_resume(tmp_path):
    plan = {'forecast_cpu_seconds': 10}
    atomic(tmp_path/'output/FIRST_TENTH.json', {'projected_seconds': 20})
    assert yield_reason(tmp_path, plan) is None
    atomic(tmp_path/'output/FIRST_TENTH.json', {'projected_seconds': 20.01})
    assert yield_reason(tmp_path, plan) == 'first_tenth_projection_exceeds_twice_forecast'
    atomic(tmp_path/'FORECAST_YIELD_SATISFIED.json', {'next_two_dispatched': True})
    assert yield_reason(tmp_path, plan) is None


def test_resource_yield_remains_independent(tmp_path):
    plan = {'forecast_cpu_seconds': 10}
    atomic(tmp_path/'FORECAST_YIELD_SATISFIED.json', {})
    assert yield_reason(tmp_path, plan, {'ram_available_GiB': 3, 'commit_headroom_GiB': 20, 'disk_free_GiB': 100}) == 'resource_floor_yield'
