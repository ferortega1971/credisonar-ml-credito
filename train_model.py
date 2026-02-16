"""
Script de entrenamiento del modelo de Credit Scoring
Ejecuta este script para generar datos, entrenar el modelo y guardarlo

Uso:
    python train_model.py
"""

import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Agregar src al path
sys.path.append(str(Path(__file__).parent))

from src.data.generate_synthetic_data import generate_synthetic_credit_data
from src.data.data_processor import CreditDataProcessor
from src.models.credit_model import CreditScoringModel
import pandas as pd


def main():
    print("="*60)
    print("🏦 CREDISONAR - Entrenamiento de Modelo de Credit Scoring")
    print("="*60)
    print()

    # Paso 1: Generar datos sintéticos
    print("📊 PASO 1: Generando datos sintéticos...")
    print("-"*60)
    df = generate_synthetic_credit_data(n_samples=1000)

    # Guardar datos
    data_path = "data/raw/credit_data_synthetic.csv"
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    df.to_csv(data_path, index=False)
    print(f"✅ Datos guardados en: {data_path}")
    print()

    # Paso 2: Procesar datos
    print("🔧 PASO 2: Procesando datos...")
    print("-"*60)
    processor = CreditDataProcessor()
    X_train, X_test, y_train, y_test = processor.prepare_data(
        data_path,
        test_size=0.2,
        random_state=42
    )
    print()

    # Paso 3: Entrenar modelos
    print("🚀 PASO 3: Entrenando modelos...")
    print("-"*60)

    # Crear carpeta de modelos
    Path("models").mkdir(exist_ok=True)

    # Entrenar XGBoost (principal)
    print("\n🤖 Entrenando XGBoost...")
    modelo_xgb = CreditScoringModel(model_type='xgboost')
    modelo_xgb.train(X_train, y_train)

    print("\n📊 Evaluando XGBoost...")
    metrics_xgb = modelo_xgb.evaluate(X_test, y_test)

    # Entrenar Logistic Regression (baseline)
    print("\n🤖 Entrenando Logistic Regression (baseline)...")
    modelo_lr = CreditScoringModel(model_type='logistic')
    modelo_lr.train(X_train, y_train)

    print("\n📊 Evaluando Logistic Regression...")
    metrics_lr = modelo_lr.evaluate(X_test, y_test)

    # Comparar modelos
    print("\n"+"="*60)
    print("📊 COMPARACIÓN DE MODELOS")
    print("="*60)
    comparison = pd.DataFrame({
        'XGBoost': metrics_xgb,
        'Logistic Regression': metrics_lr
    }).round(3)
    print(comparison)
    print()

    # Seleccionar mejor modelo (generalmente XGBoost)
    if metrics_xgb['roc_auc'] >= metrics_lr['roc_auc']:
        print("✅ XGBoost seleccionado como modelo principal")
        mejor_modelo = modelo_xgb
        model_name = "XGBoost"
    else:
        print("✅ Logistic Regression seleccionado como modelo principal")
        mejor_modelo = modelo_lr
        model_name = "Logistic Regression"

    # Paso 4: Guardar modelo y procesador
    print("\n💾 PASO 4: Guardando modelo y procesador...")
    print("-"*60)
    mejor_modelo.save("models/credit_model.pkl")
    processor.save("models/data_processor.pkl")
    print()

    # Paso 5: Prueba del modelo
    print("🧪 PASO 5: Prueba del modelo con ejemplos...")
    print("-"*60)

    # Ejemplo 1: Cliente bueno
    print("\n👤 Ejemplo 1: Cliente con buen perfil")
    cliente_bueno = pd.DataFrame([{
        'edad': 35,
        'genero': 'M',
        'estado_civil': 'casado',
        'nivel_educacion': 'universitario',
        'ocupacion': 'empleado',
        'antiguedad_trabajo_meses': 60,
        'ingreso_mensual': 30000,
        'monto_solicitado': 50000,
        'plazo_meses': 12,
        'ratio_deuda_ingreso': 0.3,
        'prestamos_anteriores': 3,
        'prestamos_pagados_completos': 3,
        'dias_atraso_promedio': 0,
        'max_dias_atraso': 0,
        'pagos_puntuales_pct': 1.0,
        'antiguedad_cliente_meses': 36,
        'consultas_credito_ultimos_6m': 1
    }])

    X_bueno = processor.preprocess(cliente_bueno, fit=False)
    X_bueno = processor.scale_features(X_bueno, fit=False)
    resultado_bueno = mejor_modelo.predict_complete(X_bueno)[0]

    print(f"  Score: {resultado_bueno['score']}")
    print(f"  Decisión: {resultado_bueno['decision']}")
    print(f"  Probabilidad default: {resultado_bueno['probabilidad_default']:.2%}")
    print(f"  Tasa sugerida: {resultado_bueno['tasa_sugerida']}%")

    # Ejemplo 2: Cliente malo
    print("\n👤 Ejemplo 2: Cliente con perfil riesgoso")
    cliente_malo = pd.DataFrame([{
        'edad': 25,
        'genero': 'F',
        'estado_civil': 'soltero',
        'nivel_educacion': 'secundaria',
        'ocupacion': 'independiente',
        'antiguedad_trabajo_meses': 6,
        'ingreso_mensual': 8000,
        'monto_solicitado': 50000,
        'plazo_meses': 24,
        'ratio_deuda_ingreso': 0.7,
        'prestamos_anteriores': 2,
        'prestamos_pagados_completos': 0,
        'dias_atraso_promedio': 45,
        'max_dias_atraso': 90,
        'pagos_puntuales_pct': 0.4,
        'antiguedad_cliente_meses': 3,
        'consultas_credito_ultimos_6m': 5
    }])

    X_malo = processor.preprocess(cliente_malo, fit=False)
    X_malo = processor.scale_features(X_malo, fit=False)
    resultado_malo = mejor_modelo.predict_complete(X_malo)[0]

    print(f"  Score: {resultado_malo['score']}")
    print(f"  Decisión: {resultado_malo['decision']}")
    print(f"  Probabilidad default: {resultado_malo['probabilidad_default']:.2%}")
    print(f"  Tasa sugerida: {resultado_malo['tasa_sugerida']}%")

    # Feature Importance
    print("\n📊 Top 10 Features Más Importantes:")
    print("-"*60)
    if mejor_modelo.feature_importance is not None:
        print(mejor_modelo.feature_importance.head(10).to_string(index=False))

    # Resumen final
    print("\n" + "="*60)
    print("✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
    print("="*60)
    print(f"📁 Modelo guardado: models/credit_model.pkl")
    print(f"📁 Procesador guardado: models/data_processor.pkl")
    print(f"🎯 Modelo seleccionado: {model_name}")
    print(f"📊 ROC-AUC Score: {mejor_modelo.evaluate(X_test, y_test)['roc_auc']:.3f}")
    print()
    print("🚀 PRÓXIMOS PASOS:")
    print("   1. Para probar la UI: streamlit run src/ui/app.py")
    print("   2. Para iniciar la API: python src/api/main.py")
    print("   3. Documentación API: http://localhost:8000/docs")
    print("="*60)


if __name__ == "__main__":
    main()
