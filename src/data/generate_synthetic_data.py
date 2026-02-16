"""
Generador de datos sintéticos para Credit Scoring
Simula datos reales de clientes de Credisonar
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)


def generate_synthetic_credit_data(n_samples=1000):
    """
    Genera datos sintéticos realistas de clientes de crédito

    Args:
        n_samples: Número de registros a generar

    Returns:
        DataFrame con datos sintéticos
    """

    data = []

    for i in range(n_samples):
        # Datos demográficos
        edad = np.random.randint(18, 70)
        genero = np.random.choice(['M', 'F'], p=[0.52, 0.48])
        estado_civil = np.random.choice(
            ['soltero', 'casado', 'divorciado', 'viudo'],
            p=[0.35, 0.45, 0.15, 0.05]
        )
        nivel_educacion = np.random.choice(
            ['primaria', 'secundaria', 'preparatoria', 'universitario', 'posgrado'],
            p=[0.10, 0.25, 0.30, 0.30, 0.05]
        )
        ocupacion = np.random.choice(
            ['empleado', 'independiente', 'profesionista', 'comerciante', 'otro'],
            p=[0.50, 0.20, 0.15, 0.10, 0.05]
        )
        antiguedad_trabajo_meses = np.random.randint(1, 240)

        # Datos financieros (correlacionados con educación y edad)
        base_ingreso = {
            'primaria': 8000,
            'secundaria': 12000,
            'preparatoria': 18000,
            'universitario': 28000,
            'posgrado': 45000
        }
        ingreso_mensual = int(np.random.normal(
            base_ingreso[nivel_educacion],
            base_ingreso[nivel_educacion] * 0.3
        ))
        ingreso_mensual = max(5000, ingreso_mensual)

        # Monto solicitado (típicamente 2-5x el ingreso mensual)
        monto_solicitado = int(np.random.uniform(
            ingreso_mensual * 1.5,
            ingreso_mensual * 6
        ))

        plazo_meses = np.random.choice([6, 12, 18, 24, 36, 48], p=[0.10, 0.30, 0.25, 0.20, 0.10, 0.05])

        # Ratio deuda-ingreso (indicador importante)
        ratio_deuda_ingreso = round(np.random.uniform(0.1, 0.8), 2)

        # Historial crediticio
        prestamos_anteriores = np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8],
                                                p=[0.20, 0.25, 0.20, 0.15, 0.10, 0.05, 0.03, 0.01, 0.01])

        if prestamos_anteriores == 0:
            prestamos_pagados_completos = 0
            dias_atraso_promedio = 0
            max_dias_atraso = 0
            pagos_puntuales_pct = 1.0
        else:
            prestamos_pagados_completos = np.random.randint(0, prestamos_anteriores + 1)
            dias_atraso_promedio = int(np.random.exponential(10))
            max_dias_atraso = int(np.random.exponential(20))
            pagos_puntuales_pct = round(np.random.beta(8, 2), 2)  # Sesgado hacia buenos pagadores

        # Comportamiento
        antiguedad_cliente_meses = np.random.randint(0, 120)
        consultas_credito_ultimos_6m = np.random.choice([0, 1, 2, 3, 4, 5, 6],
                                                         p=[0.30, 0.25, 0.20, 0.15, 0.05, 0.03, 0.02])

        # Variable objetivo: default (1 = malo, 0 = bueno)
        # Basado en reglas realistas
        default_probability = 0.15  # Base rate

        # Factores que aumentan riesgo
        if ratio_deuda_ingreso > 0.5:
            default_probability += 0.2
        if dias_atraso_promedio > 15:
            default_probability += 0.25
        if pagos_puntuales_pct < 0.7:
            default_probability += 0.2
        if consultas_credito_ultimos_6m > 3:
            default_probability += 0.15
        if ingreso_mensual < 10000:
            default_probability += 0.1
        if antiguedad_trabajo_meses < 6:
            default_probability += 0.1

        # Factores que reducen riesgo
        if prestamos_pagados_completos >= 2:
            default_probability -= 0.15
        if ingreso_mensual > 30000:
            default_probability -= 0.1
        if pagos_puntuales_pct > 0.9:
            default_probability -= 0.15

        default_probability = max(0.01, min(0.95, default_probability))
        default = 1 if np.random.random() < default_probability else 0

        record = {
            'cliente_id': f'CLI{1000 + i}',
            'fecha_solicitud': (datetime.now() - timedelta(days=np.random.randint(0, 730))).strftime('%Y-%m-%d'),

            # Demográficos
            'edad': edad,
            'genero': genero,
            'estado_civil': estado_civil,
            'nivel_educacion': nivel_educacion,
            'ocupacion': ocupacion,
            'antiguedad_trabajo_meses': antiguedad_trabajo_meses,

            # Financieros
            'ingreso_mensual': ingreso_mensual,
            'monto_solicitado': monto_solicitado,
            'plazo_meses': plazo_meses,
            'ratio_deuda_ingreso': ratio_deuda_ingreso,

            # Historial
            'prestamos_anteriores': prestamos_anteriores,
            'prestamos_pagados_completos': prestamos_pagados_completos,
            'dias_atraso_promedio': dias_atraso_promedio,
            'max_dias_atraso': max_dias_atraso,
            'pagos_puntuales_pct': pagos_puntuales_pct,

            # Comportamiento
            'antiguedad_cliente_meses': antiguedad_cliente_meses,
            'consultas_credito_ultimos_6m': consultas_credito_ultimos_6m,

            # Target
            'default': default
        }

        data.append(record)

    df = pd.DataFrame(data)

    print(f"✅ Generados {n_samples} registros sintéticos")
    print(f"📊 Distribución de defaults: {df['default'].value_counts().to_dict()}")
    print(f"📊 Tasa de morosidad: {df['default'].mean():.2%}")

    return df


if __name__ == "__main__":
    # Generar datos
    df = generate_synthetic_credit_data(n_samples=1000)

    # Guardar
    output_path = "data/raw/credit_data_synthetic.csv"
    df.to_csv(output_path, index=False)
    print(f"💾 Datos guardados en: {output_path}")

    # Mostrar resumen
    print("\n📋 Resumen de los datos:")
    print(df.describe())
    print("\n📊 Primeros registros:")
    print(df.head())
