class SmartEvalError(Exception):
    """Base error for expected SmartEval failures."""


class InputValidationError(SmartEvalError):
    """Raised when an input source is absent, unsupported, or empty."""
