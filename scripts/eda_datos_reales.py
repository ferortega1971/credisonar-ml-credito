"""
Análisis Exploratorio de Datos (EDA)
Analiza los datos reales extraídos de GoDaddy
"""

import pandas as pd
import sqlite3
from pathlib import Path

# Configuración
SQLITE_DB = r"c:\Desarrollos\projectos2026\proyecto1ML\data\credisonar.db"

def conectar_sqlite():
    """Conecta a la BD SQLite local"""
    return sqlite3.connect(SQLITE_DB)

def analizar_clientes():
    """Analiza la tabla de clientes"""
    print("\n" + "="*60)
    print("ANALISIS DE CLIENTES")
    print("="*60)

    conn = conectar_sqlite()
    df = pd.read_sql("SELECT * FROM Cobranza_clientes", conn)

    print(f"\nTotal de clientes: {len(df):,}")
    print(f"\nColumnas: {list(df.columns)}")
    print(f"\nPrimeros registros:")
    print(df.head())

    # Distribución por sexo
    if 'sexo' in df.columns:
        print(f"\nDistribucion por sexo:")
        print(df['sexo'].value_counts())

    # Distribución por estado civil
    if 'estado_civil' in df.columns:
        print(f"\nDistribucion por estado civil:")
        print(df['estado_civil'].value_counts())

    conn.close()
    return df

def analizar_cartera():
    """Analiza la tabla de cartera (préstamos)"""
    print("\n" + "="*60)
    print("ANALISIS DE CARTERA (PRESTAMOS)")
    print("="*60)

    conn = conectar_sqlite()
    df = pd.read_sql("SELECT * FROM Cobranza_cartera", conn)

    print(f"\nTotal de prestamos: {len(df):,}")
    print(f"\nColumnas: {list(df.columns)}")

    # Estadísticas de montos
    if 'valor_desembolsado' in df.columns:
        print(f"\nEstadisticas de montos desembolsados:")
        print(df['valor_desembolsado'].describe())

    # Distribución por estado
    if 'estado' in df.columns:
        print(f"\nDistribucion por estado:")
        print(df['estado'].value_counts())

    # Distribución por calificación
    if 'calificacion' in df.columns:
        print(f"\nDistribucion por calificacion:")
        print(df['calificacion'].value_counts())
        print("\nCalificacion (A=Excelente, B=Bueno, C=Regular, D=Malo, E=Muy malo)")

    # Días de mora
    if 'dias_mora' in df.columns:
        print(f"\nEstadisticas de dias de mora:")
        print(df['dias_mora'].describe())

    conn.close()
    return df

def analizar_pagos():
    """Analiza la tabla de pagos"""
    print("\n" + "="*60)
    print("ANALISIS DE PAGOS")
    print("="*60)

    conn = conectar_sqlite()
    df = pd.read_sql("SELECT * FROM Cobranza_pagos3", conn)

    print(f"\nTotal de pagos: {len(df):,}")
    print(f"\nColumnas: {list(df.columns)}")

    # Pagos por pagaré
    if 'pagare_id' in df.columns:
        pagos_por_pagare = df.groupby('pagare_id').size()
        print(f"\nEstadisticas de pagos por prestamo:")
        print(pagos_por_pagare.describe())

    # Montos de pago
    if 'valor_pagado' in df.columns:
        print(f"\nEstadisticas de montos pagados:")
        print(df['valor_pagado'].describe())

    # Fechas de pago
    if 'fecha_pago' in df.columns:
        df['fecha_pago'] = pd.to_datetime(df['fecha_pago'])
        print(f"\nRango de fechas:")
        print(f"  Desde: {df['fecha_pago'].min()}")
        print(f"  Hasta: {df['fecha_pago'].max()}")

    conn.close()
    return df

