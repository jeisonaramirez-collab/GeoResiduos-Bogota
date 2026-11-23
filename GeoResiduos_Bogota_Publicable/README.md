# GeoResiduos Bogotá – Fase 4

**Proyecto académico:** Sistema web para el reporte y análisis de puntos críticos de disposición inadecuada de residuos sólidos en Bogotá D. C.  
**Universidad:** Universidad Nacional Abierta y a Distancia (UNAD)  
**Grupo:** 37  
**Integrantes:** Rodolfo Suárez Hernández, Álvaro Africano Mejía y Jeison Andrés Ramírez Vera.

## Descripción

GeoResiduos Bogotá es un prototipo web académico que permite registrar, consultar y gestionar reportes de puntos críticos de disposición inadecuada de residuos sólidos, incluyendo datos descriptivos y ubicación geográfica. Incorpora visualización cartográfica, filtros, administración de estados y exportación CSV.

> Este prototipo no es un canal oficial de atención ciudadana y no está integrado a sistemas institucionales de Bogotá.

## Funcionalidades principales

- Registro de reportes con descripción, categoría, localidad, fecha y coordenadas.
- Adjuntar fotografías a reportes.
- Consulta de reportes y detalle.
- Filtros y visualización geográfica en mapa.
- Panel administrativo y cambio de estado.
- Registro de auditoría de cambios.
- Exportación de información en CSV.
- Carga opcional de registros ficticios para demostración.

## Tecnologías

- Frontend: HTML, CSS y JavaScript.
- Backend principal: Flask (`flask_backend.py`).
- API alternativa usada en pruebas: FastAPI (`server.py`).
- Persistencia: SQLAlchemy y SQLite por defecto.
- Opción de base de datos: PostgreSQL/PostGIS.
- Mapa: MapLibre GL JS y proveedor cartográfico configurado.
- Imágenes: Pillow.
- Pruebas: pytest.

## Instalación rápida en Windows

1. Instalar Python 3.11 o posterior y activar la opción de agregarlo al PATH.
2. Descargar o clonar este repositorio y descomprimirlo.
3. Ejecutar `iniciar_windows.bat`.
4. Seguir las instrucciones de la consola para instalar dependencias y crear una contraseña administrativa propia.
5. Abrir la dirección local indicada por el instalador (por defecto `http://127.0.0.1:8000`).

Para instrucciones completas, consultar `LEEME_INSTRUCCIONES.md` e `INSTRUCCIONES_PUBLICAR_Y_PROBAR.md`.


## Ejecutar pruebas automatizadas

En un entorno virtual e instaladas las dependencias:


```bash
python -m pytest -q tests/test_app.py
```

Las pruebas incluidas son verificaciones automatizadas de endpoints y del servicio de frontend. No reemplazan las pruebas manuales de mapa, experiencia de usuario o validación en un entorno real.

## Estructura

```text
GeoResiduos_Bogota_Publicable/
├── static/                     # Interfaz web y JavaScript
├── tests/                       # Pruebas automatizadas
├── scripts/                      # SQL auxiliar
├── data/                          # Datos locales (excluidos del repositorio)
├── uploads/                        # Imágenes cargadas (excluidas del repositorio)
├── flask_backend.py               # Backend Flask
├── server.py                      # API FastAPI
├── storage.py                     # Modelos y persistencia
├── security.py                    # Seguridad y validaciones
├── manage.py                      # Utilidades de administración
├── requirements.txt                # Dependencias
├── iniciar_windows.bat              # Inicio local en Windows
└── INSTRUCCIONES_PUBLICAR_Y_PROBAR.md
```

## Uso académico y datos

Utilizar datos ficticios para las demostraciones. No subir contraseñas, archivos `.env`, bases de datos locales, fotografías personales ni información sensible. El archivo `.gitignore` excluye datos locales, bases de datos, entornos virtuales y archivos de configuración sensibles.

## Acceso del tutor

Para entregar el repositorio al tutor, compartir la URL de GitHub. Si el repositorio es público, el tutor puede visualizar y descargar el código sin permisos de escritura. Si es privado, agregar al tutor como colaborador con permiso **Read** (solo lectura), si la configuración de la cuenta/organización permite asignarlo.
