"""
Pipeline de procesamiento de datos para Credit Scoring
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib


class CreditDataProcessor:
    """Procesa y prepara datos para el modelo de credit scoring"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None

    def load_data(self, file_path):
        """Carga datos desde archivo CSV"""
        df = pd.read_csv(file_path)
        print(f"✅ Datos cargados: {df.shape[0]} registros, {df.shape[1]} columnas")
        return df

    def preprocess(self, df, fit=True):
        """
        Preprocesa los datos

        Args:
            df: DataFrame con datos crudos
            fit: Si True, ajusta los transformadores (usar en training)

        Returns:
            DataFrame procesado
        """
        df = df.copy()

        # Eliminar columnas no necesarias
        columns_to_drop = ['cliente_id', 'fecha_solicitud']
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

        # Codificar variables categóricas
        categorical_columns = ['genero', 'estado_civil', 'nivel_educacion', 'ocupacion']

        for col in categorical_columns:
            if col in df.columns:
                if fit:
                    self.label_encoders[col] = LabelEncoder()
                    df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    if col in self.label_encoders:
                        # Manejar valores no vistos
                        df[col] = df[col].apply(
                            lambda x: x if x in self.label_encoders[col].classes_
                            else self.label_encoders[col].classes_[0]
                        )
                        df[col] = self.label_encoders[col].transform(df[col].astype(str))

        # Feature engineering
        df = self.create_features(df)

        # Manejar valores faltantes
        df = df.fillna(df.median(numeric_only=True))

        return df

    def create_features(self, df):
        """Crea features adicionales (feature engineering)"""

        # Ratio monto/ingreso
        df['ratio_monto_ingreso'] = df['monto_solicitado'] / (df['ingreso_mensual'] + 1)

        # Score de historial (custom)
        if 'prestamos_anteriores' in df.columns and 'prestamos_pagados_completos' in df.columns:
            df['ratio_prestamos_pagados'] = df['prestamos_pagados_completos'] / (df['prestamos_anteriores'] + 1)

        # Capacidad de pago mensual
        if 'plazo_meses' in df.columns:
            df['pago_mensual_estimado'] = df['monto_solicitado'] / df['plazo_meses']
            df['ratio_pago_ingreso'] = df['pago_mensual_estimado'] / (df['ingreso_mensual'] + 1)

        # Flag de cliente nuevo
        if 'antiguedad_cliente_meses' in df.columns:
            df['es_cliente_nuevo'] = (df['antiguedad_cliente_meses'] < 6).astype(int)

        # Score de estabilidad laboral
        if 'antiguedad_trabajo_meses' in df.columns:
            df['estabilidad_laboral'] = (df['antiguedad_trabajo_meses'] > 24).astype(int)

        return df

    def split_features_target(self, df, target_col='default'):
        """Separa features y target"""
        if target_col in df.columns:
            X = df.drop(columns=[target_col])
            y = df[target_col]
            return X, y
        else:
            return df, None

    def scale_features(self, X, fit=True):
        """Normaliza features numéricas"""
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)

        self.feature_names = X.columns.tolist()
        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

    def prepare_data(self, file_path, test_size=0.2, random_state=42):
        """
        Pipeline completo: carga, procesa y divide datos

        Returns:
            X_train, X_test, y_train, y_test
        """
        # Cargar
        df = self.load_data(file_path)

        # Preprocesar
        df_processed = self.preprocess(df, fit=True)

        # Separar features y target
        X, y = self.split_features_target(df_processed)

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Escalar
        X_train = self.scale_features(X_train, fit=True)
        X_test = self.scale_features(X_test, fit=False)

        print(f"✅ Train set: {X_train.shape[0]} registros")
        print(f"✅ Test set: {X_test.shape[0]} registros")
        print(f"📊 Distribución train - Buenos: {(y_train==0).sum()}, Malos: {(y_train==1).sum()}")
        print(f"📊 Distribución test - Buenos: {(y_test==0).sum()}, Malos: {(y_test==1).sum()}")

        return X_train, X_test, y_train, y_test

    def save(self, path):
        """Guarda el procesador para usar en producción"""
        joblib.dump({
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names
        }, path)
        print(f"💾 Procesador guardado en: {path}")

    def load(self, path):
        """Carga el procesador entrenado"""
        data = joblib.load(path)
        self.scaler = data['scaler']
        self.label_encoders = data['label_encoders']
        self.feature_names = data['feature_names']
        print(f"✅ Procesador cargado desde: {path}")


if __name__ == "__main__":
    # Ejemplo de uso
    processor = CreditDataProcessor()

    # Preparar datos
    X_train, X_test, y_train, y_test = processor.prepare_data(
        "data/raw/credit_data_synthetic.csv"
    )

    # Guardar procesador
    processor.save("models/data_processor.pkl")

    print("\n✅ Pipeline de datos completado")
