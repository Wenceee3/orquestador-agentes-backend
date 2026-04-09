"""
test_app.py — Suite de Tests Unitarios e Integración
Regla 1 - Modularización: Tests organizados por módulo/responsabilidad.
Regla 3 - Tipado Estricto: Todas las funciones de test tienen anotaciones de tipo.
Regla 5 - Manejo de Excepciones: Verificamos que los errores se propagan correctamente.
"""

from __future__ import annotations

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Ajuste del path para importaciones desde la raíz del proyecto
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask
from flask.testing import FlaskClient

from config.settings import AppConfig, ServerConfig, load_config
from src.app import create_app
from src.exceptions import (
    AppBaseException,
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    ErrorDetail,
    ExternalServiceException,
    RateLimitException,
    ResourceNotFoundException,
    ValidationException,
)

# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture(scope="module")
def test_config() -> AppConfig:
    """Configuración de prueba con valores fijos y predecibles."""
    server = ServerConfig(
        host="127.0.0.1",
        port=5001,
        debug=False,
        environment="testing",
    )
    return AppConfig(
        app_name="TestApp",
        version="0.0.1",
        server=server,
        allowed_origins=["http://localhost:3000"],
    )


@pytest.fixture(scope="module")
def app(test_config: AppConfig) -> Flask:
    """Instancia de Flask configurada para tests."""
    flask_app: Flask = create_app(test_config)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture(scope="module")
def client(app: Flask) -> FlaskClient:
    """Cliente HTTP de prueba."""
    return app.test_client()


# ===========================================================================
# Tests — Módulo: config/settings.py
# ===========================================================================


class TestAppConfig:
    """Verifica que la configuración carga correctamente y tiene tipado estricto."""

    def test_load_config_returns_app_config(self) -> None:
        cfg: AppConfig = load_config()
        assert isinstance(cfg, AppConfig)

    def test_server_config_has_required_fields(self) -> None:
        cfg: AppConfig = load_config()
        assert isinstance(cfg.server.host, str)
        assert isinstance(cfg.server.port, int)
        assert isinstance(cfg.server.debug, bool)
        assert isinstance(cfg.server.environment, str)

    def test_default_port_is_5000(self) -> None:
        os.environ.pop("APP_PORT", None)
        cfg: AppConfig = load_config()
        assert cfg.server.port == 5000

    def test_custom_port_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_PORT", "8080")
        cfg: AppConfig = load_config()
        assert cfg.server.port == 8080

    def test_debug_false_by_default(self) -> None:
        os.environ.pop("APP_DEBUG", None)
        cfg: AppConfig = load_config()
        assert cfg.server.debug is False

    def test_debug_true_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_DEBUG", "true")
        cfg: AppConfig = load_config()
        assert cfg.server.debug is True

    def test_app_config_is_frozen(self, test_config: AppConfig) -> None:
        """AppConfig debe ser inmutable (frozen dataclass)."""
        with pytest.raises((AttributeError, TypeError)):
            test_config.app_name = "MutatedName"  # type: ignore[misc]

    def test_server_config_is_frozen(self, test_config: AppConfig) -> None:
        with pytest.raises((AttributeError, TypeError)):
            test_config.server.port = 9999  # type: ignore[misc]


# ===========================================================================
# Tests — Módulo: src/exceptions.py
# ===========================================================================


