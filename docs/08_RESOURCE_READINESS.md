Resource Readiness
1. Scope

Resource readiness determines whether a recorded resource is presently deployable.

2. Required Factors
QUANTITY_VERIFIED
CONDITION_ACCEPTABLE
LOCATION_ACCESSIBLE
NOT_EXPIRED
NOT_ALREADY_OVERCOMMITTED
TRANSPORT_AVAILABLE
CUSTODY_KNOWN
INSPECTION_CURRENT
3. Quantities

The model distinguishes:

recorded quantity;
verified quantity;
reserved quantity;
committed quantity;
available quantity.
4. Depletion Ratio

For demonstration purposes:

depletion_ratio = committed_quantity / verified_available_quantity

When verified available quantity is zero, any positive commitment is overcommitted.

5. Demonstration Thresholds
0.00–0.49  STABLE
0.50–0.74  ELEVATED
0.75–0.89  CRITICAL
0.90–1.00  EXHAUSTION_IMMINENT
>1.00       OVERCOMMITTED

These thresholds are prototype assumptions and are not external organizational policy.

6. Revalidation

Resource readiness must be recalculated when:

inventory changes;
reservation changes;
condition changes;
location becomes inaccessible;
expiration occurs;
transport becomes unavailable.