Decision Governance
1. Governing Rule

No consequential action may be cleared solely because a prior plan was approved.

Current conditions must be evaluated at decision time.

2. Decision Inputs

A dispatch decision evaluates:

incident status;
location sufficiency;
required role coverage;
volunteer readiness;
resource readiness;
safety conditions;
authority validity;
communications availability;
transportation availability;
supersession status.
3. Decision Outcomes
CLEARED_FOR_DISPATCH
CLEARED_WITH_CONDITIONS
HELD_FOR_REVIEW
BLOCKED
SUPERSEDED
INSUFFICIENT_EVIDENCE
4. Fail-Closed Conditions

The system must not clear dispatch when:

incident is cancelled or closed;
required role is unfilled;
required volunteer is ineligible;
required resource is unavailable;
authority is expired;
plan is superseded;
mandatory evidence is missing;
a required safety condition is false.
5. Human Review

HELD_FOR_REVIEW means automated evaluation cannot safely determine clearance.

It must not be silently converted into approval.

6. Conditions

A conditional clearance must identify:

every condition;
who must satisfy it;
deadline;
revalidation requirement;
invalidation rule.
7. Decision Expiration

Every dispatch clearance must have:

issued time;
validity window;
revalidation trigger;
supersession rule.
8. Explanation

Every decision must produce a machine-readable and human-readable explanation.