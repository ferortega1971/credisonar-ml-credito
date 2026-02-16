"""
Script para importar datos MySQL a SQLite local
Extrae solo las 6 tablas clave del proyecto ML
"""

import sqlite3
import re
from pathlib import Path

# Configuración
SQL_FILE = r"C:\Users\feror\Downloads\sigcrec10 (2).sql"
SQLITE_DB = r"c:\Desarrollos\projectos2026\proyecto1ML\data\credisonar.db"

# Tablas a importar
TABLAS_CLAVE = [
    'Cobranza_clientes',
    'Cobranza_asesorias',
    'Cobranza_cartera',
    'Cobranza_pagos3',
    'Cobranza_plan_cuotas_online',
    'Cobranza_plan_de_pagos'
]

def limpiar_sql_para_sqlite(sql_content):
    """
    Convierte sintaxis MySQL a SQLite
    """
    # Reemplazar tipos de datos MySQL por SQLite
    sql_content = re.sub(r'ENGINE=\w+\s+DEFAULT\s+CHARSET=\w+\s+COLLATE=\w+;', ');', sql_content)
    sql_content = re.sub(r'int\(\d+\)', 'INTEGER', sql_content)
    sql_content = re.sub(r'varchar\((\d+)\)', r'TEXT', sql_content)
    sql_content = re.sub(r'double', 'REAL', sql_content)
    sql_content = re.sub(r'tinyint\(\d+\)', 'INTEGER', sql_content)
    sql_content = re.sub(r'date', 'TEXT', sql_content)

    return sql_content

def extraer_tabla(sql_file, nombre_tabla):
    """
    Extrae CREATE TABLE e INSERTs de una tabla específica
    """
    print(f"  >> Extrayendo: {nombre_tabla}...")

    with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Buscar CREATE TABLE
    create_pattern = rf"CREATE TABLE `{nombre_tabla}` \((.*?)\) ENGINE"
    create_match = re.search(create_pattern, content, re.DOTALL)

    if not create_match:
        print(f"    [!] No se encontro CREATE TABLE para {nombre_tabla}")
        return None, []

    create_sql = f"CREATE TABLE IF NOT EXISTS {nombre_tabla} ({create_match.group(1)});"
    create_sql = limpiar_sql_para_sqlite(create_sql)

    # Buscar INSERTs
    insert_pattern = rf"INSERT INTO `{nombre_tabla}` \((.*?)\) VALUES\s+(.*?);"
    inserts = []

    for match in re.finditer(insert_pattern, content, re.DOTALL):
        columns = match.group(1)
        values = match.group(2)

        # Limpiar valores (quitar comillas especiales de MySQL)
        values = values.replace('\\n', ' ').replace('\\r', '')

        insert_sql = f"INSERT OR IGNORE INTO {nombre_tabla} ({columns}) VALUES {values};"
        inserts.append(insert_sql)

    print(f"    [OK] {len(inserts)} registros encontrados")
    return create_sql, inserts

def importar_a_sqlite():
    """
    Importa las tablas clave a SQLite
    """
    print("\n>> Importando datos a SQLite...\n")

    # Crear directorio si no existe
    Path(SQLITE_DB).parent.mkdir(parents=True, exist_ok=True)

    # Conectar a SQLite
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()

    total_registros = 0

    for tabla in TABLAS_CLAVE:
        print(f"\n>> Procesando: {tabla}")

        # Extraer CREATE e INSERTs
        create_sql, inserts = extraer_tabla(SQL_FILE, tabla)

        if not create_sql:
            continue

        # Ejecutar CREATE TABLE
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
            cursor.execute(create_sql)
            print(f"  [OK] Tabla creada")
        except Exception as e:
            print(f"  [ERROR] Error creando tabla: {e}")
            continue

        # Ejecutar INSERTs en lotes
        batch_size = 100
        for i in range(0, len(inserts), batch_size):
            batch = inserts[i:i + batch_size]
            try:
                for insert_sql in batch:
                    cursor.execute(insert_sql)
                conn.commit()
                print(f"  >> Insertados {min(i + batch_size, len(inserts))}/{len(inserts)} registros", end='\r')
            except Exception as e:
                print(f"\n  [!] Error en insert: {e}")
                continue

        print(f"\n  [OK] {len(inserts)} registros importados")
        total_registros += len(inserts)

    conn.close()

    print(f"\n\n[COMPLETADO] Importacion completada!")
    print(f">> Total de registros: {total_registros:,}")
    print(f">> Base de datos: {SQLITE_DB}")

    # Mostrar resumen
    print("\n>> Resumen de tablas:")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()

    for tabla in TABLAS_CLAVE:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"  - {tabla}: {count:,} registros")
        except:
            print(f"  - {tabla}: Error al contar")

    conn.close()

if __name__ == "__main__":
    try:
        importar_a_sqlite()
    except Exception as e:
        print(f"\n[ERROR] Error fatal: {e}")
        import traceback
        traceback.print_exc()
