# Evidencias necesarias para Fase 4 - GeoResiduos Bogotá

Esta guía sirve para planificar y registrar las pruebas. **No sustituye resultados reales ni acredita por sí misma TRL 5**.

## Ejecución técnica

| Evidencia | Acción que debe realizar el equipo | Captura o soporte |
|---|---|---|
| E1 | Abrir la aplicación desde `http://127.0.0.1:8000` | Pantalla inicial con fecha y estadísticas |
| E2 | Crear un reporte con campos válidos y guardar | Formulario y confirmación del registro |
| E3 | Consultar el nuevo reporte y sus datos | Tabla o detalle del reporte |
| E4 | Reiniciar la aplicación y comprobar que el reporte persiste | Reporte visible luego del reinicio |
| E5 | Consultar el mapa y localizar el punto | Marcador del mapa y coordenadas asociadas |
| E6 | Iniciar sesión administrativa y cambiar el estado | Estado actualizado antes/después |
| E7 | Exportar CSV y revisar datos | Archivo exportado con registros |
| E8 | Ejecutar pruebas con `pytest -q tests/test_app.py` | Resultado de la consola |
| E9 | Abrir `http://127.0.0.1:8000/api/health` | Estado del servicio |
| E10 | Demostrar el sistema desde el entorno relevante seleccionado para evaluación | Informe de protocolo, participantes, condiciones y resultados |

## Registro de casos de prueba

| Caso | Entrada o tarea | Resultado esperado | Resultado observado | Estado | Evidencia |
|---|---|---|---|---|---|
| P01 | Registro completo | Guarda y asigna ID único | Pendiente | No ejecutado | Pendiente |
| P02 | Descripción de menos de 12 caracteres | Rechaza entrada | Pendiente | No ejecutado | Pendiente |
| P03 | Coordenadas fuera del rango | Rechaza el registro | Pendiente | No ejecutado | Pendiente |
| P04 | Consulta con filtro | Retorna coincidencias | Pendiente | No ejecutado | Pendiente |
| P05 | Reinicio y consulta | Conserva reporte | Pendiente | No ejecutado | Pendiente |
| P06 | Acceso administrativo sin sesión | Impide actualización | Pendiente | No ejecutado | Pendiente |
| P07 | Cambio autorizado de estado | Guarda e incorpora historial | Pendiente | No ejecutado | Pendiente |
| P08 | Visualización de punto | Ubicación consistente con coordenadas | Pendiente | No ejecutado | Pendiente |
| P09 | Exportación CSV | Archivo con datos correctos | Pendiente | No ejecutado | Pendiente |
| P10 | Carga de fotografía válida | Almacena imagen permitida | Pendiente | No ejecutado | Pendiente |

## Seguimiento Scrum

Registrar las iteraciones efectivamente realizadas, participantes, lista de pendientes, decisiones, dificultades y entregables. No atribuir actividades a estudiantes que no hayan intervenido.

## Validación del entorno relevante y TRL 5

Para documentar TRL 5, seleccionar y justificar un entorno relevante (por ejemplo, usuarios y dispositivos representativos, conexión y navegación ordinaria, conjunto de reportes de prueba, procedimientos reproducibles), realizar las pruebas previstas, documentar sus resultados y analizar limitaciones. Las pruebas unitarias o las capturas de pantalla de una interfaz, por sí solas, **no demuestran TRL 5**.

## Enlaces que deben anexarse al documento maestro

- Repositorio GitHub: [pegar URL real].
- Video de demostración, máximo 10 minutos: [pegar URL real].
- Registro de resultados de pruebas y participantes: [insertar evidencia real].

## Guion de video (propuesta de distribución)

- Rodolfo: descripción del problema, objetivo y arquitectura; introducción del prototipo (aprox. 2 min).
- Álvaro: demostración de registro, almacenamiento, consulta y mapa (aprox. 3 min).
- Jeison: autenticación administrativa, cambios de estado, pruebas, repositorio y limitaciones (aprox. 3 min).
- Cierre del equipo: principales resultados obtenidos, entorno de validación y conclusiones (aprox. 1 min).

La distribución es sugerida. Todos los participantes deben mantener su cámara encendida durante toda la grabación, como lo pide la guía.
