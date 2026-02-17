-- Tabla para registrar PDFs generados con consecutivo y verificación
-- Ejecutar este script en la base de datos de producción

CREATE TABLE IF NOT EXISTS Cobranza_pdf_evaluaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consecutivo VARCHAR(20) NOT NULL UNIQUE COMMENT 'Formato: YYYY-NNNNN (ej: 2026-00001)',
    cedula VARCHAR(20) NOT NULL,
    nombre_cliente VARCHAR(200) NOT NULL,
    fecha_generacion DATETIME NOT NULL,
    decision VARCHAR(20) NOT NULL COMMENT 'APROBADO o RECHAZADO',
    monto_solicitado DECIMAL(15,2) NOT NULL,
    monto_aprobado DECIMAL(15,2) NOT NULL,
    probabilidad DECIMAL(5,2) NOT NULL COMMENT 'Probabilidad de buen pagador (%)',
    nivel_riesgo VARCHAR(20) COMMENT 'BAJO, MEDIO, ALTO, CRÍTICO',
    concepto_oficina TEXT COMMENT 'Concepto del analista/director operativo sobre el crédito',
    hash_pdf VARCHAR(64) NOT NULL COMMENT 'SHA256 hash del contenido del PDF para verificación',
    usuario_generador VARCHAR(100) DEFAULT NULL COMMENT 'Usuario que generó el PDF (futuro)',

    INDEX idx_cedula (cedula),
    INDEX idx_fecha_generacion (fecha_generacion),
    INDEX idx_consecutivo (consecutivo),
    INDEX idx_hash_pdf (hash_pdf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Registro de PDFs de evaluación con consecutivo y hash para verificación';

-- Verificar que la tabla se creó correctamente
SHOW CREATE TABLE Cobranza_pdf_evaluaciones;
