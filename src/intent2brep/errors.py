class Intent2BRepError(Exception):
    """Base exception for predictable pipeline failures."""


class UnderspecifiedIntentError(Intent2BRepError):
    """Raised when geometry would require inventing unspecified dimensions/positions."""


class UnsupportedIntentError(Intent2BRepError):
    """Raised when the request contains geometry outside the current MVP subset."""


class GeometryDomainError(Intent2BRepError):
    """Raised when resolved dimensions cannot form the requested part."""


class ProviderConfigurationError(Intent2BRepError):
    """Raised when an external model provider is not configured."""


class ProviderExecutionError(Intent2BRepError):
    """Raised when an external model provider fails or returns invalid data."""


class MeshValidationError(Intent2BRepError):
    """Raised when a generated mesh cannot be loaded or inspected."""
