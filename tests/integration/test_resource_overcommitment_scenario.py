from src.scenario import ResourceOvercommitmentScenarioOrchestrator


def test_overcommitted_resource_blocks_dispatch() -> None:
    result = ResourceOvercommitmentScenarioOrchestrator().run()

    outcomes = {
        item.resource_id: item.outcome
        for item in result.resource_results
    }

    assert outcomes == {
        "RES-000001": "AVAILABLE_WITH_CONDITIONS",
        "RES-000002": "DEPLETED",
    }

    assert result.dispatch_decision.decision == "BLOCKED"
    assert (
        "RESOURCES_CURRENTLY_AVAILABLE"
        in result.dispatch_decision.failed_conditions
    )


def test_overcommitment_ratio_is_preserved() -> None:
    result = ResourceOvercommitmentScenarioOrchestrator().run()

    overcommitted = next(
        item
        for item in result.resource_results
        if item.resource_id == "RES-000002"
    )

    assert overcommitted.available_quantity == 8.0
    assert overcommitted.requested_quantity == 9.0
    assert overcommitted.depletion_ratio == 1.125
    assert overcommitted.depletion_status == "OVERCOMMITTED"


def test_reconstruction_preserves_resource_failure() -> None:
    result = ResourceOvercommitmentScenarioOrchestrator().run()

    assert result.reconstruction_report.decision == "BLOCKED"
    assert (
        "RESOURCES_CURRENTLY_AVAILABLE"
        in result.reconstruction_report.failed_conditions
    )

    assert any(
        "RES-000002.quantity_verified = 10" in entry
        for entry in result.reconstruction_report.timeline
    )

    assert any(
        "RES-000002.reserved_quantity = 2" in entry
        for entry in result.reconstruction_report.timeline
    )


def test_overcommitment_scenario_is_deterministic() -> None:
    first = ResourceOvercommitmentScenarioOrchestrator().run()
    second = ResourceOvercommitmentScenarioOrchestrator().run()

    assert first == second