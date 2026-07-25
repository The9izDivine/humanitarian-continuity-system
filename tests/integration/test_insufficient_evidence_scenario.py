from src.scenario import InsufficientEvidenceScenarioOrchestrator


def test_missing_resource_evaluations_prevent_clearance() -> None:
    result = InsufficientEvidenceScenarioOrchestrator().run()

    assert result.dispatch_decision.decision == "INSUFFICIENT_EVIDENCE"
    assert (
        "RESOURCES_CURRENTLY_AVAILABLE"
        in result.dispatch_decision.unknown_conditions
    )


def test_missing_evidence_is_unknown_not_failed() -> None:
    result = InsufficientEvidenceScenarioOrchestrator().run()

    assert (
        "RESOURCES_CURRENTLY_AVAILABLE"
        not in result.dispatch_decision.failed_conditions
    )

    condition = next(
        item
        for item in result.dispatch_decision.conditions
        if item.condition_id == "RESOURCES_CURRENTLY_AVAILABLE"
    )

    assert condition.satisfied is None


def test_insufficient_evidence_has_no_validity_window() -> None:
    result = InsufficientEvidenceScenarioOrchestrator().run()

    assert result.dispatch_decision.valid_until is None


def test_reconstruction_preserves_unknown_condition() -> None:
    result = InsufficientEvidenceScenarioOrchestrator().run()

    assert (
        result.reconstruction_report.decision
        == "INSUFFICIENT_EVIDENCE"
    )

    assert (
        "RESOURCES_CURRENTLY_AVAILABLE"
        in result.reconstruction_report.unknown_conditions
    )

    condition = next(
        item
        for item in result.reconstruction_report.conditions
        if item.condition_id == "RESOURCES_CURRENTLY_AVAILABLE"
    )

    assert condition.status == "UNKNOWN"


def test_insufficient_evidence_scenario_is_deterministic() -> None:
    first = InsufficientEvidenceScenarioOrchestrator().run()
    second = InsufficientEvidenceScenarioOrchestrator().run()

    assert first == second