-- Sombra: una sola vez sobre la D1 que ya existe y ANTES del deploy (schema.sql ya lo trae para bases nuevas).
-- Cuántos usos del día jugaron con la franja Sombra encendida (la métrica «la dejan encendida» del plan).
ALTER TABLE metricas ADD COLUMN sombra INTEGER DEFAULT 0;
