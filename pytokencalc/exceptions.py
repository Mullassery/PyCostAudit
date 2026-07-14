"""Specific exception types for PyTokenCalc."""


class PyTokenCalcError(Exception):
    """Base exception for PyTokenCalc."""
    pass


class DatabaseError(PyTokenCalcError):
    """Database operation failed."""
    pass


class ConfigurationError(PyTokenCalcError):
    """Configuration is invalid or missing."""
    pass


class ValidationError(PyTokenCalcError):
    """Input validation failed."""
    pass


class AuthenticationError(PyTokenCalcError):
    """Authentication/credentials failed."""
    pass


class APIError(PyTokenCalcError):
    """API call failed."""
    pass


class ProcessingError(PyTokenCalcError):
    """Data processing error."""
    pass


class CalculationError(ProcessingError):
    """Cost calculation error."""
    pass


class ExportError(PyTokenCalcError):
    """Export operation failed."""
    pass
