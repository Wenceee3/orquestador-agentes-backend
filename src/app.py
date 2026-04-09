"""
app.py — Servidor Flask Principal
Regla 1 - Modularización: Rutas organizadas en Blueprints independientes.
Regla 2 - Escalabilidad: Arquitectura lista para crecer en endpoints y módulos.
Regla 3 - Tipado Estricto: Todas las funciones tienen anotaciones de tipo explícitas.
Regla 4 - Acoplamiento Débil: El servidor no depende directamente de la lógica de negocio.
Regla 5 - Manejo de Excepciones: Handler centralizado para todas las excepciones del dominio.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from flask import Flask, Response, jsonify, request

# ---------------------------------------------------------------------------
# Importaciones internas — Acoplamiento Débil (Regla 4)
# ---------------------------------------------------------------------------
sys.path.insert(0, ".")

from config.settings import AppConfig, load_config
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

# ---------------------------------------------------------------------------
# Configuración del logger estructurado
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fábrica de la aplicación — patrón Application Factory (Escalabilidad, Regla 2)
# ---------------------------------------------------------------------------
def create_app(cfg: AppConfig | None = None) -> Flask:
    """
    Crea y configura la instancia de Flask.

    Args:
        cfg: Objeto de configuración. Si es None, carga desde entorno.

    Returns:
        Flask: Aplicación configurada y lista para servir peticiones.
    """
    if cfg is None:
        cfg = load_config()

    app: Flask = Flask(cfg.app_name)
    app.config["ENV"] = cfg.server.environment
    app.config["DEBUG"] = cfg.server.debug

    _register_error_handlers(app)
    _register_blueprints(app)
    _log_startup_info(cfg)

    return app


# ---------------------------------------------------------------------------
# Registro de Blueprints — Modularización (Regla 1)
# ---------------------------------------------------------------------------
def _register_blueprints(app: Flask) -> None:
    """Registra todos los Blueprints de la aplicación."""
    from flask import Blueprint

    # ── /health ──────────────────────────────────────────────────────────────
    health_bp: Blueprint = Blueprint("health", __name__, url_prefix="/health")

    @health_bp.get("/")
    def health_check() -> tuple[Response, int]:
        """Endpoint de liveness/readiness para sistemas de orquestación."""
        payload: dict[str, Any] = {
            "status": "ok",
            "service": app.name,
        }
        return jsonify(payload), 200

    # ── /api/v1/items ─────────────────────────────────────────────────────────
    items_bp: Blueprint = Blueprint("items", __name__, url_prefix="/api/v1/items")

    @items_bp.get("/")
    def list_items() -> tuple[Response, int]:
        """Devuelve la lista de ítems disponibles."""
        items: list[dict[str, Any]] = [
            {"id": 1, "name": "Ítem Alpha", "active": True},
            {"id": 2, "name": "Ítem Beta", "active": False},
        ]
        return jsonify({"data": items, "total": len(items)}), 200

    @items_bp.get("/<int:item_id>")
    def get_item(item_id: int) -> tuple[Response, int]:
        """
        Devuelve un ítem por su ID.

        Raises:
            ResourceNotFoundException: Si el ID no existe.
        """
        # Simulación de búsqueda — reemplazar por capa de servicio real
        mock_store: dict[int, dict[str, Any]] = {
            1: {"id": 1, "name": "Ítem Alpha", "active": True},
        }
        item: dict[str, Any] | None = mock_store.get(item_id)

        if item is None:
            raise ResourceNotFoundException(
                message=f"El ítem con ID '{item_id}' no existe.",
                context={"requested_id": item_id},
            )

        return jsonify({"data": item}), 200

    @items_bp.post("/")
    def create_item() -> tuple[Response, int]:
        """
        Crea un nuevo ítem validando el cuerpo de la petición.

        Raises:
            ValidationException: Si faltan campos obligatorios o son inválidos.
        """
        body: dict[str, Any] | None = request.get_json(silent=True)

        if not body:
            raise ValidationException(
                message="El cuerpo de la petición está vacío o no es JSON válido.",
                context={"content_type": request.content_type},
            )

        name: Any = body.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            raise ValidationException(
                message="El campo 'name' es obligatorio y debe ser una cadena no vacía.",
                context={"received_body": body},
            )

        created_item: dict[str, Any] = {
            "id": 99,
            "name": name.strip(),
            "active": body.get("active", True),
        }
        logger.info("Ítem creado: %s", created_item)
        return jsonify(
            {"data": created_item, "message": "Ítem creado correctamente."}
        ), 201

    # ── /api/v1/demo-errors ───────────────────────────────────────────────────
    demo_bp: Blueprint = Blueprint(
        "demo_errors", __name__, url_prefix="/api/v1/demo-errors"
    )

    @demo_bp.get("/not-found")
    def demo_not_found() -> tuple[Response, int]:
        raise ResourceNotFoundException(
            message="Recurso de demostración no encontrado."
        )

    @demo_bp.get("/validation")
    def demo_validation() -> tuple[Response, int]:
        raise ValidationException(
            message="Error de validación de demostración.",
            context={"field": "email", "rule": "formato inválido"},
        )

    @demo_bp.get("/unauthorized")
    def demo_unauthorized() -> tuple[Response, int]:
        raise AuthenticationException()

    @demo_bp.get("/forbidden")
    def demo_forbidden() -> tuple[Response, int]:
        raise AuthorizationException()

    @demo_bp.get("/conflict")
    def demo_conflict() -> tuple[Response, int]:
        raise ConflictException(message="El recurso ya existe en el sistema.")

    @demo_bp.get("/external-error")
    def demo_external() -> tuple[Response, int]:
        raise ExternalServiceException(
            message="El servicio de base de datos no responde.",
            context={"service": "PostgreSQL", "host": "db.internal"},
        )

    @demo_bp.get("/rate-limit")
    def demo_rate_limit() -> tuple[Response, int]:
        raise RateLimitException()

    # Registro de todos los Blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(demo_bp)


# ---------------------------------------------------------------------------
# Manejadores de errores centralizados — Manejo de Excepciones (Regla 5)
# ---------------------------------------------------------------------------
def _register_error_handlers(app: Flask) -> None:
    """
    Registra handlers globales para todas las excepciones del dominio
    y para errores HTTP estándar de Flask.
    """

    @app.errorhandler(AppBaseException)  # type: ignore[arg-type]
    def handle_app_exception(exc: AppBaseException) -> tuple[Response, int]:
        """Captura cualquier excepción del dominio y devuelve JSON estructurado."""
        body, status = exc.to_response()
        return jsonify(body), status

    @app.errorhandler(404)
    def handle_404(exc: Any) -> tuple[Response, int]:
        return jsonify(
            {
                "error": {
                    "code": "ROUTE_NOT_FOUND",
                    "message": f"La ruta '{request.path}' no existe en este servidor.",
                    "http_status": 404,
                }
            }
        ), 404

    @app.errorhandler(405)
    def handle_405(exc: Any) -> tuple[Response, int]:
        return jsonify(
            {
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": f"El método '{request.method}' no está permitido en '{request.path}'.",
                    "http_status": 405,
                }
            }
        ), 405

    @app.errorhandler(500)
    def handle_500(exc: Any) -> tuple[Response, int]:
        logger.critical("Error interno no controlado: %s", exc, exc_info=True)
        return jsonify(
            {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Error interno del servidor. Contacta al administrador.",
                    "http_status": 500,
                }
            }
        ), 500


# ---------------------------------------------------------------------------
# Logging de arranque
# ---------------------------------------------------------------------------
def _log_startup_info(cfg: AppConfig) -> None:
    """Registra en el log la configuración activa al arrancar."""
    logger.info("=" * 60)
    logger.info("  Aplicación : %s v%s", cfg.app_name, cfg.version)
    logger.info("  Entorno    : %s", cfg.server.environment)
    logger.info("  Dirección  : http://%s:%s", cfg.server.host, cfg.server.port)
    logger.info("  Debug      : %s", cfg.server.debug)
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app_config: AppConfig = load_config()
    flask_app: Flask = create_app(app_config)

    flask_app.run(
        host=app_config.server.host,
        port=app_config.server.port,
        debug=app_config.server.debug,
    )