class TestErrorDetail:
    """Verifica la dataclass ErrorDetail y su serialización."""

    def test_error_detail_creation(self) -> None:
        detail: ErrorDetail = ErrorDetail(
            code="TEST_CODE",
            message="Mensaje de prueba",
            http_status=400,
        )
        assert detail.code == "TEST_CODE"
        assert detail.message == "Mensaje de prueba"
        assert detail.http_status == 400
        assert detail.timestamp is not None

    def test_to_dict_structure(self) -> None:
        detail: ErrorDetail = ErrorDetail(
            code="TEST_CODE",
            message="Mensaje de prueba",
            http_status=422,
        )
        result: dict = detail.to_dict()
        assert "error" in result
        assert result["error"]["code"] == "TEST_CODE"
        assert result["error"]["message"] == "Mensaje de prueba"
        assert result["error"]["http_status"] == 422
        assert "timestamp" in result["error"]

    def test_to_dict_includes_context_when_provided(self) -> None:
        detail: ErrorDetail = ErrorDetail(
            code="CTX_CODE",
            message="Con contexto",
            http_status=400,
            context={"field": "email"},
        )
        result: dict = detail.to_dict()
        assert result["error"]["context"] == {"field": "email"}

    def test_to_dict_excludes_context_when_none(self) -> None:
        detail: ErrorDetail = ErrorDetail(
            code="NO_CTX",
            message="Sin contexto",
            http_status=400,
            context=None,
        )
        result: dict = detail.to_dict()
        assert "context" not in result["error"]

    def test_error_detail_is_frozen(self) -> None:
        detail: ErrorDetail = ErrorDetail(
            code="FROZEN",
            message="Inmutable",
            http_status=400,
        )
        with pytest.raises((AttributeError, TypeError)):
            detail.code = "CHANGED"  # type: ignore[misc]


class TestAppBaseException:
    """Verifica el comportamiento de la excepción raíz."""

    def test_raises_correctly(self) -> None:
        with pytest.raises(AppBaseException):
            raise AppBaseException()

    def test_default_values(self) -> None:
        exc: AppBaseException = AppBaseException()
        assert exc.detail.code == "APP_ERROR"
        assert exc.detail.http_status == 500

    def test_custom_message(self) -> None:
        exc: AppBaseException = AppBaseException(message="Error personalizado")
        assert str(exc) == "Error personalizado"
        assert exc.detail.message == "Error personalizado"

    def test_custom_code(self) -> None:
        exc: AppBaseException = AppBaseException(code="MY_CODE")
        assert exc.detail.code == "MY_CODE"

    def test_custom_http_status(self) -> None:
        exc: AppBaseException = AppBaseException(http_status=418)
        assert exc.detail.http_status == 418

    def test_context_is_stored(self) -> None:
        ctx: dict = {"field": "username", "value": "admin"}
        exc: AppBaseException = AppBaseException(context=ctx)
        assert exc.detail.context == ctx

    def test_to_response_returns_tuple(self) -> None:
        exc: AppBaseException = AppBaseException()
        body, status = exc.to_response()
        assert isinstance(body, dict)
        assert isinstance(status, int)
        assert status == 500

    def test_to_response_body_has_error_key(self) -> None:
        exc: AppBaseException = AppBaseException(message="Algo falló")
        body, _ = exc.to_response()
        assert "error" in body


