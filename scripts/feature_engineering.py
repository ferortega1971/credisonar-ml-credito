"""
Feature Engineering - Creación de características para el modelo ML
Combina datos de múltiples tablas y crea variables derivadas
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
from pathlib import Path

# Configuración
SQLITE_DB = r"c:\Desarrollos\projectos2026\proyecto1ML\data\credisonar.db"
OUTPUT_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\data\dataset_ml.csv"

def conectar_sqlite():
    """Conecta a la BD SQLite local"""
    return sqlite3.connect(SQLITE_DB)

def calcular_edad(fecha_nacimiento):
    """Calcula edad a partir de fecha de nacimiento"""
    try:
        nacimiento = pd.to_datetime(fecha_nacimiento)
        hoy = pd.Timestamp.now()
        edad = (hoy - nacimiento).days // 365
        return edad
    except:
        return None

def extraer_features_clientes():
    """Extrae features de la tabla de clientes"""
    print("\n>> Extrayendo features de clientes...")

    conn = conectar_sqlite()
    df = pd.read_sql("SELECT * FROM Cobranza_clientes", conn)
    conn.close()

    # Calcular edad
    df['edad'] = df['fecha_nacimiento'].apply(calcular_edad)

    # Codificar sexo (M=1, F=0)
    df['sexo_num'] = df['sexo'].map({'M': 1, 'F': 0})

    # Codificar estado civil (S=0, C=1, V=2, D=3)
    df['estado_civil_num'] = df['estado_civil'].map({'S': 0, 'C': 1, 'V': 2, 'D': 3})

    # Seleccionar columnas relevantes
    features = df[['cedula', 'edad', 'sexo_num', 'estado_civil_num']].copy()
    features.columns = ['cedula', 'edad', 'sexo', 'estado_civil']

    print(f"  [OK] {len(features)} clientes procesados")
    return features

def extraer_features_asesorias():
    """Extrae features de la tabla de asesorías (última solicitud)"""
    print("\n>> Extrayendo features de asesorias...")

    conn = conectar_sqlite()
    # Obtener la última asesoría por cliente
    query = """
    SELECT
        cedula_id,
        valor as monto_solicitado,
        plazo,
        score_datacredito,
        nivel_estudio_id,
        profesion_id,
        sector_id,
        fecha_asesoria
    FROM Cobranza_asesorias
    WHERE id IN (
        SELECT MAX(id)
        FROM Cobranza_asesorias
        GROUP BY cedula_id
    )
    """
    df = pd.read_sql(query, conn)
    conn.close()

    df.columns = ['cedula', 'monto_solicitado', 'plazo', 'score_datacredito',
                  'nivel_estudio', 'profesion', 'sector', 'fecha_ultima_asesoria']

    print(f"  [OK] {len(df)} asesorias procesadas")
    return df

def extraer_features_historial_cartera():
    """Extrae features del historial de cartera del cliente"""
    print("\n>> Extrayendo features de historial de cartera...")

    conn = conectar_sqlite()
    query = """
    SELECT
        cedula_id,
        COUNT(*) as num_prestamos_historicos,
        SUM(CASE WHEN estado = 'C' THEN 1 ELSE 0 END) as prestamos_cancelados,
        SUM(CASE WHEN estado = 'A' THEN 1 ELSE 0 END) as prestamos_activos,
        AVG(valor_desembolsado) as monto_promedio_historico,
        MAX(valor_desembolsado) as monto_maximo_historico,
        AVG(dias_mora) as dias_mora_promedio,
        MAX(dias_mora) as dias_mora_maximo,
        SUM(CASE WHEN calificacion = 'A' THEN 1 ELSE 0 END) as prestamos_calificacion_A,
        SUM(CASE WHEN calificacion = 'E' THEN 1 ELSE 0 END) as prestamos_calificacion_E,
        SUM(CASE WHEN restructurado = 'S' THEN 1 ELSE 0 END) as prestamos_restructurados,
        SUM(CASE WHEN en_juridica = 'S' THEN 1 ELSE 0 END) as prestamos_en_juridica,
        MIN(fecha_desembolso) as fecha_primer_prestamo,
        MAX(fecha_desembolso) as fecha_ultimo_prestamo
    FROM Cobranza_cartera
    GROUP BY cedula_id
    """
    df = pd.read_sql(query, conn)
    conn.close()

    df.columns = ['cedula', 'num_prestamos_historicos', 'prestamos_cancelados',
                  'prestamos_activos', 'monto_promedio_historico', 'monto_maximo_historico',
                  'dias_mora_promedio', 'dias_mora_maximo', 'prestamos_calificacion_A',
                  'prestamos_calificacion_E', 'prestamos_restructurados',
                  'prestamos_en_juridica', 'fecha_primer_prestamo', 'fecha_ultimo_prestamo']

    # Calcular antigüedad como cliente (en meses)
    df['fecha_primer_prestamo'] = pd.to_datetime(df['fecha_primer_prestamo'])
    hoy = pd.Timestamp.now()
    df['antiguedad_cliente_meses'] = ((hoy - df['fecha_primer_prestamo']).dt.days / 30).astype(int)

    # Ratio de préstamos buenos
    df['ratio_prestamos_buenos'] = df['prestamos_calificacion_A'] / df['num_prestamos_historicos']

    # Ratio de cancelación
    df['ratio_cancelacion'] = df['prestamos_cancelados'] / df['num_prestamos_historicos']

    # Eliminar fechas (ya usadas para cálculos)
    df = df.drop(['fecha_primer_prestamo', 'fecha_ultimo_prestamo'], axis=1)

    print(f"  [OK] {len(df)} historiales procesados")
    return df

def extraer_features_comportamiento_pago():
    """Extrae features del comportamiento de pago"""
    print("\n>> Extrayendo features de comportamiento de pago...")

    conn = conectar_sqlite()

    # Obtener información de pagos por préstamo
    query = """
    SELECT
        car.cedula_id,
        car.pagare,
        COUNT(p.id) as num_pagos,
        SUM(p.valor_pagado) as total_pagado,
        AVG(p.valor_pagado) as promedio_valor_pago,
        MIN(p.fecha_pago) as fecha_primer_pago,
        MAX(p.fecha_pago) as fecha_ultimo_pago
    FROM Cobranza_cartera car
    LEFT JOIN Cobranza_pagos3 p ON car.pagare = p.pagare_id
    GROUP BY car.cedula_id, car.pagare
    """
    df_pagos = pd.read_sql(query, conn)

    # Agrupar por cliente
    df = df_pagos.groupby('cedula_id').agg({
        'num_pagos': 'sum',
        'total_pagado': 'sum',
        'promedio_valor_pago': 'mean'
    }).reset_index()

    df.columns = ['cedula', 'total_pagos_realizados', 'monto_total_pagado', 'promedio_valor_pago']

    conn.close()

    print(f"  [OK] {len(df)} comportamientos procesados")
    return df

def crear_variable_objetivo():
    """Crea la variable objetivo (target) basada en el comportamiento"""
    print("\n>> Creando variable objetivo...")

    conn = conectar_sqlite()

    # Criterio: Buenos pagadores = Todos los préstamos con calificación A o B
    # y días de mora máximo <= 30
    query = """
    SELECT
        cedula_id as cedula,
        CASE
            WHEN MAX(dias_mora) <= 30 AND
                 SUM(CASE WHEN calificacion IN ('A', 'B') THEN 1 ELSE 0 END) = COUNT(*)
            THEN 1
            ELSE 0
        END as es_buen_pagador
    FROM Cobranza_cartera
    GROUP BY cedula_id
    """
    df = pd.read_sql(query, conn)
    conn.close()

    buenos = df[df['es_buen_pagador'] == 1]
    malos = df[df['es_buen_pagador'] == 0]

    print(f"  [OK] Variable objetivo creada:")
    print(f"      - Buenos pagadores: {len(buenos)} ({len(buenos)/len(df)*100:.1f}%)")
    print(f"      - Malos pagadores: {len(malos)} ({len(malos)/len(df)*100:.1f}%)")

    return df

def combinar_features():
    """Combina todas las features en un solo dataset"""
    print("\n" + "="*60)
    print("COMBINANDO TODAS LAS FEATURES")
    print("="*60)

    # Extraer todas las features
    df_clientes = extraer_features_clientes()
    df_asesorias = extraer_features_asesorias()
    df_historial = extraer_features_historial_cartera()
    df_pagos = extraer_features_comportamiento_pago()
    df_target = crear_variable_objetivo()

    # Combinar todo
    print("\n>> Combinando features...")
    df = df_clientes.copy()

    df = df.merge(df_asesorias, on='cedula', how='left')
    df = df.merge(df_historial, on='cedula', how='left')
    df = df.merge(df_pagos, on='cedula', how='left')
    df = df.merge(df_target, on='cedula', how='left')

    # Eliminar filas sin target (clientes sin préstamos)
    df = df.dropna(subset=['es_buen_pagador'])

    print(f"\n  [OK] Dataset combinado: {len(df)} registros, {len(df.columns)} columnas")

    # Rellenar NaN con 0 para features numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df

def guardar_dataset(df):
    """Guarda el dataset final"""
    print("\n>> Guardando dataset final...")

    # Crear directorio si no existe
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Guardar CSV
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"  [OK] Dataset guardado en: {OUTPUT_FILE}")
    print(f"  [OK] {len(df)} registros, {len(df.columns)} columnas")

    return OUTPUT_FILE

def mostrar_resumen(df):
    """Muestra un resumen del dataset final"""
    print("\n" + "="*60)
    print("RESUMEN DEL DATASET FINAL")
    print("="*60)

    print(f"\nDimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")

    print(f"\nColumnas:")
    for col in df.columns:
        print(f"  - {col}")

    print(f"\nDistribucion de la variable objetivo:")
    print(df['es_buen_pagador'].value_counts())
    print(f"\nBalance: {df['es_buen_pagador'].value_counts(normalize=True) * 100}")

    print(f"\nEstadisticas descriptivas (primeras columnas):")
    print(df.describe().iloc[:, :5])

    print(f"\nValores faltantes:")
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(missing[missing > 0])
    else:
        print("  No hay valores faltantes")

def main():
    """Ejecuta el proceso completo de feature engineering"""
    print("\n" + "="*60)
    print("FEATURE ENGINEERING - CREDISONAR")
    print("="*60)

    # Verificar que existe la BD
    if not Path(SQLITE_DB).exists():
        print(f"\n[ERROR] No se encontro la base de datos: {SQLITE_DB}")
        print("Ejecuta primero: extract_from_godaddy.py")
        return

    try:
        # Combinar features
        df = combinar_features()

        # Mostrar resumen
        mostrar_resumen(df)

        # Guardar dataset
        output_file = guardar_dataset(df)

        print("\n" + "="*60)
        print("FEATURE ENGINEERING COMPLETADO")
        print("="*60)
        print(f"\nDataset listo para entrenar modelos ML:")
        print(f"  {output_file}")
        print(f"\nProximo paso: Entrenar modelos")

    except Exception as e:
        print(f"\n[ERROR] Error durante feature engineering: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
