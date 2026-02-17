# Sistema de Consecutivos y Verificación de PDFs

## 📋 Objetivo

Implementar un sistema de **consecutivos únicos** y **verificación de autenticidad** para los PDFs de evaluación de crédito.

## 🔑 Características Implementadas

### 1. Consecutivo Único por Año
- Formato: **YYYY-NNNNN** (ej: 2026-00001, 2026-00002, etc.)
- Auto-incremental por año
- Se reinicia cada año en 00001

### 2. Hash SHA256 para Verificación
- Cada PDF genera un hash único de su contenido
- **Cualquier modificación al PDF cambiará el hash**
- Permite verificar autenticidad comparando hash original vs hash actual

### 3. Registro en Base de Datos
- Tabla: `Cobranza_pdf_evaluaciones`
- Almacena:
  - Consecutivo
  - Datos del cliente (cédula, nombre)
  - Fecha y hora de generación
  - Decisión (APROBADO/RECHAZADO)
  - Montos solicitado y aprobado
  - Probabilidad y nivel de riesgo
  - **Concepto de la Oficina** (analista/director operativo)
  - **Hash SHA256 del PDF**
  - Usuario que generó (futuro)

## 🚀 Pasos para Implementación

### Paso 1: Crear la tabla en la Base de Datos

**IMPORTANTE:** Ejecutar este script SQL en la base de datos de **PRODUCCIÓN** (GoDaddy):

```sql
-- Copiar y ejecutar el contenido del archivo:
-- scripts/create_pdf_registry.sql
```

O directamente:

```sql
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
```

### Paso 2: Verificar la Tabla

```sql
-- Verificar que la tabla se creó correctamente
SHOW CREATE TABLE Cobranza_pdf_evaluaciones;

-- Ver estructura de la tabla
DESCRIBE Cobranza_pdf_evaluaciones;

-- Verificar índices
SHOW INDEX FROM Cobranza_pdf_evaluaciones;
```

### Paso 3: Desplegar en Streamlit Cloud

Los cambios en `hello.py` ya están listos. Solo necesitas:

1. **Hacer commit y push:**
```bash
git add .
git commit -m "Implementar sistema de consecutivos y verificación de PDFs"
git push
```

2. **Streamlit Cloud** se re-desplegará automáticamente

## 🔍 Cómo Funciona la Verificación

### Al Generar un PDF:

1. Sistema obtiene el siguiente consecutivo de la BD
2. Genera el PDF con el consecutivo en el encabezado
3. Calcula el hash SHA256 del contenido del PDF
4. Guarda el registro en `Cobranza_pdf_evaluaciones` con:
   - Consecutivo
   - Datos del cliente y evaluación
   - **Hash del PDF**

### Al Verificar un PDF:

Para verificar si un PDF es auténtico (no ha sido alterado):

1. Lee el PDF recibido
2. Calcula su hash SHA256
3. Busca el consecutivo en la BD
4. Compara el hash guardado con el hash calculado
5. Si coinciden → **PDF AUTÉNTICO** ✅
6. Si NO coinciden → **PDF ALTERADO** ❌

## 📊 Consultas Útiles

### Ver todos los PDFs generados:
```sql
SELECT consecutivo, cedula, nombre_cliente, fecha_generacion, decision, monto_aprobado,
       LEFT(concepto_oficina, 50) as concepto_resumen
FROM Cobranza_pdf_evaluaciones
ORDER BY fecha_generacion DESC;
```

### Buscar PDF por consecutivo:
```sql
SELECT *
FROM Cobranza_pdf_evaluaciones
WHERE consecutivo = '2026-00001';
```

### Buscar PDFs de un cliente:
```sql
SELECT consecutivo, fecha_generacion, decision, monto_aprobado, monto_solicitado,
       concepto_oficina
FROM Cobranza_pdf_evaluaciones
WHERE cedula = '1234567890'
ORDER BY fecha_generacion DESC;
```

### Verificar hash de un PDF:
```sql
SELECT consecutivo, hash_pdf, fecha_generacion
FROM Cobranza_pdf_evaluaciones
WHERE consecutivo = '2026-00001';
```

### Estadísticas de PDFs generados:
```sql
SELECT
    DATE(fecha_generacion) as fecha,
    COUNT(*) as total_pdfs,
    SUM(CASE WHEN decision = 'APROBADO' THEN 1 ELSE 0 END) as aprobados,
    SUM(CASE WHEN decision = 'RECHAZADO' THEN 1 ELSE 0 END) as rechazados
FROM Cobranza_pdf_evaluaciones
GROUP BY DATE(fecha_generacion)
ORDER BY fecha DESC;
```

## 🛡️ Seguridad

### ¿Qué se guarda en la BD?

✅ **SÍ se guarda:**
- Consecutivo único
- Datos del cliente (cédula, nombre)
- Fecha/hora de generación
- Decisión y montos
- **Hash SHA256 del PDF**
- Nivel de riesgo y probabilidad

❌ **NO se guarda:**
- El PDF completo (solo el hash)
- Información confidencial adicional

### ¿Cómo previene fraude?

1. **Consecutivo único:** No se puede duplicar o inventar un número
2. **Hash SHA256:** Cualquier modificación al PDF (cambiar montos, fechas, decisión) generará un hash diferente
3. **Registro inmutable:** La BD guarda el hash original, permitiendo detectar alteraciones

### ¿Cómo verificar si un PDF es auténtico?

**Método Manual:**
1. Buscar el consecutivo en la BD
2. Calcular el hash del PDF recibido
3. Comparar con el hash guardado en la BD

**Método Automático (futuro):**
- Crear una funcionalidad en la app para subir un PDF y verificarlo automáticamente

## 📝 Notas Importantes

- Los consecutivos se reinician cada año (2026-00001, 2027-00001, etc.)
- El hash SHA256 es de 64 caracteres hexadecimales
- La tabla usa índices para búsquedas rápidas por: consecutivo, cédula, fecha, hash
- El campo `usuario_generador` está listo para futuras implementaciones de autenticación

## ✅ Checklist de Implementación

- [x] Crear tabla SQL `Cobranza_pdf_evaluaciones`
- [x] Implementar función `obtener_siguiente_consecutivo()`
- [x] Implementar función `calcular_hash_pdf()`
- [x] Implementar función `guardar_registro_pdf()`
- [x] Modificar `generar_pdf()` para incluir consecutivo
- [x] Integrar sistema en flujo de generación de PDFs
- [x] Mostrar consecutivo y hash al usuario
- [ ] **Ejecutar script SQL en base de datos de producción**
- [ ] **Hacer commit y push a GitHub**
- [ ] **Verificar funcionamiento en Streamlit Cloud**

## 🎯 Próximas Mejoras (Opcionales)

1. **Panel de Verificación:** Agregar funcionalidad para subir un PDF y verificar su autenticidad
2. **Autenticación:** Implementar sistema de usuarios para registrar quién generó cada PDF
3. **Auditoría:** Dashboard para ver estadísticas de PDFs generados
4. **Notificaciones:** Enviar email automático con el PDF y su consecutivo
5. **Firma Digital:** Implementar firma digital adicional al hash