class TestDomainExceptions:
    """Verifica cada excepción de dominio específica."""

    def test_resource_not_found_defaults(self) -> None:
        exc: ResourceNotFoundException = ResourceNotFoundException()
        assert exc.detail.http_status == 404
        assert exc.detail.code == "RESOURCE_NOT_FOUND"

    def test_validation_exception_defaults(self) -> None:
        exc: ValidationException = ValidationException()
        assert exc.detail.http_status == 422
        assert exc.detail.code == "VALIDATION_ERROR"

    def test_authentication_exception_defaults(self) -> None:
        exc: AuthenticationException = AuthenticationException()
        assert exc.detail.http_status == 401
        assert exc.detail.code == "AUTHENTICATION_FAILED"

    def test_authorization_exception_defaults(self) -> None:
        exc: AuthorizationException = AuthorizationException()
        assert exc.detail.http_status == 403
        assert exc.detail.code == "AUTHORIZATION_DENIED"

    def test_conflict_exception_defaults(self) -> None:
        exc: ConflictException = ConflictException()
        assert exc.detail.http_status == 409
        assert exc.detail.code == "RESOURCE_CONFLICT"

    def test_external_service_exception_defaults(self) -> None:
        exc: ExternalServiceException = ExternalServiceException()
        assert exc.detail.http_status == 502
        assert exc.detail.code == "EXTERNAL_SERVICE_ERROR"

    def test_rate_limit_exception_defaults(self) -> None:
        exc: RateLimitException = RateLimitException()
        assert exc.detail.http_status == 429
        assert exc.detail.code == "RATE_LIMIT_EXCEEDED"

    def test_domain_exceptions_inherit_base(self) -> None:
        """Todas las excepciones de dominio deben heredar de AppBaseException."""
        exceptions: list = [
            ResourceNotFoundException(),
            ValidationException(),
            AuthenticationException(),
            AuthorizationException(),
            ConflictException(),
            ExternalServiceException(),
            RateLimitException(),
        ]
        for exc in exceptions:
            assert isinstance(exc, AppBaseException), (
                f"{type(exc).__name__} no hereda de AppBaseException"
            )

    def test_override_message_on_domain_exception(self) -> None:
        exc: ResourceNotFoundException = ResourceNotFoundException(
            message="El usuario con ID 42 no existe.",
            context={"id": 42},
        )
        assert "42" in exc.detail.message
        assert exc.detail.context == {"id": 42}
        assert exc.detail.http_status == 404


# ===========================================================================
# Tests — Integración: Endpoints HTTP
# ===========================================================================


