# 💰 Sistema de Decisión de Crédito ML - Credisonar

Sistema de Machine Learning para evaluación de créditos que combina:
- ✅ **Estándares financieros colombianos** (Score Datacrédito, ratios deuda/ingreso)
- ✅ **Predicción ML** (Modelo entrenado con historial de pagos)

## 🚀 Despliegue en Streamlit Cloud

**Lee el archivo:** [DESPLIEGUE_STREAMLIT_CLOUD.md](DESPLIEGUE_STREAMLIT_CLOUD.md)

Instrucciones completas paso a paso para desplegar GRATIS.

## 🔧 Ejecución Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar secrets (copiar ejemplo)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Editar .streamlit/secrets.toml con tus credenciales MySQL

# Ejecutar app
streamlit run app_prediccion_v3.py
```

## 📊 Estructura del Proyecto

```
proyecto1ML/
├── app_prediccion_v3.py          # 🌐 Aplicación web Streamlit
├── models/
│   ├── best_model_v2.pkl         # 🤖 Modelo ML entrenado
│   ├── scaler_v2.pkl             # 📐 Normalizador de features
│   └── feature_names_v2.pkl      # 📋 Nombres de features
├── scripts/
│   ├── extract_from_godaddy.py   # 📥 Extracción desde MySQL
│   ├── feature_engineering_v2.py # 🔧 Creación de features
│   └── train_model_v2.py         # 🎓 Entrenamiento del modelo
├── .streamlit/
│   ├── config.toml               # ⚙️ Configuración UI
│   └── secrets.toml.example      # 🔐 Template de credenciales
└── requirements.txt              # 📦 Dependencias Python
```

## 🎯 Características

### Evaluación en 2 Capas

1. **Capa 1 - Estándares Colombia:**
   - Score Datacrédito ≥ 500
   - Ratio deuda/ingreso ≤ 50%
   - Sin mora > 30 días
   - Sin préstamos en jurídica
   - Sin calificación E

2. **Capa 2 - Machine Learning:**
   - Predice probabilidad de buen pagador
   - Basado en historial de 6,400+ pagos
   - Features temporales de comportamiento

### Flujo de Evaluación

1. **Buscar Cliente** → Ingresa cédula
2. **Información Actual** → Sueldo, egresos, Datacrédito HOY
3. **Nuevo Crédito** → Monto y plazo solicitado
4. **Resultado** → Aprobado/Rechazado con probabilidad
5. **Recomendación** → Monto sugerido, cuota al 3% mensual

## 📈 Modelo ML

- **Algoritmo:** Random Forest / Logistic Regression
- **Features:** 40 variables (historial + capacidad de pago)
- **Dataset:** 228 registros, 59.2% buenos pagadores
- **Validación:** StratifiedKFold cross-validation
- **Anti-overfitting:** Regularización L2, árboles poco profundos

## 🔐 Seguridad

- ❌ NO subir `secrets.toml` a GitHub
- ✅ Repo privado recomendado
- ✅ Credenciales encriptadas en Streamlit Cloud
- ✅ Conexión segura a MySQL GoDaddy

## 🆘 Soporte

- **Bugs:** Crear issue en este repo
- **Streamlit:** https://docs.streamlit.io/
- **MySQL:** Verificar permisos remotos en GoDaddy cPanel

---

**Desarrollado con:** Python 3.13 | Streamlit | scikit-learn | pandas | MySQL
**Año:** 2026

