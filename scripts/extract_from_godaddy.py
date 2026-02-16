"""
Script para extraer datos directamente desde MySQL (GoDaddy) a SQLite
Mucho más confiable que parsear el archivo SQL
"""

import pandas as pd
import mysql.connector
import sqlite3
from pathlib import Path

# Configuración SQLite
SQLITE_DB = r"c:\Desarrollos\projectos2026\proyecto1ML\data\credisonar.db"

# Tablas a extraer
TABLAS = [
    'Cobranza_clientes',
    'Cobranza_asesorias',
    'Cobranza_cartera',
    'Cobranza_pagos3',
    'Cobranza_plan_cuotas_online',
    'Cobranza_plan_de_pagos'
]

def conectar_mysql():
    """
    Conecta a MySQL en GoDaddy
    Debes configurar las credenciales primero
    """
    # CREDENCIALES DE GODADDY
    config = {
        'host': '92.204.216.38',  # IP dedicada de GoDaddy
        'port': 3306,
        'database': 'sigcrec10',
        'user': 'sigcrec_user',
        'password': 'Skidata2013*'
    }

    try:
        conn = mysql.connector.connect(**config)
        print("[OK] Conectado a MySQL (GoDaddy)")
        return conn
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a MySQL: {e}")
        print("\nAsegurate de:")
        print("1. Habilitar acceso remoto en tu panel de GoDaddy")
        print("2. Agregar tu IP publica a la whitelist")
        print("3. Verificar host, user, password")
        return None

def extraer_tablas():
    """
    Extrae todas las tablas de MySQL a SQLite
    """
    print("\n>> Extrayendo datos desde GoDaddy MySQL...\n")

    # Conectar a MySQL
    mysql_conn = conectar_mysql()
    if not mysql_conn:
        return

    # Crear directorio SQLite
    Path(SQLITE_DB).parent.mkdir(parents=True, exist_ok=True)

    # Conectar a SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)

    total_registros = 0

    for tabla in TABLAS:
        try:
            print(f">> Extrayendo: {tabla}...")

            # Leer tabla desde MySQL con pandas
            df = pd.read_sql(f"SELECT * FROM {tabla}", mysql_conn)

            print(f"  >> {len(df):,} registros encontrados")

            # Guardar en SQLite
            df.to_sql(tabla, sqlite_conn, if_exists='replace', index=False)

            print(f"  [OK] {len(df):,} registros importados a SQLite")
            total_registros += len(df)

        except Exception as e:
            print(f"  [ERROR] Error con {tabla}: {e}")
            continue

    # Cerrar conexiones
    mysql_conn.close()
    sqlite_conn.close()

    print(f"\n[COMPLETADO] Extraccion completada!")
    print(f">> Total de registros: {total_registros:,}")
    print(f">> Base de datos SQLite: {SQLITE_DB}")

    # Mostrar resumen
    print("\n>> Resumen de tablas:")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    cursor = sqlite_conn.cursor()

    for tabla in TABLAS:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"  - {tabla}: {count:,} registros")
        except:
            print(f"  - {tabla}: No encontrada")

    sqlite_conn.close()

def test_conexion():
    """
    Prueba la conexión a MySQL
    """
    print(">> Probando conexion a GoDaddy MySQL...")
    conn = conectar_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        print(f"\n[OK] Conexion exitosa! Tablas encontradas: {len(tablas)}")
        print("\nPrimeras 10 tablas:")
        for tabla in tablas[:10]:
            print(f"  - {tabla[0]}")
        conn.close()
    else:
        print("\n[ERROR] No se pudo conectar. Revisa las credenciales.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Modo test: solo probar conexión
        test_conexion()
    else:
        # Modo normal: extraer todas las tablas
        extraer_tablas()
