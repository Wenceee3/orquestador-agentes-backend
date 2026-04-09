# Orquestador de Agentes - Generador de Backend Inmutable

## Fase 1: Configuración del Agente
El agente ha sido instruido a través del archivo `.zed/.custom_rules`. Se han definido las siguientes reglas:

1. **Rol:** Ingeniero Senior y Orquestador de Sistemas.
2. **Normativa:** Estándares Clean Code y Seguridad OWASP.
3. **Vocabulario Técnico Obligatorio:**
   - **Modularización:** División del código en componentes reutilizables.
   - **Tipado Estricto:** Definición explícita de tipos para evitar errores en tiempo de ejecución.
   - **Acoplamiento Débil:** Independencia entre la configuración y la lógica de negocio.
   - **Escalabilidad:** Diseño preparado para el crecimiento.
   - **Manejo de Excepciones:** Respuestas JSON estructuradas ante cualquier fallo.

## Fase 2: Automatización
**Problema:** La configuración inicial de proyectos backend es lenta, repetitiva y proponer a inconsistencias estructurales.

**Solución:** Un script de automatización (`setup_project.py`) que:
1. Genera una arquitectura de carpetas profesional (`/src`, `/config`, `/tests`).
2. Implementa un servidor de salud inmutable.
3. Configura automáticamente el manejo de errores centralizado siguiendo las reglas del agente.

## Instrucciones de Ejecución

### 1. Requisitos previos
- Python 3.10+
- Gestor de paquetes `pip`

Si el sistema no dispone de Python o Pip, instale las dependencias base:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# 1. Navegar a la carpeta del proyecto
cd OrquestadorAgentes

# 2. Crear un nuevo entorno virtual
python3 -m venv .venv

# 3. Activar el entorno
source .venv/bin/activate

# 4. Instalar dependencias del proyecto
pip install -r requirements.txt

# 5 Iniciar el servidor
python3 src/app.py

# Para probar la Automatización
# Generar un nuevo microservicio independiente
python3 setup_project.py --name mi_nuevo_backend

# ── PROBAR ENDPOINTS (en otra terminal) ──────────────
curl http://localhost:5000/health/
curl http://localhost:5000/api/v1/items/
curl http://localhost:5000/api/v1/items/9999        # → 404 estructurado
curl -X POST http://localhost:5000/api/v1/items/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Proyecto Omega"}'                # → 201
curl http://localhost:5000/api/v1/demo-errors/unauthorized  # → 401
