-- Opcional: ejecutar en una base de datos PostgreSQL con PostGIS disponible.
-- La aplicación almacena latitud/longitud para mantener compatibilidad con SQLite y PostgreSQL.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE OR REPLACE VIEW reportes_geograficos AS
SELECT pk, description, locality, category, date,
       ST_SetSRID(ST_MakePoint(lng, lat), 4326) AS geom
FROM reports;
-- Ejemplo: SELECT locality, count(*) FROM reportes_geograficos GROUP BY locality;
