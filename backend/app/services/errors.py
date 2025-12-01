"""
Service-level error classes for better error handling.
Audit reference: 01_backend_action_plan.md - P2 Service errors
"""


class ServiceError(Exception):
    """Base exception for all service-level errors."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ServiceError):
    """Raised when input validation fails."""
    pass


class DuplicateError(ServiceError):
    """Raised when attempting to create a duplicate resource."""
    pass


# Unused error classes (kept for potential future use):
# class NotFoundError(ServiceError):
#     """Raised when a requested resource is not found."""
#     pass
#
# class ImportError(ServiceError):
#     """Raised when CSV import operations fail."""
#     pass
#
# class ProcessingError(ServiceError):
#     """Raised when data processing fails."""
#     pass
#
# class AuthorizationError(ServiceError):
#     """Raised when user doesn't have permission for an operation."""
#     pass
