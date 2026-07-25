class HumanitarianContinuityError(Exception):
    """Base exception."""


class ValidationError(HumanitarianContinuityError):
    """Schema validation failure."""


class PolicyError(HumanitarianContinuityError):
    """Policy evaluation failure."""


class DispatchError(HumanitarianContinuityError):
    """Dispatch decision failure."""