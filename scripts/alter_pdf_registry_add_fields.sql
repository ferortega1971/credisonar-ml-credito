-- Script para agregar campos adicionales a la tabla Cobranza_pdf_evaluaciones
-- Ejecutar este script en la base de datos de producción (GoDaddy)

-- Agregar campos de información financiera al momento de la evaluación
ALTER TABLE Cobranza_pdf_evaluaciones
ADD COLUMN score_datacredito INT COMMENT 'Score de Datacrédito reportado en la evaluación' AFTER nivel_riesgo,
ADD COLUMN ingresos_reportados DECIMAL(15,2) COMMENT 'Ingresos mensuales reportados en la evaluación' AFTER score_datacredito,
ADD COLUMN egresos_reportados DECIMAL(15,2) COMMENT 'Egresos totales reportados en la evaluación' AFTER ingresos_reportados;

-- Verificar que los campos se agregaron correctamente
DESCRIBE Cobranza_pdf_evaluaciones;
