"""
setup_project.py — Script de Automatización de Estructura de Proyecto Backend
==============================================================================
Regla 1 - Modularización:  Cada responsabilidad está encapsulada en su propia función.
Regla 2 - Escalabilidad:   La estructura generada soporta crecimiento en módulos y servicios.
Regla 3 - Tipado Estricto: Todas las funciones tienen anotaciones de tipo explícitas.
Regla 4 - Acoplamiento Débil: Cada paso es independiente; fallar uno no bloquea los demás.
Regla 5 - Manejo de Excepciones: Control de errores robusto y descriptivo en cada operación.

Uso:
    python setup_project.py                         # Crea proyecto en el directorio actual
    python setup_project.py --name mi_proyecto      # Crea proyecto en ./mi_proyecto
    python setup_project.py --name mi_proyecto --force  # Sobreescribe si ya existe
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# Configuración del logger
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes — Tipado Estricto (Regla 3)
# ---------------------------------------------------------------------------
SEPARATOR: Final[str] = "=" * 64
OK: Final[str] = "✔"
SKIP: Final[str] = "⚠"
FAIL: Final[str] = "✘"


# ---------------------------------------------------------------------------
# Modelo de resultado — Tipado Estricto (Regla 3)
# ---------------------------------------------------------------------------
@dataclass
class StepResult:
    """Resultado inmutable de un paso de la automatización."""

    name: str
    success: bool
    message: str


@dataclass
class SetupReport:
    """Informe acumulado de todos los pasos ejecutados."""

    project_root: Path
    steps: list[StepResult] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return any(not s.success for s in self.steps)

    def add(self, result: StepResult) -> None:
        self.steps.append(result)

    def print_summary(self) -> None:
        print(f"\n{SEPARATOR}")
        print("  RESUMEN DE LA AUTOMATIZACIÓN")
        print(SEPARATOR)
        for step in self.steps:
            icon: str = OK if step.success else FAIL
            print(f"  {icon}  {step.name:<40} {step.message}")
        print(SEPARATOR)
        if self.has_failures:
            print("  Estado final: FALLIDO — revisa los errores anteriores.")
        else:
            print("  Estado final: EXITOSO — proyecto listo para usar.")
        print(f"{SEPARATOR}\n")


# ---------------------------------------------------------------------------
# Excepciones personalizadas del script — Manejo de Excepciones (Regla 5)
# ---------------------------------------------------------------------------
class SetupException(Exception):
    """Error base del proceso de configuración del proyecto."""

    def __init__(self, step: str, reason: str) -> None:
        self.step = step
        self.reason = reason
        super().__init__(f"[{step}] {reason}")


class DirectoryCreationError(SetupException):
    """No se pudo crear uno o más directorios del proyecto."""


class FileGenerationError(SetupException):
    """No se pudo generar uno o más archivos del proyecto."""


# ---------------------------------------------------------------------------
# Plantillas de archivos — Modularización (Regla 1)
# ---------------------------------------------------------------------------

TEMPLATE_GITIGNORE: Final[str] = """\
# Entornos virtuales
.venv/
venv/
env/

# Caché de Python
__pycache__/
*.py[cod]
*.pyo

# Variables de entorno
.env
.env.*
!.env.example

# IDEs
.vscode/
.idea/
*.swp

# Cobertura de tests
.coverage
htmlcov/
.pytest_cache/

# Distribución
dist/
build/
*.egg-info/
"""

TEMPLATE_ENV_EXAMPLE: Final[str] = """\
# ============================================================
# .env.example — Variables de entorno de la aplicación
# Copia este archivo como .env y ajusta los valores.
# ============================================================

APP_NAME=BackendBoilerplate
APP_VERSION=1.0.0
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=5000
APP_DEBUG=true

# Orígenes permitidos para CORS (separados por coma)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
"""

TEMPLATE_README: Final[str] = """\
# BackendBoilerplate

Proyecto backend generado automáticamente por el **Orquestador de Agentes**.

