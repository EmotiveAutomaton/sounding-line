"""The ordinary capped service path changes only its reviewed watcher binding."""
from pathlib import Path
import pytest

CARDS = Path(__file__).resolve().parents[1] / "runners/drive/cards"


@pytest.mark.parametrize("stem,renames", [
    ("week6_policy_services", {"week6_transition_services_v4":"week6_transition_services_v5"}),
    ("week6_runtime_services", {"week6_policy_services_v5":"week6_policy_services_v6",
                                "week6_launch_services_v5":"week6_launch_services_v6"}),
    ("week6_launch_services", {"week6_transition_services_v4":"week6_transition_services_v5",
                               "week6_runtime_services_v5":"week6_runtime_services_v6",
                               "week6_policy_services_v5":"week6_policy_services_v6"}),
])
def test_existing_ordinary_admission_and_accounting_are_preserved(stem, renames):
    original = (CARDS / (stem+"_v5.py")).read_text(encoding="utf8")
    for before, after in renames.items():
        assert before in original
        original = original.replace(before, after)
    assert (CARDS / (stem+"_v6.py")).read_text(encoding="utf8") == original
