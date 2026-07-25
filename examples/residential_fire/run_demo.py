"""Run the canonical residential-fire demonstration."""

from src.audit import DecisionReconstructionEngine
from src.scenario import ResidentialFireScenarioOrchestrator


def main() -> int:
    result = ResidentialFireScenarioOrchestrator().run()

    print("HUMANITARIAN CONTINUITY SYSTEM")
    print("RESIDENTIAL FIRE RESPONSE ASSURANCE DEMONSTRATION")
    print("=" * 62)
    print(f"Scenario ID       : {result.scenario_id}")
    print(f"World Valid       : {result.validation_report.valid}")
    print(f"Volunteers        : {len(result.volunteer_results)}")
    print(f"Resources         : {len(result.resource_results)}")
    print(f"Dispatch Decision : {result.dispatch_decision.decision}")
    print()

    for volunteer in result.volunteer_results:
        print(
            f"{volunteer.volunteer_id} "
            f"{volunteer.role}: {volunteer.outcome}"
        )

    print()

    for resource in result.resource_results:
        print(
            f"{resource.resource_id}: {resource.outcome} "
            f"({resource.depletion_status})"
        )

    print()
    print(
        DecisionReconstructionEngine.to_text(
            result.reconstruction_report
        )
    )

    return (
        0
        if result.dispatch_decision.decision
        == "CLEARED_FOR_DISPATCH"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())