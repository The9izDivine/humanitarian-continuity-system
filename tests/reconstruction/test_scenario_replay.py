import pytest

from src.scenario import (
    AuthorityExpirationScenarioOrchestrator,
    BlockedVolunteerScenarioOrchestrator,
    InsufficientEvidenceScenarioOrchestrator,
    ResidentialFireScenarioOrchestrator,
    ResourceOvercommitmentScenarioOrchestrator,
    ScenarioReplayEngine,
    SupersededPlanScenarioOrchestrator,
)


@pytest.mark.parametrize(
    ("runner", "expected_decision"),
    (
        (
            ResidentialFireScenarioOrchestrator(),
            "CLEARED_FOR_DISPATCH",
        ),
        (
            BlockedVolunteerScenarioOrchestrator(),
            "BLOCKED",
        ),
        (
            ResourceOvercommitmentScenarioOrchestrator(),
            "BLOCKED",
        ),
        (
            AuthorityExpirationScenarioOrchestrator(),
            "BLOCKED",
        ),
        (
            SupersededPlanScenarioOrchestrator(),
            "SUPERSEDED",
        ),
        (
            InsufficientEvidenceScenarioOrchestrator(),
            "INSUFFICIENT_EVIDENCE",
        ),
    ),
)
def test_scenario_replay_is_deterministic(
    runner: object,
    expected_decision: str,
) -> None:
    engine = ScenarioReplayEngine()
    verification = engine.verify(runner)

    engine.assert_deterministic(verification)

    assert verification.deterministic
    assert verification.first.fingerprint
    assert len(verification.first.fingerprint) == 64
    assert verification.first.decision == expected_decision
    assert verification.first == verification.second


def test_distinct_scenarios_have_distinct_fingerprints() -> None:
    engine = ScenarioReplayEngine()

    valid = engine.capture(
        ResidentialFireScenarioOrchestrator()
    )
    blocked = engine.capture(
        BlockedVolunteerScenarioOrchestrator()
    )

    assert valid.scenario_id != blocked.scenario_id
    assert valid.fingerprint != blocked.fingerprint
    assert valid.decision != blocked.decision