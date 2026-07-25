Data Governance
1. Data Principle

Synthetic data must remain explicitly distinguishable from real operational data.

2. Data Classes
PUBLIC_SYNTHETIC
INTERNAL_SYNTHETIC
RESTRICTED_TEST
PROHIBITED_REAL_DATA
3. Permitted Classes

Version 0.1.0 permits:

PUBLIC_SYNTHETIC
INTERNAL_SYNTHETIC
4. Prohibited Classes

The following are prohibited:

real survivor records;
real volunteer records;
real medical information;
real addresses;
real phone numbers;
real credentials;
real case identifiers;
private organizational records;
authentication secrets.
5. Missing Data

Missing values must be represented explicitly as:

omitted optional fields;
null where schema permits;
an enumerated unknown state;
an evidence deficiency.

Missing data must not be replaced with guessed defaults.

6. Estimated Data

Estimated values must include:

estimate flag;
source;
timestamp;
confidence or qualification;
verification state.
7. Retention

Synthetic demonstration records may be retained for reproducibility.

Generated temporary data should be separated from canonical examples.

8. Provenance

Every material fact should identify:

origin;
author or source;
creation time;
verification status;
evidence reference;
supersession status.