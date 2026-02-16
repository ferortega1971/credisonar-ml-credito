"""
Entrenamiento de Modelos ML con Datos Reales
Entrena y compara múltiples modelos para predicción de buenos pagadores
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
import warnings
warnings.filterwarnings('ignore')

# Configuración
DATA_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\data\dataset_ml.csv"
MODEL_DIR = r"c:\Desarrollos\projectos2026\proyecto1ML\models"
SCALER_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\models\scaler_real.pkl"
BEST_MODEL_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\models\best_model_real.pkl"

def cargar_datos():
    """Carga el dataset procesado"""
    print("\n>> Cargando datos...")
    df = pd.read_sql(DATA_FILE)
    print(f"  [OK] {len(df)} registros cargados")
    return df

def preparar_datos(df):
    """Prepara los datos para entrenamiento"""
    print("\n>> Preparando datos...")

    # Eliminar columnas no útiles para el modelo
    columnas_a_eliminar = ['cedula', 'fecha_ultima_asesoria']
    df = df.drop([col for col in columnas_a_eliminar if col in df.columns], axis=1)

    # Separar features y target
    X = df.drop('es_buen_pagador', axis=1)
    y = df['es_buen_pagador']

    # Eliminar columnas con todos NaN
    X = X.dropna(axis=1, how='all')

    # Rellenar NaN restantes con 0
    X = X.fillna(0)

    print(f"  [OK] Features: {X.shape[1]} columnas")
    print(f"  [OK] Target: {len(y)} registros")
    print(f"      - Clase 1 (buenos): {(y==1).sum()} ({(y==1).sum()/len(y)*100:.1f}%)")
    print(f"      - Clase 0 (malos): {(y==0).sum()} ({(y==0).sum()/len(y)*100:.1f}%)")

    return X, y

def dividir_datos(X, y):
    """Divide en train y test"""
    print("\n>> Dividiendo datos en train/test...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print(f"  [OK] Train: {len(X_train)} registros")
    print(f"  [OK] Test: {len(X_test)} registros")

    return X_train, X_test, y_train, y_test

def escalar_datos(X_train, X_test):
    """Escala los datos"""
    print("\n>> Escalando features...")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Guardar scaler
    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)
    with open(SCALER_FILE, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"  [OK] Datos escalados")
    print(f"  [OK] Scaler guardado en: {SCALER_FILE}")

    return X_train_scaled, X_test_scaled, scaler

def entrenar_modelos(X_train, y_train):
    """Entrena múltiples modelos"""
    print("\n" + "="*60)
    print("ENTRENANDO MODELOS")
    print("="*60)

    modelos = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42, max_depth=5)
    }

    modelos_entrenados = {}

    for nombre, modelo in modelos.items():
        print(f"\n>> Entrenando: {nombre}...")

        # Entrenar
        modelo.fit(X_train, y_train)

        # Cross-validation
        cv_scores = cross_val_score(modelo, X_train, y_train, cv=5, scoring='accuracy')

        print(f"  [OK] Entrenado")
        print(f"      - CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")

        modelos_entrenados[nombre] = modelo

    return modelos_entrenados

def evaluar_modelos(modelos, X_test, y_test):
    """Evalúa todos los modelos"""
    print("\n" + "="*60)
    print("EVALUACION DE MODELOS")
    print("="*60)

    resultados = {}

    for nombre, modelo in modelos.items():
        print(f"\n>> Evaluando: {nombre}")

        # Predecir
        y_pred = modelo.predict(X_test)
        y_proba = modelo.predict_proba(X_test)[:, 1] if hasattr(modelo, 'predict_proba') else None

        # Métricas
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        print(f"  Accuracy:  {accuracy:.3f}")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall:    {recall:.3f}")
        print(f"  F1-Score:  {f1:.3f}")

        if y_proba is not None:
            auc = roc_auc_score(y_test, y_proba)
            print(f"  ROC-AUC:   {auc:.3f}")
        else:
            auc = None

        # Matriz de confusión
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n  Matriz de Confusion:")
        print(f"    TN: {cm[0,0]}, FP: {cm[0,1]}")
        print(f"    FN: {cm[1,0]}, TP: {cm[1,1]}")

        resultados[nombre] = {
            'modelo': modelo,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc,
            'y_pred': y_pred,
            'y_proba': y_proba
        }

    return resultados

def seleccionar_mejor_modelo(resultados):
    """Selecciona el mejor modelo basado en F1-Score"""
    print("\n" + "="*60)
    print("SELECCION DEL MEJOR MODELO")
    print("="*60)

    # Ordenar por F1-Score
    ranking = sorted(resultados.items(), key=lambda x: x[1]['f1'], reverse=True)

    print(f"\nRanking por F1-Score:")
    for i, (nombre, res) in enumerate(ranking, 1):
        print(f"  {i}. {nombre}: {res['f1']:.3f}")

    mejor_nombre, mejor_resultado = ranking[0]
    print(f"\nMejor modelo: {mejor_nombre}")
    print(f"  - F1-Score: {mejor_resultado['f1']:.3f}")
    print(f"  - Accuracy: {mejor_resultado['accuracy']:.3f}")
    print(f"  - Precision: {mejor_resultado['precision']:.3f}")
    print(f"  - Recall: {mejor_resultado['recall']:.3f}")

    return mejor_nombre, mejor_resultado['modelo']

def guardar_modelo(modelo, nombre):
    """Guarda el mejor modelo"""
    print(f"\n>> Guardando modelo...")

    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)

    with open(BEST_MODEL_FILE, 'wb') as f:
        pickle.dump(modelo, f)

    print(f"  [OK] Modelo guardado en: {BEST_MODEL_FILE}")

    # Guardar info del modelo
    info_file = Path(MODEL_DIR) / "model_info.txt"
    with open(info_file, 'w') as f:
        f.write(f"Mejor Modelo: {nombre}\n")
        f.write(f"Fecha: {pd.Timestamp.now()}\n")
        f.write(f"Dataset: {DATA_FILE}\n")

    print(f"  [OK] Info guardada en: {info_file}")

def analizar_importancia_features(modelo, feature_names):
    """Analiza la importancia de las features"""
    print("\n" + "="*60)
    print("IMPORTANCIA DE FEATURES")
    print("="*60)

    if hasattr(modelo, 'feature_importances_'):
        importances = modelo.feature_importances_
        indices = np.argsort(importances)[::-1]

        print(f"\nTop 10 features más importantes:")
        for i in range(min(10, len(feature_names))):
            idx = indices[i]
            print(f"  {i+1}. {feature_names[idx]}: {importances[idx]:.4f}")

    elif hasattr(modelo, 'coef_'):
        coef = modelo.coef_[0]
        indices = np.argsort(np.abs(coef))[::-1]

        print(f"\nTop 10 features más importantes (coeficientes):")
        for i in range(min(10, len(feature_names))):
            idx = indices[i]
            print(f"  {i+1}. {feature_names[idx]}: {coef[idx]:.4f}")

def main():
    """Ejecuta el pipeline completo de entrenamiento"""
    print("\n" + "="*60)
    print("ENTRENAMIENTO DE MODELO ML - DATOS REALES")
    print("="*60)

    # Verificar que existe el dataset
    if not Path(DATA_FILE).exists():
        print(f"\n[ERROR] No se encontro el dataset: {DATA_FILE}")
        print("Ejecuta primero: feature_engineering.py")
        return

    try:
        # Cargar y preparar datos
        df = pd.read_csv(DATA_FILE)
        X, y = preparar_datos(df)

        # Dividir datos
        X_train, X_test, y_train, y_test = dividir_datos(X, y)

        # Escalar datos
        X_train_scaled, X_test_scaled, scaler = escalar_datos(X_train, X_test)

        # Entrenar modelos
        modelos = entrenar_modelos(X_train_scaled, y_train)

        # Evaluar modelos
        resultados = evaluar_modelos(modelos, X_test_scaled, y_test)

        # Seleccionar mejor modelo
        mejor_nombre, mejor_modelo = seleccionar_mejor_modelo(resultados)

        # Guardar modelo
        guardar_modelo(mejor_modelo, mejor_nombre)

        # Analizar importancia de features
        analizar_importancia_features(mejor_modelo, X.columns.tolist())

        print("\n" + "="*60)
        print("ENTRENAMIENTO COMPLETADO")
        print("="*60)
        print(f"\nModelo guardado y listo para usar!")
        print(f"  - Modelo: {BEST_MODEL_FILE}")
        print(f"  - Scaler: {SCALER_FILE}")
        print(f"\nProximo paso: Crear API o interfaz de prediccion")

    except Exception as e:
        print(f"\n[ERROR] Error durante el entrenamiento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
