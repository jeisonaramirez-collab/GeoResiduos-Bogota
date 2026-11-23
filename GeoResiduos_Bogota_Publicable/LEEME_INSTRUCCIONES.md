# Acceso sin BAT para quien evalúa

**La opción recomendada es publicar el proyecto como página web.** Abre `INSTRUCCIONES_PUBLICAR_Y_PROBAR.md`. Para ver una muestra sin servidor, abre `DEMO_abrir_con_doble_clic.html` (solo demostración, sin datos compartidos).

---

# GeoResiduos Bogotá - Fase 4

**Proyecto:** Desarrollo de un sistema web georreferenciado para el reporte, análisis y visualización de puntos críticos de disposición inadecuada de residuos sólidos en Bogotá D. C.

**Curso:** Proyecto de grado 202016907 · Grupo 37 · Universidad Nacional Abierta y a Distancia (UNAD).

**Equipo:** Rodolfo Suárez Hernández, Álvaro Africano Mejía y Jeison Andrés Ramírez Vera.

## ¿Qué incluye?

- Pantallas HTML/CSS/JavaScript conservadas del diseño de la Fase 3: inicio, nuevo reporte, mapa, consultas y administración.
- Servidor **Flask** (`flask_backend.py`) para ejecutar la aplicación de acuerdo con la tecnología propuesta en el documento maestro.
- Motor alternativo **FastAPI** (`server.py`), utilizado para validar automáticamente los endpoints y la persistencia. Ambos comparten tablas, credenciales y formato de API.
- Base de datos **SQLite** por defecto (archivo persistente y sin instalación adicional). Se puede configurar **PostgreSQL** y habilitar **PostGIS** para la fase de integración.
- Carga de fotografías, validación de campos y coordenadas de referencia, lista de reportes, filtros, descarga CSV, mapa, control de acceso administrativo, actualización de estado y registro de cambios.
- Un botón administrativo para cargar ocho reportes **ficticios y claramente identificados**. Se cargan solo si se solicita.
- Pruebas automatizadas, guía de evidencias y capturas de interfaz de referencia.

> **Importante:** Este es un sistema académico. No equivale a un canal oficial de atención ciudadana de la UAESP y no confirma automáticamente la existencia de un punto crítico. La cartografía depende de la disponibilidad del proveedor externo; si falla, la aplicación muestra un plano ilustrativo de respaldo, que no debe usarse para determinar coordenadas precisas.

## Instalación en Windows (camino más sencillo)

1. Instala **Python 3.11 o posterior** desde python.org y habilita la opción «Add Python to PATH».
2. Extrae todo el archivo ZIP en una carpeta, por ejemplo `C:\GeoResiduos_Bogota_Fase4`.
3. Con conexión a Internet, haz doble clic en `iniciar_windows.bat`.
4. Durante la primera ejecución se instalarán las dependencias. El asistente te pedirá crear y confirmar una **contraseña de administrador de al menos 10 caracteres**. Escribe tu propia contraseña. No se incluye ninguna contraseña predeterminada.
5. Cuando el asistente pregunte si deseas cargar puntos ficticios, responde `s` para contar con registros de prueba.
6. Se abrirá la página de la aplicación en **http://127.0.0.1:8000**. Si el navegador se abre antes de arrancar el servidor, actualiza la página.
7. Para ingresar al panel administrativo, abre **Administración** y utiliza la contraseña que configuraste.

Al cerrar la consola, se apaga el servidor. El archivo de base de datos permanece en `data/georesiduos.db` para la próxima ejecución.

**Importante:** No debes abrir `static/index.html` directamente desde el explorador de archivos, pues el formulario necesita conectarse al servidor para guardar y consultar reportes.

## Ejecución manual

En la carpeta del proyecto:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux o macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py init
python -m flask --app flask_backend run --host 127.0.0.1 --port 8000
```

Después visita `http://127.0.0.1:8000`.

La primera configuración del administrador puede realizarse en otra terminal sin volver a ejecutar el servidor.

## ¿Cómo probar el flujo completo?

