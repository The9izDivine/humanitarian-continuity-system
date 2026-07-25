from src.scenario import SupersededPlanScenarioOrchestrator


def test_superseded_plan_produces_superseded_decision() -> None:
    result = SupersededPlanScenarioOrchestrator().run()

    assert result.dispatch_decision.decision == "SUPERSEDED"
    assert (
        "PLAN_NOT_SUPERSEDED"
        in result.dispatch_decision.failed_conditions
    )


def test_superseded_plan_has_no_validity_window() -> None:
    result = SupersededPlanScenarioOrchestrator().run()

    assert result.dispatch_decision.valid_until is None


def test_other_operational_conditions_remain_satisfied() -> None:
    result = SupersededPlanScenarioOrchestrator().run()

    condition_status = {
        condition.condition_id: condition.satisfied
        for condition in result.dispatch_decision.conditions
    }

    assert condition_status["PLAN_NOT_SUPERSEDED"] is False
    assert condition_status["INCIDENT_ACTIVE"] is True
    assert condition_status["REQUIRED_ROLES_FILLED"] is True
    assert condition_status["VOLUNTEERS_CURRENTLY_ELIGIBLE"] is True
    assert condition_status["RESOURCES_CURRENTLY_AVAILABLE"] is True
    assert condition_status["AUTHORITY_CURRENT"] is True


def test_reconstruction_preserves_supersession() -> None:
    result = SupersededPlanScenarioOrchestrator().run()

    assert result.reconstruction_report.decision == "SUPERSEDED"
    assert (
        "PLAN_NOT_SUPERSEDED"
        in result.reconstruction_report.failed_conditions
    )

    condition = next(
        item
        for item in result.reconstruction_report.conditions
        if item.condition_id == "PLAN_NOT_SUPERSEDED"
    )

    assert condition.status == "FAILED"
    assert "PLAN-000002" in condition.explanation


def test_superseded_plan_scenario_is_deterministic() -> None:
    first = SupersededPlanScenarioOrchestrator().run()
    second = SupersededPlanScenarioOrchestrator().run()

    assert first == second