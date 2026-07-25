from src.audit import DecisionReconstructionEngine
from src.scenario import ResidentialFireScenarioOrchestrator


def test_residential_fire_scenario_runs_end_to_end() -> None:
    result = ResidentialFireScenarioOrchestrator().run()

    assert result.scenario_id == "SCENARIO-RESIDENTIAL-FIRE-001"
    assert result.validation_report.valid
    assert len(result.volunteer_results) == 2
    assert len(result.resource_results) == 2
    assert result.dispatch_decision.decision == "CLEARED_FOR_DISPATCH"
    assert result.reconstruction_report.decision == "CLEARED_FOR_DISPATCH"


def test_all_volunteers_are_eligible() -> None:
    result = ResidentialFireScenarioOrchestrator().run()

    assert {
        item.outcome
        for item in result.volunteer_results
    } == {"ELIGIBLE"}


def test_all_resources_are_available() -> None:
    result = ResidentialFireScenarioOrchestrator().run()

    outcomes = {
        item.resource_id: item.outcome
        for item in result.resource_results
    }

    assert outcomes == {
        "RES-000001": "AVAILABLE_WITH_CONDITIONS",
        "RES-000002": "AVAILABLE",
    }


def test_reconstruction_contains_complete_decision() -> None:
    result = ResidentialFireScenarioOrchestrator().run()

    text = DecisionReconstructionEngine.to_text(
        result.reconstruction_report
    )

    assert "DECISION RECONSTRUCTION" in text
    assert "PLAN-000001" in text
    assert "CLEARED_FOR_DISPATCH" in text
    assert "VOLUNTEERS_CURRENTLY_ELIGIBLE" in text
    assert "RESOURCES_CURRENTLY_AVAILABLE" in text


def test_scenario_run_is_deterministic() -> None:
    first = ResidentialFireScenarioOrchestrator().run()
    second = ResidentialFireScenarioOrchestrator().run()

    assert first == second