## Estructura

```
/
├── src/
│   ├── __init__.py       # Exportaciones del paquete
│   ├── app.py            # Servidor Flask (Application Factory)
│   └── exceptions.py     # Excepciones personalizadas del dominio
├── tests/
│   ├── __init__.py
│   └── test_exceptions.py
├── config/
│   ├── __init__.py
│   └── settings.py       # Configuración tipada desde variables de entorno
├── .env.example          # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt
└── setup_project.py      # Este script de automatización
```

## Requisitos

- Python 3.11+
- pip

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\\Scripts\\activate           # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env

# 4. Arrancar el servidor
python src/app.py
```

## Endpoints disponibles

| Método | Ruta                          | Descripción                        |
|--------|-------------------------------|------------------------------------|
| GET    | /health/                      | Liveness check                     |
| GET    | /api/v1/items/                | Listar ítems                       |
| GET    | /api/v1/items/<id>            | Obtener ítem por ID                |
| POST   | /api/v1/items/                | Crear nuevo ítem                   |
| GET    | /api/v1/demo-errors/not-found | Demo: ResourceNotFoundException    |
| GET    | /api/v1/demo-errors/validation| Demo: ValidationException          |
| GET    | /api/v1/demo-errors/unauthorized | Demo: AuthenticationException   |

## Tests

```bash
pytest tests/ -v --cov=src
```

## Principios de Arquitectura aplicados

1. **Modularización** — Blueprints independientes por dominio.
2. **Escalabilidad** — Application Factory pattern listo para crecer.
3. **Tipado Estricto** — Anotaciones de tipo en todas las funciones.
4. **Acoplamiento Débil** — Configuración, excepciones y rutas desacopladas.
5. **Manejo de Excepciones** — Handler centralizado con respuestas JSON estructuradas.
"""

TEMPLATE_TEST_EXCEPTIONS: Final[str] = '''\
"""
tests/test_exceptions.py — Tests unitarios del módulo de excepciones.
Regla 5 - Manejo de Excepciones: Verifica que cada excepción produce
el código HTTP y payload JSON correctos.
"""

from __future__ import annotations

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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


class TestErrorDetail:
    """Verifica la estructura del dataclass ErrorDetail."""

    def test_to_dict_contains_required_keys(self) -> None:
        exc = ResourceNotFoundException(message="No encontrado.")
        body, _ = exc.to_response()
        assert "error" in body
        error = body["error"]
        assert "code" in error
        assert "message" in error
        assert "http_status" in error
        assert "timestamp" in error

    def test_context_included_when_provided(self) -> None:
        exc = ValidationException(
            message="Campo inválido.",
            context={"field": "email"},
        )
        body, _ = exc.to_response()
        assert body["error"]["context"] == {"field": "email"}

    def test_context_absent_when_not_provided(self) -> None:
        exc = ResourceNotFoundException()
        body, _ = exc.to_response()
        assert "context" not in body["error"]


class TestHttpStatusCodes:
    """Verifica que cada excepción produce el código HTTP correcto."""

    @pytest.mark.parametrize(
        "exception_class, expected_status",
        [
            (ResourceNotFoundException, 404),
            (ValidationException, 422),
            (AuthenticationException, 401),
            (AuthorizationException, 403),
            (ConflictException, 409),
            (ExternalServiceException, 502),
            (RateLimitException, 429),
        ],
    )
    def test_http_status(
        self, exception_class: type[AppBaseException], expected_status: int
    ) -> None:
        exc = exception_class()
        _, status = exc.to_response()
        assert status == expected_status, (
            f"{exception_class.__name__} debe devolver HTTP {expected_status}, "
            f"pero devolvió {status}."
        )


class TestExceptionMessages:
    """Verifica que los mensajes personalizados se respetan."""

    def test_custom_message_overrides_default(self) -> None:
        custom_msg = "Este recurso fue eliminado el lunes."
        exc = ResourceNotFoundException(message=custom_msg)
        assert str(exc) == custom_msg
        body, _ = exc.to_response()
        assert body["error"]["message"] == custom_msg

    def test_default_message_used_when_none_provided(self) -> None:
        exc = ResourceNotFoundException()
        assert exc.detail.message == ResourceNotFoundException.default_message

    def test_custom_code_overrides_default(self) -> None:
        exc = AppBaseException(code="MY_CUSTOM_CODE")
        assert exc.detail.code == "MY_CUSTOM_CODE"


class TestExceptionInheritance:
    """Verifica la jerarquía de herencia para el handler centralizado."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            ResourceNotFoundException,
            ValidationException,
            AuthenticationException,
            AuthorizationException,
            ConflictException,
            ExternalServiceException,
            RateLimitException,
        ],
    )
    def test_is_subclass_of_app_base_exception(
        self, exception_class: type[AppBaseException]
    ) -> None:
        assert issubclass(exception_class, AppBaseException), (
            f"{exception_class.__name__} debe heredar de AppBaseException."
        )
'''

TEMPLATE_TEST_INIT: Final[str] = '"""tests/__init__.py — Paquete de tests."""\n'

TEMPLATE_SRC_INIT: Final[str] = '''\
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
'''

TEMPLATE_CONFIG_INIT: Final[str] = '''\
"""
config/__init__.py — Paquete de configuración de la aplicación.
Expone la instancia de configuración global para uso en toda la aplicación.
"""

from config.settings import AppConfig, ServerConfig, config, load_config

__all__: list[str] = [
    "AppConfig",
    "ServerConfig",
    "load_config",
    "config",
]
'''

TEMPLATE_SETTINGS: Final[str] = '''\
"""
Módulo de configuración de la aplicación.
Regla 3 - Tipado Estricto: Todas las propiedades tienen tipos explícitos definidos.
Regla 4 - Acoplamiento Débil: La configuración está aislada del resto del sistema.
"""

import os
from dataclasses import dataclass, field
from typing import Final

DEFAULT_HOST: Final[str] = "0.0.0.0"
DEFAULT_PORT: Final[int] = 5000
DEFAULT_DEBUG: Final[bool] = False
DEFAULT_ENV: Final[str] = "development"


@dataclass(frozen=True)
class ServerConfig:
    """Configuración del servidor HTTP. Inmutable tras su creación."""

    host: str
    port: int
    debug: bool
    environment: str


@dataclass(frozen=True)
class AppConfig:
    """Configuración raíz de la aplicación."""

    app_name: str
    version: str
    server: ServerConfig
    allowed_origins: list[str] = field(default_factory=list)


def load_config() -> AppConfig:
    """Carga la configuración desde variables de entorno con valores por defecto."""
    server = ServerConfig(
        host=os.getenv("APP_HOST", DEFAULT_HOST),
        port=int(os.getenv("APP_PORT", str(DEFAULT_PORT))),
        debug=os.getenv("APP_DEBUG", str(DEFAULT_DEBUG)).lower() == "true",
        environment=os.getenv("APP_ENV", DEFAULT_ENV),
    )
    return AppConfig(
        app_name=os.getenv("APP_NAME", "BackendBoilerplate"),
        version=os.getenv("APP_VERSION", "1.0.0"),
        server=server,
        allowed_origins=os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:3000"
        ).split(","),
    )


config: AppConfig = load_config()
'''

TEMPLATE_EXCEPTIONS: Final[str] = '''\
"""
exceptions.py — Módulo de Manejo de Excepciones Personalizado
Regla 5: Implementa siempre un control de errores robusto y descriptivo.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Optional

logger: logging.Logger = logging.getLogger(__name__)


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


class AppBaseException(Exception):
    """Excepción raíz de la aplicación."""

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
        return self.detail.to_dict(), self.detail.http_status


class ResourceNotFoundException(AppBaseException):
    default_code = "RESOURCE_NOT_FOUND"
    default_message = "El recurso solicitado no fue encontrado."
    default_http_status = HTTPStatus.NOT_FOUND.value


class ValidationException(AppBaseException):
    default_code = "VALIDATION_ERROR"
    default_message = "Los datos proporcionados no son válidos."
    default_http_status = HTTPStatus.UNPROCESSABLE_ENTITY.value


class AuthenticationException(AppBaseException):
    default_code = "AUTHENTICATION_FAILED"
    default_message = "Autenticación fallida. Credenciales inválidas o ausentes."
    default_http_status = HTTPStatus.UNAUTHORIZED.value


class AuthorizationException(AppBaseException):
    default_code = "AUTHORIZATION_DENIED"
    default_message = "No tienes permisos para realizar esta operación."
    default_http_status = HTTPStatus.FORBIDDEN.value


class ConflictException(AppBaseException):
    default_code = "RESOURCE_CONFLICT"
    default_message = "El recurso ya existe o produce un conflicto."
    default_http_status = HTTPStatus.CONFLICT.value


class ExternalServiceException(AppBaseException):
    default_code = "EXTERNAL_SERVICE_ERROR"
    default_message = "Error al comunicarse con un servicio externo."
    default_http_status = HTTPStatus.BAD_GATEWAY.value


class RateLimitException(AppBaseException):
    default_code = "RATE_LIMIT_EXCEEDED"
    default_message = "Has superado el límite de solicitudes. Intenta más tarde."
    default_http_status = HTTPStatus.TOO_MANY_REQUESTS.value
'''

TEMPLATE_APP: Final[str] = '''\
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


def create_app(cfg: AppConfig | None = None) -> Flask:
    """Crea y configura la instancia de Flask (Application Factory)."""
    if cfg is None:
        cfg = load_config()

    app: Flask = Flask(cfg.app_name)
    app.config["ENV"] = cfg.server.environment
    app.config["DEBUG"] = cfg.server.debug

    _register_error_handlers(app)
    _register_blueprints(app)
    _log_startup_info(cfg)

    return app


def _register_blueprints(app: Flask) -> None:
    """Registra todos los Blueprints de la aplicación."""
    from flask import Blueprint

    health_bp: Blueprint = Blueprint("health", __name__, url_prefix="/health")

    @health_bp.get("/")
    def health_check() -> tuple[Response, int]:
        return jsonify({"status": "ok", "service": app.name}), 200

    items_bp: Blueprint = Blueprint("items", __name__, url_prefix="/api/v1/items")

    @items_bp.get("/")
    def list_items() -> tuple[Response, int]:
        items: list[dict[str, Any]] = [
            {"id": 1, "name": "Item Alpha", "active": True},
            {"id": 2, "name": "Item Beta", "active": False},
        ]
        return jsonify({"data": items, "total": len(items)}), 200

    @items_bp.get("/<int:item_id>")
    def get_item(item_id: int) -> tuple[Response, int]:
        mock_store: dict[int, dict[str, Any]] = {
            1: {"id": 1, "name": "Item Alpha", "active": True},
        }
        item: dict[str, Any] | None = mock_store.get(item_id)
        if item is None:
            raise ResourceNotFoundException(
                message=f"El item con ID \'{item_id}\' no existe.",
                context={"requested_id": item_id},
            )
        return jsonify({"data": item}), 200

    @items_bp.post("/")
    def create_item() -> tuple[Response, int]:
        body: dict[str, Any] | None = request.get_json(silent=True)
        if not body:
            raise ValidationException(
                message="El cuerpo de la petición está vacío o no es JSON válido.",
                context={"content_type": request.content_type},
            )
        name: Any = body.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            raise ValidationException(
                message="El campo \'name\' es obligatorio y debe ser una cadena no vacía.",
                context={"received_body": body},
            )
        created: dict[str, Any] = {"id": 99, "name": name.strip(), "active": body.get("active", True)}
        return jsonify({"data": created, "message": "Item creado correctamente."}), 201

    demo_bp: Blueprint = Blueprint("demo_errors", __name__, url_prefix="/api/v1/demo-errors")

    @demo_bp.get("/not-found")
    def demo_not_found() -> tuple[Response, int]:
        raise ResourceNotFoundException(message="Recurso de demostración no encontrado.")

    @demo_bp.get("/validation")
    def demo_validation() -> tuple[Response, int]:
        raise ValidationException(message="Error de validación.", context={"field": "email"})

    @demo_bp.get("/unauthorized")
    def demo_unauthorized() -> tuple[Response, int]:
        raise AuthenticationException()

    @demo_bp.get("/forbidden")
    def demo_forbidden() -> tuple[Response, int]:
        raise AuthorizationException()

    @demo_bp.get("/conflict")
    def demo_conflict() -> tuple[Response, int]:
        raise ConflictException(message="El recurso ya existe.")

    @demo_bp.get("/external-error")
    def demo_external() -> tuple[Response, int]:
        raise ExternalServiceException(
            message="El servicio de base de datos no responde.",
            context={"service": "PostgreSQL"},
        )

    @demo_bp.get("/rate-limit")
    def demo_rate_limit() -> tuple[Response, int]:
        raise RateLimitException()

    app.register_blueprint(health_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(demo_bp)


def _register_error_handlers(app: Flask) -> None:
    """Registra handlers globales para todas las excepciones del dominio."""

    @app.errorhandler(AppBaseException)  # type: ignore[arg-type]
    def handle_app_exception(exc: AppBaseException) -> tuple[Response, int]:
        body, status = exc.to_response()
        return jsonify(body), status

    @app.errorhandler(404)
    def handle_404(exc: Any) -> tuple[Response, int]:
        return jsonify({
            "error": {"code": "ROUTE_NOT_FOUND", "message": f"La ruta \'{request.path}\' no existe.", "http_status": 404}
        }), 404

    @app.errorhandler(405)
    def handle_405(exc: Any) -> tuple[Response, int]:
        return jsonify({
            "error": {"code": "METHOD_NOT_ALLOWED", "message": f"Método \'{request.method}\' no permitido.", "http_status": 405}
        }), 405

    @app.errorhandler(500)
    def handle_500(exc: Any) -> tuple[Response, int]:
        logger.critical("Error interno no controlado: %s", exc, exc_info=True)
        return jsonify({
            "error": {"code": "INTERNAL_SERVER_ERROR", "message": "Error interno del servidor.", "http_status": 500}
        }), 500


def _log_startup_info(cfg: AppConfig) -> None:
    logger.info("=" * 60)
    logger.info("  Aplicación : %s v%s", cfg.app_name, cfg.version)
    logger.info("  Entorno    : %s", cfg.server.environment)
    logger.info("  Dirección  : http://%s:%s", cfg.server.host, cfg.server.port)
    logger.info("  Debug      : %s", cfg.server.debug)
    logger.info("=" * 60)


if __name__ == "__main__":
    app_config: AppConfig = load_config()
    flask_app: Flask = create_app(app_config)
    flask_app.run(
        host=app_config.server.host,
        port=app_config.server.port,
        debug=app_config.server.debug,
    )
'''

TEMPLATE_REQUIREMENTS: Final[str] = """\
# ============================================================
# requirements.txt — Dependencias del Proyecto Backend
# ============================================================

# Servidor Web
flask==3.0.3
flask-restful==0.3.10

# Validación y Tipado en Tiempo de Ejecución
pydantic==2.7.1

# Variables de Entorno
python-dotenv==1.0.1

# Logging Estructurado
structlog==24.1.0

# Testing
pytest==8.2.0
pytest-cov==5.0.0

# Utilidades HTTP
requests==2.32.2
"""

# ---------------------------------------------------------------------------
# Definición de la estructura del proyecto — Escalabilidad (Regla 2)
# ---------------------------------------------------------------------------
PROJECT_STRUCTURE: Final[dict[str, str | None]] = {
    # Directorios (valor None = solo crear carpeta)
    "src": None,
    "tests": None,
    "config": None,
    # Archivos raíz
    ".gitignore": TEMPLATE_GITIGNORE,
    ".env.example": TEMPLATE_ENV_EXAMPLE,
    "README.md": TEMPLATE_README,
    "requirements.txt": TEMPLATE_REQUIREMENTS,
    # Paquete src/
    "src/__init__.py": TEMPLATE_SRC_INIT,
    "src/app.py": TEMPLATE_APP,
    "src/exceptions.py": TEMPLATE_EXCEPTIONS,
    # Paquete config/
    "config/__init__.py": TEMPLATE_CONFIG_INIT,
    "config/settings.py": TEMPLATE_SETTINGS,
    # Paquete tests/
    "tests/__init__.py": TEMPLATE_TEST_INIT,
    "tests/test_exceptions.py": TEMPLATE_TEST_EXCEPTIONS,
}


# ---------------------------------------------------------------------------
# Funciones de setup — Modularización (Regla 1)
# ---------------------------------------------------------------------------


def _resolve_project_root(name: str) -> Path:
    """
    Resuelve la ruta raíz del proyecto a crear.

    Args:
        name: Nombre del proyecto (puede ser '.' para el directorio actual).

    Returns:
        Path absoluto del directorio raíz.
    """
    if name == ".":
        return Path.cwd()
    return Path.cwd() / name


def _prepare_root_directory(root: Path, force: bool) -> StepResult:
    """
    Crea o valida el directorio raíz del proyecto.

    Args:
        root:  Ruta del directorio raíz.
        force: Si True, elimina el directorio existente antes de crearlo.

    Returns:
        StepResult con el resultado de la operación.

    Raises:
        DirectoryCreationError: Si ocurre un error al crear el directorio.
    """
    step_name: str = "Directorio raíz"
    try:
        if root.exists():
            if force:
                shutil.rmtree(root)
                logger.info("%s Eliminado directorio existente: %s", SKIP, root)
            else:
                return StepResult(
                    name=step_name,
                    success=True,
                    message=f"Ya existe, reutilizando: {root.name}",
                )
        root.mkdir(parents=True, exist_ok=True)
        return StepResult(name=step_name, success=True, message=f"Creado: {root}")
    except OSError as exc:
        raise DirectoryCreationError(step_name, str(exc)) from exc


def _create_directories(
    root: Path, structure: dict[str, str | None]
) -> list[StepResult]:
    """
    Crea los directorios definidos en la estructura del proyecto.

    Args:
        root:      Raíz del proyecto.
        structure: Mapa de rutas relativas a contenido (None = directorio).

    Returns:
        Lista de StepResult por cada directorio procesado.
    """
    results: list[StepResult] = []

    for relative_path, content in structure.items():
        if content is not None:
            continue  # Es un archivo, no un directorio

        target: Path = root / relative_path
        try:
            target.mkdir(parents=True, exist_ok=True)
            results.append(
                StepResult(
                    name=f"Directorio /{relative_path}",
                    success=True,
                    message="Creado",
                )
            )
            logger.info("%s  Directorio creado: %s", OK, target)
        except OSError as exc:
            results.append(
                StepResult(
                    name=f"Directorio /{relative_path}",
                    success=False,
                    message=f"ERROR: {exc}",
                )
            )
            logger.error("%s  No se pudo crear %s: %s", FAIL, target, exc)

    return results


def _generate_files(root: Path, structure: dict[str, str | None]) -> list[StepResult]:
    """
    Genera los archivos del proyecto a partir de las plantillas.

    Args:
        root:      Raíz del proyecto.
        structure: Mapa de rutas relativas a contenido (str = archivo).

    Returns:
        Lista de StepResult por cada archivo procesado.

    Raises:
        FileGenerationError: Si ocurre un error crítico al escribir archivos.
    """
    results: list[StepResult] = []

    for relative_path, content in structure.items():
        if content is None:
            continue  # Es un directorio, ya procesado

        target: Path = root / relative_path
        try:
            # Garantiza que el directorio padre existe
            target.parent.mkdir(parents=True, exist_ok=True)

            if target.exists():
                results.append(
                    StepResult(
                        name=relative_path,
                        success=True,
                        message="Ya existía, omitido",
                    )
                )
                logger.warning("%s  Archivo omitido (ya existe): %s", SKIP, target)
                continue

            target.write_text(content, encoding="utf-8")
            results.append(
                StepResult(name=relative_path, success=True, message="Generado")
            )
            logger.info("%s  Archivo generado: %s", OK, target)

        except OSError as exc:
            results.append(
                StepResult(
                    name=relative_path,
                    success=False,
                    message=f"ERROR: {exc}",
                )
            )
            logger.error("%s  No se pudo generar %s: %s", FAIL, target, exc)

    return results


def _print_next_steps(root: Path) -> None:
    """Imprime las instrucciones de uso tras la generación exitosa."""
    is_current_dir: bool = root == Path.cwd()
    cd_cmd: str = "" if is_current_dir else f"cd {root.name} && "

    print(f"""
{SEPARATOR}
  COMANDOS PARA COMENZAR
{SEPARATOR}

  # 1. Crear y activar el entorno virtual
  python -m venv .venv
  source .venv/bin/activate          # Linux / macOS
  .venv\\Scripts\\activate              # Windows

  # 2. Instalar dependencias
  pip install -r requirements.txt

  # 3. Configurar variables de entorno
  cp .env.example .env

  # 4. Arrancar el servidor
  {cd_cmd}python src/app.py

  # 5. Ejecutar los tests
  pytest tests/ -v --cov=src

  # 6. Probar el health-check (en otra terminal)
  curl http://localhost:5000/health/

  # 7. Probar manejo de errores (demo)
  curl http://localhost:5000/api/v1/demo-errors/not-found
  curl http://localhost:5000/api/v1/demo-errors/validation
  curl http://localhost:5000/api/v1/demo-errors/unauthorized

{SEPARATOR}
""")


# ---------------------------------------------------------------------------
# Orquestador principal — entrada del script (Regla 1)
# ---------------------------------------------------------------------------


def run_setup(project_name: str, force: bool) -> int:
    """
    Orquesta todos los pasos de la automatización.

    Args:
        project_name: Nombre del proyecto o '.' para el directorio actual.
        force:        Si True, borra y recrea el directorio si ya existe.

    Returns:
        Código de salida: 0 = éxito, 1 = hay fallos.
    """
    print(f"\n{SEPARATOR}")
    print("  ORQUESTADOR — Generación de Estructura de Proyecto Backend")
    print(f"{SEPARATOR}\n")

    root: Path = _resolve_project_root(project_name)
    report: SetupReport = SetupReport(project_root=root)

    # Paso 1: Directorio raíz
    try:
        root_result: StepResult = _prepare_root_directory(root, force)
        report.add(root_result)
    except DirectoryCreationError as exc:
        report.add(StepResult(name="Directorio raíz", success=False, message=str(exc)))
        report.print_summary()
        return 1

    # Paso 2: Subdirectorios
    for result in _create_directories(root, PROJECT_STRUCTURE):
        report.add(result)

    # Paso 3: Archivos
    for result in _generate_files(root, PROJECT_STRUCTURE):
        report.add(result)

    # Informe final
    report.print_summary()

    if not report.has_failures:
        _print_next_steps(root)
        return 0

    return 1


def _parse_args() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="setup_project.py",
        description="Orquestador: Genera la estructura base de un proyecto backend Python.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=".",
        metavar="NOMBRE",
        help="Nombre del directorio del proyecto a crear (por defecto: directorio actual).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Elimina y recrea el directorio del proyecto si ya existe.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args: argparse.Namespace = _parse_args()
    exit_code: int = run_setup(project_name=args.name, force=args.force)
    sys.exit(exit_code)
