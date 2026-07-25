"""Run deterministic replay verification for all canonical scenarios."""

from src.scenario import (
    AuthorityExpirationScenarioOrchestrator,
    BlockedVolunteerScenarioOrchestrator,
    InsufficientEvidenceScenarioOrchestrator,
    ResidentialFireScenarioOrchestrator,
    ResourceOvercommitmentScenarioOrchestrator,
    ScenarioReplayEngine,
    SupersededPlanScenarioOrchestrator,
)


def main() -> int:
    scenarios = (
        ResidentialFireScenarioOrchestrator(),
        BlockedVolunteerScenarioOrchestrator(),
        ResourceOvercommitmentScenarioOrchestrator(),
        AuthorityExpirationScenarioOrchestrator(),
        SupersededPlanScenarioOrchestrator(),
        InsufficientEvidenceScenarioOrchestrator(),
    )

    engine = ScenarioReplayEngine()
    all_deterministic = True

    print("HUMANITARIAN CONTINUITY SYSTEM")
    print("SCENARIO REPLAY AND DETERMINISM VERIFICATION")
    print("=" * 62)

    for scenario in scenarios:
        verification = engine.verify(scenario)
        engine.assert_deterministic(verification)

        print(f"Scenario      : {verification.scenario_id}")
        print(f"Decision      : {verification.first.decision}")
        print(f"Fingerprint   : {verification.first.fingerprint}")
        print(f"Deterministic : {verification.deterministic}")
        print()

        all_deterministic = (
            all_deterministic and verification.deterministic
        )

    return 0 if all_deterministic else 1


if __name__ == "__main__":
    raise SystemExit(main())