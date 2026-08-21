"""Guard tests for the Phase 2.3 shared schemas (process record, contribution network,
anomaly trajectory) and the new reading-profile sections. Run: python tools/test_process_record.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from soundingline.process_record import (                              # noqa: E402
    AnomalyTrajectory, ContributionCollapse, ContributionNetwork, PerceptualAccessViolation,
    ProcessCase, ProcessEvent)
from soundingline.reading_profile import (                             # noqa: E402
    ClaimBoundary, Interface, InterfaceLeak, ReadingProfile)


def _case(events):
    return ProcessCase(case_id="c1", lineage_id="l1", domain="essay", medium="text",
                       brief_id="b1", declared_context={}, participants={"a": "model"},
                       route_family="direct", events=events)


def _profile(interface, **kw):
    return ReadingProfile(artifact_id="a", reader_id="r", reader_config={},
                          interface=interface, declared_context={}, candidate_family="f",
                          baseline_family="echo",
                          claim_boundary=ClaimBoundary(
                              human_coherent_route_supported=False,
                              process_correspondence="unavailable",
                              provenance="not_inferred"), **kw)


def run() -> None:
    failures = []

    def check(name, fn, expect=None):
        try:
            fn()
            ok = expect is None
        except Exception as e:                                        # noqa: BLE001
            ok = expect is not None and isinstance(e, expect)
        (failures.append(name) if not ok else None)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    # 1. a notice event without perceptual access is forbidden (ruling §2.1)
    check("notice-without-access raises",
          lambda: ProcessEvent(event_id="e1", order=0, actor_id="a", operation="notice",
                               perceptual_access=False).validate(),
          PerceptualAccessViolation)

    # 2. exactly one non-recognition event per case
    check("two non-recognition events raise",
          lambda: _case([ProcessEvent("e1", 0, "a", "perceive", noticed=False,
                                      perceptual_access=True),
                         ProcessEvent("e2", 1, "a", "perceive", noticed=False,
                                      perceptual_access=True)]).validate(),
          ValueError)

    # 3. a valid single non-recognition event passes
    check("one non-recognition event passes",
          lambda: _case([ProcessEvent("e1", 0, "a", "perceive", noticed=False,
                                      perceptual_access=True)]).validate())

    # 4. unknown operation refused
    check("unknown operation raises",
          lambda: ProcessEvent("e1", 0, "a", "ponder").validate(), ValueError)

    # 5. dangling parent refused
    check("dangling parent raises",
          lambda: _case([ProcessEvent("e1", 0, "a", "propose",
                                      parent_event_ids=["ghost"])]).validate(),
          ValueError)

    # 6. the author-share scalar does not exist
    check("author_share raises",
          lambda: ContributionNetwork("c1", {"a": {"proposal": 1}}).author_share(),
          ContributionCollapse)

    # 7. contribution roles are a fixed vocabulary
    check("unknown role raises",
          lambda: ContributionNetwork("c1", {"a": {"percent_authored": 0.5}}).validate(),
          ValueError)

    # 8. anomaly axes hold vocabulary
    check("bad axis value raises",
          lambda: AnomalyTrajectory("an1", "c1", axes={"handling": "shrug"}).validate(),
          ValueError)

    # 9. blocked access cannot carry a not-noticed awareness label
    check("blocked+not_noticed raises",
          lambda: AnomalyTrajectory("an1", "c1", axes={
              "perceptual_access": "blocked", "awareness": "not_noticed"}).validate(),
          PerceptualAccessViolation)

    # 10. a coherent multilabel trajectory passes
    check("coherent trajectory passes",
          lambda: AnomalyTrajectory("an1", "c1", axes={
              "perceptual_access": "available", "awareness": "noticed",
              "origin": "unintended", "handling": "exploit",
              "final_status": "integrated_downstream"}).validate())

    # 11. observed contribution network is I3: leaking it into an I1 reading raises
    check("I3 contribution section leaks into I1 reading",
          lambda: _profile(Interface.I1_FINAL_ARTIFACT,
                           contribution_network_observed={"a": {"proposal": 1}}
                           ).validate(),
          InterfaceLeak)

    # 12. the reader's own enactable route is I1 and passes there
    check("reader-enactable route valid at I1",
          lambda: _profile(Interface.I1_FINAL_ARTIFACT,
                           reader_enactable_route={"steps": ["outline", "draft"],
                                                   "historical_claim": False}
                           ).validate())

    if failures:
        print(f"\n{len(failures)} FAILURES: {failures}")
        sys.exit(1)
    print("\nall process-record guard tests pass")


if __name__ == "__main__":
    run()
