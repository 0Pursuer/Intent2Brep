class Intent2BRepError(Exception):
    """Base exception for predictable pipeline failures."""


class ProviderConfigurationError(Intent2BRepError):
    """Raised when an external model provider is not configured."""


class ProviderExecutionError(Intent2BRepError):
    """Raised when an external model provider fails or returns invalid data."""


class MeshValidationError(Intent2BRepError):
    """Raised when a generated mesh cannot be loaded or inspected."""
