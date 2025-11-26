from typing import Any, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error payload for API responses.

    Fields:
    - status: HTTP status code returned by the server
    - code: machine-readable error code (e.g. "validation_error")
    - message: human-readable short message suitable for displaying
    - details: optional object with additional contextual information
    """

    status: int
    code: str
    message: str
    details: Optional[Any] = None


class StandardErrorWrapper(BaseModel):
    """Top-level wrapper used by most endpoints for error responses.

    Example:
    {
      "success": false,
      "error": { "status": 404, "code": "not_found", "message": "..." }
    }
    """

    success: bool = False
    error: ErrorResponse
