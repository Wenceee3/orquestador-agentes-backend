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
