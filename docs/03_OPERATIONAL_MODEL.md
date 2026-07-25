# Operational Model

## 1. Purpose

The Humanitarian Continuity System models a humanitarian response as a governed sequence of evidence-bearing state transitions.

The canonical lifecycle is:

```text
INCIDENT
  ↓
NEEDS ASSESSMENT
  ↓
RESPONSE PLAN
  ↓
ELIGIBILITY EVALUATION
  ↓
DISPATCH DECISION
  ↓
FIELD CONFIRMATION
  ↓
ASSISTANCE DELIVERY
  ↓
RECOVERY CONTINUITY
  ↓
AFTER-ACTION RECONSTRUCTION
No later stage may silently rewrite or erase evidence created by an earlier stage.

2. Canonical Objects

The system defines eight primary objects:

Incident
Needs Assessment
Volunteer
Resource
Response Plan
Dispatch Decision
Delivery Record
Recovery Case

Each object has:

a stable identifier;
a creation timestamp;
a current state;
a provenance record;
an evidence basis;
uncertainty representation;
change history;
explicit ownership or authority;
validation requirements.
3. Incident

An Incident represents a reported humanitarian event requiring assessment.

Canonical incident states:

REPORTED
PARTIALLY_VERIFIED
VERIFIED
DUPLICATE
CANCELLED
CLOSED
Incident invariants
REPORTED does not imply factual verification.
PARTIALLY_VERIFIED requires at least one verified material fact.
VERIFIED requires the minimum evidence defined by policy.
DUPLICATE must identify the canonical incident.
CANCELLED must preserve the cancellation basis.
CLOSED must not imply all human needs were resolved.
4. Needs Assessment

A Needs Assessment records reported, observed, verified, authorized, and fulfilled needs.

Canonical need states:

UNASSESSED
REPORTED
OBSERVED
VERIFIED
AUTHORIZED
ASSIGNED
IN_PROGRESS
FULFILLED
PARTIALLY_FULFILLED
UNABLE_TO_FULFILL
REFERRED
UNKNOWN
Need invariants
REPORTED does not imply observation.
OBSERVED does not imply authorization.
REFERRED does not imply fulfillment.
PARTIALLY_FULFILLED must preserve the unresolved portion.
UNKNOWN is an evidence-bearing state.
Case closure must not erase unresolved needs.
5. Volunteer

A Volunteer represents a synthetic response participant.

Canonical readiness states:

ELIGIBLE
CONDITIONALLY_ELIGIBLE
INELIGIBLE
PENDING_VERIFICATION
INSUFFICIENT_INFORMATION
EXPIRED
UNAVAILABLE

Volunteer readiness must be evaluated against a particular role, assignment, incident, and time.

A volunteer is not globally eligible.

6. Resource

A Resource represents a synthetic deployable asset, supply, service, vehicle, accommodation allocation, or support capability.

Canonical resource states:

AVAILABLE
AVAILABLE_WITH_CONDITIONS
RESERVED
IN_TRANSIT
UNVERIFIED
DAMAGED
EXPIRED
DEPLETED
INACCESSIBLE

Recorded quantity and verified deployable quantity must remain distinct.

7. Response Plan

A Response Plan represents a proposed coordinated action.

Canonical plan states:

DRAFT
UNDER_REVIEW
AUTHORIZED
CONDITIONALLY_AUTHORIZED
READY
BLOCKED
DISPATCHED
SUPERSEDED
CANCELLED
COMPLETED

Authorization does not automatically produce readiness.

8. Dispatch Decision

A Dispatch Decision is a time-bound evaluation of whether a response plan may proceed under current evidence and conditions.

Canonical decision states:

CLEARED_FOR_DISPATCH
CLEARED_WITH_CONDITIONS
HELD_FOR_REVIEW
BLOCKED
SUPERSEDED
INSUFFICIENT_EVIDENCE

Every dispatch decision must identify:

evaluated conditions;
satisfied conditions;
failed conditions;
unknown conditions;
decision authority;
decision timestamp;
evidence references;
expiration or revalidation requirements.
9. Delivery Record

A Delivery Record captures actual assistance outcomes.

Canonical delivery states:

DELIVERED
PARTIALLY_DELIVERED
NOT_DELIVERED
REFUSED
REFERRED
REVERSED
UNKNOWN
UNVERIFIED

Planned, assigned, and delivered assistance must remain distinguishable.

10. Recovery Case

A Recovery Case preserves continuity after immediate response.

Canonical recovery states:

FOLLOW_UP_REQUIRED
FOLLOW_UP_SCHEDULED
CONTACT_ATTEMPTED
CONTACT_CONFIRMED
REFERRED_TO_SERVICE
SERVICE_ACCEPTED
SERVICE_DECLINED
NEED_RESOLVED
NEED_UNRESOLVED
CASE_CLOSED
CASE_REOPENED

CASE_CLOSED may coexist historically with unresolved needs and must include its closure basis.

11. Canonical Distinctions

The system must preserve:

REPORT ≠ VERIFICATION
OBSERVATION ≠ AUTHORIZATION
ASSIGNMENT ≠ ELIGIBILITY
RECORDED QUANTITY ≠ VERIFIED AVAILABILITY
AUTHORIZATION ≠ CURRENT READINESS
DISPATCH ≠ ARRIVAL
ARRIVAL ≠ ASSISTANCE DELIVERY
REFERRAL ≠ SERVICE ACCEPTANCE
CASE CLOSURE ≠ NEED RESOLUTION
12. Reconstruction Requirement

Every consequential system outcome must be reconstructable from:

canonical object state;
policy version;
evaluated evidence;
actor or authority;
timestamp;
state-transition history;
failed and unknown conditions;
superseded decisions.