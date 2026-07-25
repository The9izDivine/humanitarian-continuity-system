Security Policy
Supported Status

The repository is an early public-reference prototype and is not approved for production deployment.

Reporting

Security concerns should be reported privately to the repository owner rather than disclosed through public issues when exploitation or sensitive exposure is possible.

Prohibited Content

Never commit:

passwords;
API tokens;
private keys;
cloud credentials;
database credentials;
real personal information;
internal organizational documents;
protected infrastructure information.
Security Requirements

All contributions must preserve:

deterministic validation;
strict schema boundaries;
input rejection;
auditability;
least privilege;
dependency review;
secret scanning;
explicit error states;
no silent fallback for consequential decisions.