1. En **Nuevo reporte**, escribe una descripción de al menos 12 caracteres, selecciona el tipo de residuo, fecha y localidad, y elige coordenadas en Bogotá.
2. Pulsa **Guardar reporte**. Comprueba que el nuevo registro aparezca en **Consultar reportes**.
3. Cierra la pestaña, abre otra en la misma dirección y verifica que el reporte sigue disponible. Esto demuestra persistencia en servidor, no solo en localStorage.
4. Abre **Mapa de puntos** y comprueba que el registro aparece en los marcadores, cuando el proveedor de mapas está accesible. Si no, utiliza el plano ilustrativo de respaldo y valida las coordenadas manualmente.
5. Entra a **Administración**, inicia sesión y cambia el estado del reporte a **En revisión**. Actualiza la página y confirma que el estado se conserva.
6. Exporta el listado mediante **Exportar CSV** y comprueba las columnas y valores.
7. Si lo necesitas, comprueba el estado del servidor en `http://127.0.0.1:8000/api/health`.

## PostgreSQL/PostGIS (opcional)

SQLite se utiliza únicamente para facilitar la puesta en marcha local. Si cuentas con un servidor PostgreSQL, instala las dependencias de `requirements-postgres.txt` y define `DATABASE_URL` como una URL válida de SQLAlchemy, por ejemplo:

```text
postgresql+psycopg://usuario:clave@localhost:5432/georesiduos
```

En Windows CMD:

```bat
set DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/georesiduos
python manage.py init-db
```

Las coordenadas se guardan como latitud y longitud. En una base PostgreSQL con la extensión PostGIS habilitada, ejecuta `scripts/activar_postgis.sql` para crear una vista espacial mediante `ST_MakePoint` y SRID 4326. La aplicación sigue funcionando sin esta vista, pero las consultas espaciales avanzadas necesitarían implementación adicional.

No publiques contraseñas de PostgreSQL ni claves de sesión en GitHub.

## Pruebas automatizadas

```bash
pip install pytest httpx
pytest -q tests/test_app.py
```

Las pruebas de integración incluidas ejercitan la API equivalente FastAPI, los formularios de entrada, SQLite, la autenticación, el cambio de estado, el historial y la carga opcional de ejemplos. El adaptador Flask utiliza la misma base y lógica de validación, pero **debe probarse durante la instalación definitiva**; las pruebas de esta entrega no constituyen por sí mismas validación TRL 5.

## Archivos principales

| Archivo | Función |
| --- | --- |
| `static/index.html` | Interfaces y estilos HTML/CSS originales, adaptados a servidor |
| `static/app.js` | Interacción, consultas HTTP y representación cartográfica |
| `flask_backend.py` | Servidor Flask, opción principal para el curso |
| `server.py` | Servidor API alternativo FastAPI utilizado en las pruebas automáticas |
| `storage.py` | Modelos de datos e integración SQLite/PostgreSQL |
| `security.py` | Contraseña de administrador mediante scrypt |
| `manage.py` | Configuración de administrador, base de datos y datos ficticios |
| `scripts/activar_postgis.sql` | Vista espacial opcional en PostgreSQL |
| `GUIA_EVIDENCIAS_FASE4.md` | Actividades de prueba y evidencias que deben registrarse |
| `captura_*.png` | Capturas de presentación de interfaz basadas en datos simulados para revisión visual |

## Subir el código a GitHub

Con Git instalado, abre una consola en la carpeta extraída y ejecuta:

```bash
git init
git add .
git commit -m "GeoResiduos Fase 4 - prototipo funcional"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/TU-REPOSITORIO.git
git push -u origin main
```

Antes de `git remote add origin`, crea un repositorio **vacío** en tu cuenta de GitHub y cambia la URL de ejemplo por la dirección real. El archivo `.gitignore` excluye las bases de datos, claves y fotografías que pueden contener información sensible.

No basta con mostrar que el código abre: la guía de la Fase 4 solicita además **pruebas en un entorno relevante para sustentar TRL 5**, video de máximo 10 minutos con cámara de los participantes, actualización del documento maestro y enlaces del repositorio y del video.
