"""
src/__init__.py — Paquete principal del módulo fuente.
Expone los componentes principales para facilitar las importaciones.
"""

from src.exceptions import (
    AppBaseException,
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    ExternalServiceException,
    RateLimitException,
    ResourceNotFoundException,
    ValidationException,
)

__all__: list[str] = [
    "AppBaseException",
    "ResourceNotFoundException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "ConflictException",
    "ExternalServiceException",
    "RateLimitException",
]
