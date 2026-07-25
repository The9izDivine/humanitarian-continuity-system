from src.scenario import AuthorityExpirationScenarioOrchestrator


def test_expired_authority_blocks_dispatch() -> None:
    result = AuthorityExpirationScenarioOrchestrator().run()

    assert result.dispatch_decision.decision == "BLOCKED"
    assert (
        "AUTHORITY_CURRENT"
        in result.dispatch_decision.failed_conditions
    )


def test_other_operational_conditions_remain_satisfied() -> None:
    result = AuthorityExpirationScenarioOrchestrator().run()

    condition_status = {
        condition.condition_id: condition.satisfied
        for condition in result.dispatch_decision.conditions
    }

    assert condition_status["AUTHORITY_CURRENT"] is False
    assert condition_status["INCIDENT_ACTIVE"] is True
    assert condition_status["REQUIRED_ROLES_FILLED"] is True
    assert condition_status["VOLUNTEERS_CURRENTLY_ELIGIBLE"] is True
    assert condition_status["RESOURCES_CURRENTLY_AVAILABLE"] is True


def test_expired_authority_has_no_valid_until() -> None:
    result = AuthorityExpirationScenarioOrchestrator().run()

    assert result.dispatch_decision.valid_until is None


def test_reconstruction_preserves_authority_failure() -> None:
    result = AuthorityExpirationScenarioOrchestrator().run()

    assert result.reconstruction_report.decision == "BLOCKED"
    assert (
        "AUTHORITY_CURRENT"
        in result.reconstruction_report.failed_conditions
    )

    authority_condition = next(
        condition
        for condition in result.reconstruction_report.conditions
        if condition.condition_id == "AUTHORITY_CURRENT"
    )

    assert authority_condition.status == "FAILED"


def test_authority_expiration_scenario_is_deterministic() -> None:
    first = AuthorityExpirationScenarioOrchestrator().run()
    second = AuthorityExpirationScenarioOrchestrator().run()

    assert first == second