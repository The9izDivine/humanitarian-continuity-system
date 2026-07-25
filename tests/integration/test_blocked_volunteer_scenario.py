from src.scenario import BlockedVolunteerScenarioOrchestrator


def test_expired_volunteer_blocks_dispatch() -> None:
    result = BlockedVolunteerScenarioOrchestrator().run()

    outcomes = {
        item.volunteer_id: item.outcome
        for item in result.volunteer_results
    }

    assert outcomes == {
        "VOL-000001": "ELIGIBLE",
        "VOL-000002": "EXPIRED",
    }

    assert result.dispatch_decision.decision == "BLOCKED"
    assert (
        "VOLUNTEERS_CURRENTLY_ELIGIBLE"
        in result.dispatch_decision.failed_conditions
    )


def test_blocked_scenario_reconstruction_is_complete() -> None:
    result = BlockedVolunteerScenarioOrchestrator().run()

    assert result.reconstruction_report.decision == "BLOCKED"
    assert "EV-000033" in result.reconstruction_report.evidence_ids
    assert any(
        "training_status = 'EXPIRED'" in entry
        for entry in result.reconstruction_report.timeline
    )


def test_blocked_scenario_is_deterministic() -> None:
    first = BlockedVolunteerScenarioOrchestrator().run()
    second = BlockedVolunteerScenarioOrchestrator().run()

    assert first == second