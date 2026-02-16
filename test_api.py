"""
Script de prueba para la API de Credit Scoring
Prueba varios casos de uso de la API

Uso:
    1. Asegúrate de que la API esté corriendo: python src/api/main.py
    2. Ejecuta este script: python test_api.py
"""

import requests
import json

API_URL = "http://localhost:8000"


def test_health():
    """Prueba el endpoint de health"""
    print("🔍 Probando endpoint /health...")
    response = requests.get(f"{API_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Respuesta: {response.json()}")
    print()


def test_evaluar_cliente_bueno():
    """Prueba con un cliente de buen perfil"""
    print("✅ Probando cliente con buen perfil...")

    cliente = {
        "edad": 35,
        "genero": "M",
        "estado_civil": "casado",
        "nivel_educacion": "universitario",
        "ocupacion": "empleado",
        "antiguedad_trabajo_meses": 60,
        "ingreso_mensual": 30000,
        "monto_solicitado": 50000,
        "plazo_meses": 12,
        "ratio_deuda_ingreso": 0.3,
        "prestamos_anteriores": 3,
        "prestamos_pagados_completos": 3,
        "dias_atraso_promedio": 0,
        "max_dias_atraso": 0,
        "pagos_puntuales_pct": 1.0,
        "antiguedad_cliente_meses": 36,
        "consultas_credito_ultimos_6m": 1
    }

    response = requests.post(f"{API_URL}/evaluar", json=cliente)

    if response.status_code == 200:
        resultado = response.json()
        print(f"   Score: {resultado['score']}")
        print(f"   Decisión: {resultado['decision']}")
        print(f"   Probabilidad default: {resultado['probabilidad_default']:.2%}")
        print(f"   Tasa sugerida: {resultado['tasa_sugerida']}%")
        print(f"   Explicación: {', '.join(resultado['explicacion'])}")
    else:
        print(f"   ERROR: {response.status_code}")
        print(f"   {response.json()}")
    print()


def test_evaluar_cliente_malo():
    """Prueba con un cliente de mal perfil"""
    print("❌ Probando cliente con mal perfil...")

    cliente = {
        "edad": 25,
        "genero": "F",
        "estado_civil": "soltero",
        "nivel_educacion": "secundaria",
        "ocupacion": "independiente",
        "antiguedad_trabajo_meses": 6,
        "ingreso_mensual": 8000,
        "monto_solicitado": 50000,
        "plazo_meses": 24,
        "ratio_deuda_ingreso": 0.7,
        "prestamos_anteriores": 2,
        "prestamos_pagados_completos": 0,
        "dias_atraso_promedio": 45,
        "max_dias_atraso": 90,
        "pagos_puntuales_pct": 0.4,
        "antiguedad_cliente_meses": 3,
        "consultas_credito_ultimos_6m": 5
    }

    response = requests.post(f"{API_URL}/evaluar", json=cliente)

    if response.status_code == 200:
        resultado = response.json()
        print(f"   Score: {resultado['score']}")
        print(f"   Decisión: {resultado['decision']}")
        print(f"   Probabilidad default: {resultado['probabilidad_default']:.2%}")
        print(f"   Tasa sugerida: {resultado['tasa_sugerida']}%")
        print(f"   Explicación: {', '.join(resultado['explicacion'])}")
    else:
        print(f"   ERROR: {response.status_code}")
        print(f"   {response.json()}")
    print()


def test_evaluar_cliente_medio():
    """Prueba con un cliente de perfil medio"""
    print("⚠️  Probando cliente con perfil medio...")

    cliente = {
        "edad": 30,
        "genero": "M",
        "estado_civil": "soltero",
        "nivel_educacion": "preparatoria",
        "ocupacion": "empleado",
        "antiguedad_trabajo_meses": 24,
        "ingreso_mensual": 18000,
        "monto_solicitado": 40000,
        "plazo_meses": 18,
        "ratio_deuda_ingreso": 0.45,
        "prestamos_anteriores": 2,
        "prestamos_pagados_completos": 1,
        "dias_atraso_promedio": 10,
        "max_dias_atraso": 30,
        "pagos_puntuales_pct": 0.75,
        "antiguedad_cliente_meses": 12,
        "consultas_credito_ultimos_6m": 2
    }

    response = requests.post(f"{API_URL}/evaluar", json=cliente)

    if response.status_code == 200:
        resultado = response.json()
        print(f"   Score: {resultado['score']}")
        print(f"   Decisión: {resultado['decision']}")
        print(f"   Probabilidad default: {resultado['probabilidad_default']:.2%}")
        print(f"   Tasa sugerida: {resultado['tasa_sugerida']}%")
        print(f"   Explicación: {', '.join(resultado['explicacion'])}")
    else:
        print(f"   ERROR: {response.status_code}")
        print(f"   {response.json()}")
    print()


def main():
    print("="*60)
    print("🧪 PRUEBAS DE LA API - Credisonar Credit Scoring")
    print("="*60)
    print()

    try:
        # Verificar que la API esté corriendo
        test_health()

        # Probar diferentes perfiles
        test_evaluar_cliente_bueno()
        test_evaluar_cliente_medio()
        test_evaluar_cliente_malo()

        print("="*60)
        print("✅ Todas las pruebas completadas")
        print("="*60)

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar a la API")
        print("   Asegúrate de que la API esté corriendo:")
        print("   python src/api/main.py")
    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    main()
