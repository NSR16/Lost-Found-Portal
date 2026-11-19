"""
services/errors.py
------------------
Framework-independent errors raised by the service layer.
Routers translate them into HTTP responses, so the services never import FastAPI.
"""


class ServiceError(Exception):
    """Base class for all business-rule errors."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    """A referenced record does not exist (HTTP 404)."""


class ForbiddenError(ServiceError):
    """The caller is not allowed to perform the action (HTTP 403)."""


class ValidationError(ServiceError):
    """The request violates a business rule (HTTP 400)."""


class ConflictError(ServiceError):
    """The request conflicts with existing data (HTTP 409)."""
