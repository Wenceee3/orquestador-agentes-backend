"""
Módulo de configuración de la aplicación.
Regla 3 - Tipado Estricto: Todas las propiedades tienen tipos explícitos definidos.
Regla 4 - Acoplamiento Débil: La configuración está aislada del resto del sistema.
"""

import os
from dataclasses import dataclass, field
from typing import Final

# ---------------------------------------------------------------------------
# Constantes globales inmutables
# ---------------------------------------------------------------------------
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
    """
    Configuración raíz de la aplicación.
    Regla 1 - Modularización: Cada bloque de configuración está encapsulado
    en su propio dataclass.
    """

    app_name: str
    version: str
    server: ServerConfig
    allowed_origins: list[str] = field(default_factory=list)


def load_config() -> AppConfig:
    """
    Carga la configuración desde variables de entorno con valores por defecto.

    Returns:
        AppConfig: Objeto de configuración completamente tipado.
    """
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
        allowed_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(
            ","
        ),
    )


# Instancia singleton exportable — se evalúa una sola vez al importar el módulo.
config: AppConfig = load_config()
