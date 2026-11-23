# GeoResiduos Bogotá: publicación y pruebas sin ejecutar archivos BAT

**Objetivo:** entregar al tutor una URL que se abre como cualquier página web (en PC o celular). Quien visita el enlace NO necesita instalar Python, descomprimir archivos ni iniciar un servidor.

## Dos maneras de mostrar la aplicación

**A. Demostración inmediata sin instalación**

Abre `DEMO_abrir_con_doble_clic.html` con Chrome o Edge. Puedes compartir **ese archivo** para que otra persona lo abra por doble clic. Es la interfaz de la Fase 3 con datos locales de demostración; **no equivale al prototipo con servidor**, y sus registros no se comparten entre personas.

**B. Página web funcional para la Fase 4 (recomendada)**

Publica este proyecto en Render. El tutor solo recibe la dirección `https://...onrender.com` y puede realizar registros y consultas que quedan guardados en PostgreSQL.

## Paso 1. Subir la carpeta al repositorio de GitHub

1. Crea en GitHub un repositorio nuevo, por ejemplo `georesiduos-bogota-fase4`.
2. Descomprime el ZIP. **Debes subir los archivos contenidos en `GeoResiduos_Bogota_Publicable` a la raíz del repositorio**, de modo que `render.yaml`, `flask_backend.py`, `storage.py`, `requirements.txt` y la carpeta `static` se vean directamente al abrir el repositorio.
3. Puedes usar GitHub Desktop: menú **File > Add local repository** o **Create a New Repository** sobre la carpeta, luego **Publish repository**. O usar Git desde terminal:

   ```bash
   git init
   git add .
   git commit -m "GeoResiduos Bogotá - publicación Fase 4"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/georesiduos-bogota-fase4.git
   git push -u origin main
   ```

   Cambia la dirección de ejemplo por la de tu repositorio real. Nunca subas contraseñas, `.env`, archivos de base de datos ni fotografías de personas sin autorización.

## Paso 2. Crear la web en Render

1. Accede a https://dashboard.render.com/ e inicia sesión.
2. Conecta tu cuenta de GitHub a Render si se solicita.
3. Selecciona **New > Blueprint**.
4. Escoge el repositorio `georesiduos-bogota-fase4` y su archivo `render.yaml`.
5. Render propondrá **un Web Service** y **una base PostgreSQL**. Revisa que ambos figuren como gratuitos antes de aceptar.
6. Cuando pida `ADMIN_PASSWORD`, ingresa **una contraseña propia de al menos 10 caracteres**, que solo el equipo y el tutor autorizado conocerán si necesitan probar administración.
7. Render generará `SESSION_SECRET` automáticamente y vinculará `DATABASE_URL` a PostgreSQL. No tienes que escribir estas claves.
8. Selecciona **Deploy / Apply Blueprint**, y desde el panel abre el servicio cuando su estado indique *Live*.
9. Copia la URL real `https://[nombre-asignado].onrender.com`. Es el enlace que compartirás con la persona que evaluará la aplicación.

**Importante:** no inventes la URL: Render la asigna después de la publicación. Si el servicio gratuito no recibe visitas durante unos 15 minutos, la siguiente apertura puede tardar alrededor de un minuto. La base gratuita de Render **vence 30 días después de crearla**, por lo que es apropiada para una demostración corta, no para almacenamiento indefinido. Verifica disponibilidad del plan al crearla.

## Paso 3. Probar la web publicada

Para empezar ya aparecerán ocho reportes **ficticios, etiquetados como demostración**. El usuario visitante puede:

1. Abrir la URL en un navegador de computador o teléfono y verificar **Inicio**.
2. Entrar en **Nuevo reporte**, registrar una descripción de al menos 12 caracteres, elegir categoría/localidad, establecer una fecha válida y seleccionar un punto dentro de Bogotá. Puede adjuntar una fotografía de prueba de hasta 1 MB.
3. Pulsar **Guardar reporte** y verificar que aparece en **Consultar reportes**.
4. Entrar al **Mapa** y buscar el marcador. La cartografía usa un proveedor externo y puede mostrar un plano de respaldo si la conexión falla.
5. Actualizar la página (F5) y abrir la misma URL en otro navegador: el reporte debe continuar disponible porque la información está guardada en PostgreSQL.
6. En **Administración**, usar la clave configurada en Render para cambiar el estado de un registro de *Pendiente* a *En revisión*. Volver a cargar y verificar que el cambio se mantiene.
7. Exportar la consulta a un archivo CSV y contrastar los datos.

**Prueba obligatoria para sustentar TRL 5:** documenta navegador, fecha, equipo, escenarios de prueba, resultados obtenidos y capturas. El despliegue por sí solo **no demuestra** que se haya alcanzado TRL 5. La universidad también solicita el documento maestro, repositorio GitHub, video con cámaras encendidas de máximo 10 minutos y evidencias de validación.

## Alternativa cuando necesitas que la base no caduque en 30 días: Neon

1. Crea una base PostgreSQL en https://neon.com/ y copia su **Connection string** desde **Connect** (mantén `sslmode=require`). No la publiques en GitHub.
2. En la carpeta del proyecto cambia el nombre `render.yaml` por `render_con_base_temporal.yaml` y cambia `render_neon.yaml` por `render.yaml`, antes de subir los archivos al repositorio.
3. Crea en Render el Blueprint. Cuando pida `DATABASE_URL`, pega la cadena completa de Neon; cuando pida `ADMIN_PASSWORD`, escribe una contraseña propia.
4. El resto de los pasos de publicación y uso son los mismos. Este proyecto interpreta tanto `postgres://` como `postgresql://` con el controlador psycopg.

Los planes gratuitos de hosting y almacenamiento tienen límites y pueden cambiar. Para una demostración académica conserva siempre una copia del código y no dependas de que el servidor gratuito esté activo permanentemente.

## Cómo entregar al tutor

- **Enlace 1:** URL de la web publicada en Render.
- **Enlace 2:** repositorio de GitHub con permiso de lectura.
- **Enlace 3:** video de demostración (máximo 10 minutos) con participación visible de los integrantes.

Los enlaces reales deben insertarse en el documento maestro, no enlaces de ejemplo.

## Privacidad

Este proyecto es un prototipo académico. Los reportes ingresados por visitantes **no han sido verificados por la UAESP**. No publiques datos personales, rostros, placas ni domicilios particulares. No compartas públicamente la contraseña administrativa. Para el video y las pruebas usa datos inventados o información autorizada.
