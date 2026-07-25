Volunteer Readiness
1. Scope

Volunteer readiness is evaluated for a specific assignment at a specific time.

2. Required Factors
TRAINING_VALID
CREDENTIAL_VALID
BACKGROUND_REQUIREMENT_SATISFIED
CURRENTLY_AVAILABLE
ROLE_MATCH
CONTACTABLE
SUPERVISOR_AUTHORIZED
NO_CONFLICTING_ASSIGNMENT
FATIGUE_ACCEPTABLE
3. Evaluation Formula

A volunteer is eligible only when all mandatory factors are satisfied and no blocking condition exists.

4. Unknown Handling

If a mandatory factor is unknown, the result must be:

PENDING_VERIFICATION

or:

INSUFFICIENT_INFORMATION

It must not default to ELIGIBLE.

5. Expiration

Readiness must be re-evaluated when:

training expires;
availability changes;
assignment changes;
authority changes;
incident requirements change;
the validity window expires.
6. Synthetic Boundary

All Version 0.1.0 volunteer records are fabricated.