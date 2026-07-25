Dispatch Assurance
1. Purpose

Dispatch assurance verifies that an authorized response plan remains executable immediately before dispatch.

2. Mandatory Checks
INCIDENT_ACTIVE
LOCATION_SUFFICIENT
REQUIRED_ROLES_FILLED
VOLUNTEERS_CURRENTLY_ELIGIBLE
RESOURCES_CURRENTLY_AVAILABLE
SAFETY_CONDITIONS_ACCEPTABLE
AUTHORITY_CURRENT
COMMUNICATIONS_CONFIRMED
TRANSPORT_AVAILABLE
PLAN_NOT_SUPERSEDED
3. Decision Rule

A plan may be cleared only when every mandatory check is satisfied.

Unknown mandatory checks produce:

INSUFFICIENT_EVIDENCE

or:

HELD_FOR_REVIEW
4. Evidence

Every check must record:

check identifier;
status;
evaluated value;
source;
timestamp;
evidence reference;
explanation.
5. Revalidation Triggers

A cleared plan must be re-evaluated if:

dispatch is delayed beyond its validity window;
personnel changes;
resource conditions change;
incident facts materially change;
new safety information appears;
authority changes;
the plan is modified.