def analizar_relaciones():
    """Analiza las relaciones entre tablas"""
    print("\n" + "="*60)
    print("ANALISIS DE RELACIONES")
    print("="*60)

    conn = conectar_sqlite()

    # Clientes con préstamos
    query = """
    SELECT
        COUNT(DISTINCT c.cedula) as total_clientes,
        COUNT(DISTINCT car.pagare) as total_prestamos,
        CAST(COUNT(DISTINCT car.pagare) AS FLOAT) / COUNT(DISTINCT c.cedula) as prestamos_por_cliente
    FROM Cobranza_clientes c
    LEFT JOIN Cobranza_cartera car ON c.cedula = car.cedula_id
    """
    df = pd.read_sql(query, conn)
    print(f"\nRelacion Clientes-Prestamos:")
    print(df)

    # Préstamos con pagos
    query = """
    SELECT
        COUNT(DISTINCT car.pagare) as prestamos_con_pagos,
        COUNT(DISTINCT p.pagare_id) as total_pagares_pagados,
        COUNT(*) as total_pagos,
        CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT p.pagare_id) as pagos_por_prestamo
    FROM Cobranza_cartera car
    INNER JOIN Cobranza_pagos3 p ON car.pagare = p.pagare_id
    """
    df = pd.read_sql(query, conn)
    print(f"\nRelacion Prestamos-Pagos:")
    print(df)

    # Clientes buenos vs malos
    query = """
    SELECT
        calificacion,
        COUNT(*) as cantidad,
        AVG(dias_mora) as promedio_dias_mora,
        AVG(valor_desembolsado) as promedio_monto
    FROM Cobranza_cartera
    GROUP BY calificacion
    ORDER BY calificacion
    """
    df = pd.read_sql(query, conn)
    print(f"\nCalificacion de prestamos:")
    print(df)

    conn.close()

def identificar_buenos_malos_pagadores():
    """Identifica buenos y malos pagadores"""
    print("\n" + "="*60)
    print("IDENTIFICACION DE BUENOS Y MALOS PAGADORES")
    print("="*60)

    conn = conectar_sqlite()

    # Criterio: Clientes con todos sus préstamos en calificación A o B
    query = """
    SELECT
        cedula_id,
        COUNT(*) as total_prestamos,
        SUM(CASE WHEN calificacion IN ('A', 'B') THEN 1 ELSE 0 END) as prestamos_buenos,
        AVG(dias_mora) as promedio_dias_mora,
        MAX(dias_mora) as max_dias_mora,
        AVG(valor_desembolsado) as promedio_monto
    FROM Cobranza_cartera
    WHERE estado IN ('A', 'C')  -- Activos o Cancelados
    GROUP BY cedula_id
    """
    df = pd.read_sql(query, conn)

    # Clasificar
    df['es_buen_pagador'] = (
        (df['prestamos_buenos'] == df['total_prestamos']) &
        (df['max_dias_mora'] <= 30)
    )

    buenos = df[df['es_buen_pagador'] == True]
    malos = df[df['es_buen_pagador'] == False]

    print(f"\nBuenos pagadores: {len(buenos)} ({len(buenos)/len(df)*100:.1f}%)")
    print(f"Malos pagadores: {len(malos)} ({len(malos)/len(df)*100:.1f}%)")

    print(f"\nEstadisticas de buenos pagadores:")
    print(buenos[['promedio_dias_mora', 'max_dias_mora', 'promedio_monto']].describe())

    print(f"\nEstadisticas de malos pagadores:")
    print(malos[['promedio_dias_mora', 'max_dias_mora', 'promedio_monto']].describe())

    # Guardar para referencia
    df.to_csv(r"c:\Desarrollos\projectos2026\proyecto1ML\data\clientes_clasificados.csv", index=False)
    print(f"\nClasificacion guardada en: data/clientes_clasificados.csv")

    conn.close()
    return df

def main():
    """Ejecuta todos los análisis"""
    print("\n" + "="*60)
    print("ANALISIS EXPLORATORIO DE DATOS - CREDISONAR")
    print("="*60)

    # Verificar que existe la BD
    if not Path(SQLITE_DB).exists():
        print(f"\n[ERROR] No se encontro la base de datos: {SQLITE_DB}")
        print("Ejecuta primero: extract_from_godaddy.py")
        return

    try:
        # Análisis individuales
        df_clientes = analizar_clientes()
        df_cartera = analizar_cartera()
        df_pagos = analizar_pagos()

        # Análisis de relaciones
        analizar_relaciones()

        # Identificar buenos y malos pagadores
        df_clasificacion = identificar_buenos_malos_pagadores()

        print("\n" + "="*60)
        print("ANALISIS COMPLETADO")
        print("="*60)
        print(f"\nProximo paso: Feature Engineering")

    except Exception as e:
        print(f"\n[ERROR] Error durante el analisis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
