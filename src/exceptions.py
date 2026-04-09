"""
exceptions.py — Módulo de Manejo de Excepciones Personalizado
Regla 5: Implementa siempre un control de errores robusto y descriptivo.
Principio: Acoplamiento Débil — las excepciones son independientes del servidor.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Optional

# ---------------------------------------------------------------------------
# Configuración del logger del módulo
# ---------------------------------------------------------------------------
logger: logging.Logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclass de payload de error — Tipado Estricto (Regla 3)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ErrorDetail:
    """Representación inmutable y tipada de un error ocurrido en el sistema."""

    code: str
    message: str
    http_status: int
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    context: Optional[dict] = field(default=None)

    def to_dict(self) -> dict:
        """Serializa el detalle del error a un diccionario JSON-serializable."""
        payload: dict = {
            "error": {
                "code": self.code,
                "message": self.message,
                "http_status": self.http_status,
                "timestamp": self.timestamp,
            }
        }
        if self.context:
            payload["error"]["context"] = self.context
        return payload


# ---------------------------------------------------------------------------
# Excepción base — todas las excepciones del dominio heredan de aquí
# ---------------------------------------------------------------------------
class AppBaseException(Exception):
    """
    Excepción raíz de la aplicación.

    Proporciona un contrato común para todas las excepciones del dominio,
    garantizando que siempre exista un código identificador, un mensaje
    descriptivo y un estado HTTP asociado.
    """

    default_code: str = "APP_ERROR"
    default_message: str = "Se produjo un error interno en la aplicación."
    default_http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR.value

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        http_status: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> None:
        resolved_message: str = message or self.default_message
        resolved_code: str = code or self.default_code
        resolved_status: int = http_status or self.default_http_status

        super().__init__(resolved_message)

        self.detail: ErrorDetail = ErrorDetail(
            code=resolved_code,
            message=resolved_message,
            http_status=resolved_status,
            context=context,
        )
        logger.error(
            "[%s] HTTP %s — %s | contexto=%s",
            self.detail.code,
            self.detail.http_status,
            self.detail.message,
            self.detail.context,
        )

    def to_response(self) -> tuple[dict, int]:
        """Devuelve una tupla (body_dict, http_status) lista para Flask/FastAPI."""
        return self.detail.to_dict(), self.detail.http_status


# ---------------------------------------------------------------------------
# Excepciones de dominio específicas — Modularización (Regla 1)
# ---------------------------------------------------------------------------
class ResourceNotFoundException(AppBaseException):
    """El recurso solicitado no existe en el sistema."""

    default_code = "RESOURCE_NOT_FOUND"
    default_message = "El recurso solicitado no fue encontrado."
    default_http_status = HTTPStatus.NOT_FOUND.value


class ValidationException(AppBaseException):
    """Los datos de entrada no superaron la validación del dominio."""

    default_code = "VALIDATION_ERROR"
    default_message = "Los datos proporcionados no son válidos."
    default_http_status = HTTPStatus.UNPROCESSABLE_ENTITY.value


class AuthenticationException(AppBaseException):
    """El usuario no está autenticado o las credenciales son incorrectas."""

    default_code = "AUTHENTICATION_FAILED"
    default_message = "Autenticación fallida. Credenciales inválidas o ausentes."
    default_http_status = HTTPStatus.UNAUTHORIZED.value


class AuthorizationException(AppBaseException):
    """El usuario autenticado no tiene permisos para realizar esta acción."""

    default_code = "AUTHORIZATION_DENIED"
    default_message = "No tienes permisos para realizar esta operación."
    default_http_status = HTTPStatus.FORBIDDEN.value


class ConflictException(AppBaseException):
    """La operación produce un conflicto con el estado actual del recurso."""

    default_code = "RESOURCE_CONFLICT"
    default_message = "El recurso ya existe o produce un conflicto."
    default_http_status = HTTPStatus.CONFLICT.value


class ExternalServiceException(AppBaseException):
    """Un servicio externo (BD, API terceros, etc.) devolvió un error."""

    default_code = "EXTERNAL_SERVICE_ERROR"
    default_message = "Error al comunicarse con un servicio externo."
    default_http_status = HTTPStatus.BAD_GATEWAY.value


class RateLimitException(AppBaseException):
    """El cliente ha superado el límite de peticiones permitidas."""

    default_code = "RATE_LIMIT_EXCEEDED"
    default_message = "Has superado el límite de solicitudes. Intenta más tarde."
    default_http_status = HTTPStatus.TOO_MANY_REQUESTS.value
