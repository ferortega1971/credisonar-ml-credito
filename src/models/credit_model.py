"""
Modelo de Credit Scoring
Predice riesgo crediticio y calcula score
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix
)
import joblib
import shap


class CreditScoringModel:
    """Modelo de credit scoring con múltiples algoritmos"""

    def __init__(self, model_type='xgboost', min_score=300, max_score=850):
        """
        Args:
            model_type: 'xgboost', 'random_forest', 'logistic'
            min_score: Score mínimo (ej: 300)
            max_score: Score máximo (ej: 850)
        """
        self.model_type = model_type
        self.model = None
        self.min_score = min_score
        self.max_score = max_score
        self.feature_importance = None
        self.explainer = None

        # Inicializar modelo según tipo
        if model_type == 'xgboost':
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss'
            )
        elif model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        elif model_type == 'logistic':
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42
            )
        else:
            raise ValueError(f"Tipo de modelo no soportado: {model_type}")

    def train(self, X_train, y_train):
        """Entrena el modelo"""
        print(f"🚀 Entrenando modelo {self.model_type}...")

        self.model.fit(X_train, y_train)

        # Calcular importancia de features
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': X_train.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)

        print("✅ Modelo entrenado exitosamente")

        return self

    def evaluate(self, X_test, y_test):
        """Evalúa el modelo en datos de prueba"""
        print("\n📊 Evaluación del modelo:")

        # Predicciones
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]

        # Métricas
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba)
        }

        print(f"Accuracy:  {metrics['accuracy']:.3f}")
        print(f"Precision: {metrics['precision']:.3f}")
        print(f"Recall:    {metrics['recall']:.3f}")
        print(f"F1-Score:  {metrics['f1']:.3f}")
        print(f"ROC-AUC:   {metrics['roc_auc']:.3f}")

        print("\n📋 Reporte de clasificación:")
        print(classification_report(y_test, y_pred,
                                   target_names=['Buen Pagador', 'Mal Pagador']))

        print("\n🔢 Matriz de confusión:")
        cm = confusion_matrix(y_test, y_pred)
        print(f"TN: {cm[0,0]}, FP: {cm[0,1]}")
        print(f"FN: {cm[1,0]}, TP: {cm[1,1]}")

        return metrics

    def predict_proba(self, X):
        """Predice probabilidad de default"""
        return self.model.predict_proba(X)[:, 1]

    def predict(self, X):
        """Predice clase (0=bueno, 1=malo)"""
        return self.model.predict(X)

    def calculate_score(self, probability):
        """
        Convierte probabilidad de default a score crediticio

        Alta probabilidad de default = Score bajo
        Baja probabilidad de default = Score alto

        Args:
            probability: Probabilidad de default (0-1)

        Returns:
            Score entre min_score y max_score
        """
        # Invertir: alta probabilidad = bajo score
        inverted_prob = 1 - probability

        # Escalar a rango de score
        score = self.min_score + (inverted_prob * (self.max_score - self.min_score))

        return int(score)

    def get_decision(self, score, threshold_reject=500, threshold_approve=650):
        """
        Determina decisión basada en score

        Args:
            score: Score crediticio
            threshold_reject: Umbral para rechazar
            threshold_approve: Umbral para aprobar

        Returns:
            'RECHAZAR', 'REVISAR MANUAL', o 'APROBAR'
        """
        if score < threshold_reject:
            return 'RECHAZAR'
        elif score < threshold_approve:
            return 'REVISAR MANUAL'
        else:
            return 'APROBAR'

    def get_interest_rate(self, score):
        """Sugiere tasa de interés según score"""
        if score >= 800:
            return 15.0
        elif score >= 700:
            return 18.0
        elif score >= 600:
            return 22.0
        elif score >= 500:
            return 28.0
        else:
            return 0.0  # No se aprueba

    def predict_complete(self, X):
        """
        Predicción completa con score, decisión y explicación

        Returns:
            Lista de diccionarios con resultado completo
        """
        # Probabilidades
        probas = self.predict_proba(X)

        results = []
        for i, proba in enumerate(probas):
            score = self.calculate_score(proba)
            decision = self.get_decision(score)
            rate = self.get_interest_rate(score)

            result = {
                'probabilidad_default': round(float(proba), 4),
                'score': score,
                'decision': decision,
                'tasa_sugerida': rate,
                'confianza': round(abs(0.5 - proba) * 2, 2)  # Qué tan seguro está
            }
            results.append(result)

        return results

    def explain_prediction(self, X, sample_index=0):
        """
        Explica la predicción usando SHAP values

        Args:
            X: Features
            sample_index: Índice de la muestra a explicar

        Returns:
            Explicación de la predicción
        """
        if self.explainer is None:
            print("🔍 Inicializando explicador SHAP...")
            self.explainer = shap.TreeExplainer(self.model)

        shap_values = self.explainer.shap_values(X)

        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Para clasificación binaria

        # Top features que influyen
        sample_shap = shap_values[sample_index]
        feature_names = X.columns

        # Ordenar por valor absoluto
        importance_idx = np.argsort(np.abs(sample_shap))[::-1][:5]

        explanation = []
        for idx in importance_idx:
            feature = feature_names[idx]
            value = X.iloc[sample_index, idx]
            shap_val = sample_shap[idx]
            direction = "incrementa" if shap_val > 0 else "reduce"

            explanation.append({
                'feature': feature,
                'value': float(value),
                'shap_value': float(shap_val),
                'effect': direction
            })

        return explanation

    def get_feature_importance(self, top_n=10):
        """Retorna top N features más importantes"""
        if self.feature_importance is not None:
            return self.feature_importance.head(top_n)
        return None

    def save(self, path):
        """Guarda el modelo"""
        joblib.dump({
            'model': self.model,
            'model_type': self.model_type,
            'min_score': self.min_score,
            'max_score': self.max_score,
            'feature_importance': self.feature_importance
        }, path)
        print(f"💾 Modelo guardado en: {path}")

    def load(self, path):
        """Carga el modelo"""
        data = joblib.load(path)
        self.model = data['model']
        self.model_type = data['model_type']
        self.min_score = data['min_score']
        self.max_score = data['max_score']
        self.feature_importance = data.get('feature_importance')
        print(f"✅ Modelo cargado desde: {path}")


if __name__ == "__main__":
    print("Este módulo debe ser importado, no ejecutado directamente")
    print("Ver notebook de entrenamiento para ejemplos de uso")