class TestHealthEndpoint:
    """Tests del endpoint /health/."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        response = client.get("/health/")
        assert response.status_code == 200

    def test_health_returns_json(self, client: FlaskClient) -> None:
        response = client.get("/health/")
        data: dict = response.get_json()
        assert data is not None
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_includes_service_name(self, client: FlaskClient) -> None:
        response = client.get("/health/")
        data: dict = response.get_json()
        assert "service" in data


class TestItemsEndpoint:
    """Tests del endpoint /api/v1/items."""

    def test_list_items_returns_200(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/items/")
        assert response.status_code == 200

    def test_list_items_returns_data_and_total(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/items/")
        data: dict = response.get_json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
        assert data["total"] == len(data["data"])

    def test_get_existing_item_returns_200(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/items/1")
        assert response.status_code == 200

    def test_get_existing_item_has_data_key(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/items/1")
        data: dict = response.get_json()
        assert "data" in data
        assert data["data"]["id"] == 1

    def test_get_nonexistent_item_returns_404(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/items/9999")
        assert response.status_code == 404

    def test_get_nonexistent_item_returns_error_json(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/items/9999")
        data: dict = response.get_json()
        assert "error" in data
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert data["error"]["http_status"] == 404

    def test_create_item_returns_201(self, client: FlaskClient) -> None:
        response = client.post(
            "/api/v1/items/",
            json={"name": "Ítem Gamma", "active": True},
        )
        assert response.status_code == 201

    def test_create_item_returns_created_data(self, client: FlaskClient) -> None:
        response = client.post(
            "/api/v1/items/",
            json={"name": "Ítem Delta"},
        )
        data: dict = response.get_json()
        assert "data" in data
        assert data["data"]["name"] == "Ítem Delta"

    def test_create_item_empty_body_returns_422(self, client: FlaskClient) -> None:
        response = client.post(
            "/api/v1/items/", data="not-json", content_type="text/plain"
        )
        assert response.status_code == 422

    def test_create_item_missing_name_returns_422(self, client: FlaskClient) -> None:
        response = client.post(
            "/api/v1/items/",
            json={"active": True},
        )
        assert response.status_code == 422

    def test_create_item_empty_name_returns_422(self, client: FlaskClient) -> None:
        response = client.post(
            "/api/v1/items/",
            json={"name": "   "},
        )
        assert response.status_code == 422

    def test_create_item_non_string_name_returns_422(self, client: FlaskClient) -> None:
        response = client.post(
            "/api/v1/items/",
            json={"name": 12345},
        )
        assert response.status_code == 422


class TestDemoErrorsEndpoint:
    """Tests de los endpoints de demostración de errores."""

    def test_demo_not_found_returns_404(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/demo-errors/not-found")
        assert response.status_code == 404
        data: dict = response.get_json()
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_demo_validation_returns_422(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/demo-errors/validation")
        assert response.status_code == 422
        data: dict = response.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "context" in data["error"]

    def test_demo_unauthorized_returns_401(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/demo-errors/unauthorized")
        assert response.status_code == 401
        data: dict = response.get_json()
        assert data["error"]["code"] == "AUTHENTICATION_FAILED"

    def test_demo_forbidden_returns_403(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/demo-errors/forbidden")
        assert response.status_code == 403
        data: dict = response.get_json()
        assert data["error"]["code"] == "AUTHORIZATION_DENIED"

    def test_demo_conflict_returns_409(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/demo-errors/conflict")
        assert response.status_code == 409
        data: dict = response.get_json()
        assert data["error"]["code"] == "RESOURCE_CONFLICT"

    def test_demo_external_error_returns_502(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/demo-errors/external-error")
        assert response.status_code == 502
        data: dict = response.get_json()
        assert data["error"]["code"] == "EXTERNAL_SERVICE_ERROR"
        assert "context" in data["error"]

    def test_demo_rate_limit_returns_429(self, client: FlaskClient) -> None:
        response = client.get("/api/v1/demo-errors/rate-limit")
        assert response.status_code == 429
        data: dict = response.get_json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"


class TestGlobalErrorHandlers:
    """Tests de los manejadores globales de errores HTTP."""

    def test_unknown_route_returns_404(self, client: FlaskClient) -> None:
        response = client.get("/ruta/que/no/existe")
        assert response.status_code == 404

    def test_unknown_route_returns_structured_json(self, client: FlaskClient) -> None:
        response = client.get("/ruta/inexistente")
        data: dict = response.get_json()
        assert "error" in data
        assert data["error"]["code"] == "ROUTE_NOT_FOUND"
        assert data["error"]["http_status"] == 404

    def test_method_not_allowed_returns_405(self, client: FlaskClient) -> None:
        # /health/ solo acepta GET, no DELETE
        response = client.delete("/health/")
        assert response.status_code == 405

    def test_method_not_allowed_returns_structured_json(
        self, client: FlaskClient
    ) -> None:
        response = client.delete("/health/")
        data: dict = response.get_json()
        assert "error" in data
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"
        assert data["error"]["http_status"] == 405


# ===========================================================================
# Tests — Estructura del proyecto
# ===========================================================================


class TestProjectStructure:
    """Verifica que la estructura de carpetas y archivos obligatorios existe."""

    BASE_DIR: str = os.path.join(os.path.dirname(__file__), "..")

    def _path(self, *parts: str) -> str:
        return os.path.join(self.BASE_DIR, *parts)

    def test_src_directory_exists(self) -> None:
        assert os.path.isdir(self._path("src")), "Falta el directorio /src"

    def test_tests_directory_exists(self) -> None:
        assert os.path.isdir(self._path("tests")), "Falta el directorio /tests"

    def test_config_directory_exists(self) -> None:
        assert os.path.isdir(self._path("config")), "Falta el directorio /config"

    def test_app_py_exists(self) -> None:
        assert os.path.isfile(self._path("src", "app.py")), "Falta src/app.py"

    def test_exceptions_py_exists(self) -> None:
        assert os.path.isfile(self._path("src", "exceptions.py")), (
            "Falta src/exceptions.py"
        )

    def test_settings_py_exists(self) -> None:
        assert os.path.isfile(self._path("config", "settings.py")), (
            "Falta config/settings.py"
        )

    def test_requirements_txt_exists(self) -> None:
        assert os.path.isfile(self._path("requirements.txt")), "Falta requirements.txt"
