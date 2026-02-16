"""
Interfaz de Usuario para Credit Scoring - Credisonar
UI simple con Streamlit para evaluar solicitudes de crédito
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.credit_model import CreditScoringModel
from src.data.data_processor import CreditDataProcessor

# Configuración de la página
st.set_page_config(
    page_title="Credisonar - Evaluación Crediticia",
    page_icon="🏦",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .score-approved {
        background-color: #4CAF50;
        color: white;
    }
    .score-rejected {
        background-color: #f44336;
        color: white;
    }
    .score-review {
        background-color: #FF9800;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    """Carga el modelo y procesador (cache para eficiencia)"""
    try:
        modelo = CreditScoringModel(model_type='xgboost')
        procesador = CreditDataProcessor()

        # Intentar cargar modelo entrenado
        try:
            modelo.load("models/credit_model.pkl")
            procesador.load("models/data_processor.pkl")
            return modelo, procesador, True
        except FileNotFoundError:
            st.warning("⚠️ Modelo no encontrado. Entrenar modelo primero ejecutando el notebook.")
            return modelo, procesador, False
    except Exception as e:
        st.error(f"Error al cargar modelo: {e}")
        return None, None, False


def crear_gauge(score, min_val=300, max_val=850):
    """Crea un gauge visual para el score"""
    # Determinar color según score
    if score < 500:
        color = "red"
    elif score < 650:
        color = "orange"
    else:
        color = "green"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Score Crediticio", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [min_val, 500], 'color': '#ffcccc'},
                {'range': [500, 650], 'color': '#ffe0b3'},
                {'range': [650, max_val], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))

    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def main():
    """Función principal de la UI"""

    # Header
    st.markdown('<h1 class="main-header">🏦 CREDISONAR</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center; color: #666;">Sistema de Evaluación Crediticia</h3>', unsafe_allow_html=True)
    st.markdown("---")

    # Cargar modelo
    modelo, procesador, modelo_cargado = load_model()

    if not modelo_cargado:
        st.error("❌ No se puede evaluar sin modelo entrenado")
        st.stop()

    # Tabs
    tab1, tab2 = st.tabs(["📝 Evaluación de Cliente", "📊 Información del Sistema"])

    with tab1:
        # Formulario de evaluación
        st.subheader("Datos del Cliente")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Información Demográfica**")
            edad = st.number_input("Edad", min_value=18, max_value=100, value=35)
            genero = st.selectbox("Género", ["M", "F"])
            estado_civil = st.selectbox("Estado Civil", ["soltero", "casado", "divorciado", "viudo"])
            nivel_educacion = st.selectbox("Nivel Educación",
                ["primaria", "secundaria", "preparatoria", "universitario", "posgrado"])
            ocupacion = st.selectbox("Ocupación",
                ["empleado", "independiente", "profesionista", "comerciante", "otro"])
            antiguedad_trabajo = st.number_input("Antigüedad Trabajo (meses)", min_value=0, value=24)

            st.markdown("**Historial Crediticio**")
            prestamos_anteriores = st.number_input("Préstamos Anteriores", min_value=0, value=2)
            prestamos_pagados = st.number_input("Préstamos Pagados Completos",
                min_value=0, max_value=prestamos_anteriores, value=min(2, prestamos_anteriores))
            dias_atraso = st.number_input("Días Atraso Promedio", min_value=0, value=5)
            max_atraso = st.number_input("Máximo Días Atraso", min_value=0, value=15)
            puntualidad = st.slider("Puntualidad en Pagos (%)", 0, 100, 85) / 100.0

        with col2:
            st.markdown("**Información Financiera**")
            ingreso_mensual = st.number_input("Ingreso Mensual ($)", min_value=1000, value=25000, step=1000)
            monto_solicitado = st.number_input("Monto Solicitado ($)", min_value=1000, value=50000, step=1000)
            plazo_meses = st.selectbox("Plazo (meses)", [6, 12, 18, 24, 36, 48], index=1)
            ratio_deuda = st.slider("Ratio Deuda/Ingreso", 0.0, 1.0, 0.35, 0.05)

            st.markdown("**Comportamiento**")
            antiguedad_cliente = st.number_input("Antigüedad como Cliente (meses)", min_value=0, value=12)
            consultas_credito = st.number_input("Consultas Crédito (últimos 6 meses)", min_value=0, value=2)

        st.markdown("---")

        # Botón de evaluación
        if st.button("🔍 EVALUAR SOLICITUD", use_container_width=True, type="primary"):
            with st.spinner("Analizando solicitud..."):
                # Crear DataFrame con datos
                datos = {
                    'edad': edad,
                    'genero': genero,
                    'estado_civil': estado_civil,
                    'nivel_educacion': nivel_educacion,
                    'ocupacion': ocupacion,
                    'antiguedad_trabajo_meses': antiguedad_trabajo,
                    'ingreso_mensual': ingreso_mensual,
                    'monto_solicitado': monto_solicitado,
                    'plazo_meses': plazo_meses,
                    'ratio_deuda_ingreso': ratio_deuda,
                    'prestamos_anteriores': prestamos_anteriores,
                    'prestamos_pagados_completos': prestamos_pagados,
                    'dias_atraso_promedio': dias_atraso,
                    'max_dias_atraso': max_atraso,
                    'pagos_puntuales_pct': puntualidad,
                    'antiguedad_cliente_meses': antiguedad_cliente,
                    'consultas_credito_ultimos_6m': consultas_credito
                }

                df = pd.DataFrame([datos])

                # Procesar datos
                df_processed = procesador.preprocess(df, fit=False)
                X = procesador.scale_features(df_processed, fit=False)

                # Predecir
                resultado = modelo.predict_complete(X)[0]

                # Mostrar resultados
                st.markdown("---")
                st.subheader("📊 RESULTADO DE LA EVALUACIÓN")

                # Gauge del score
                col1, col2 = st.columns([1, 1])

                with col1:
                    fig_gauge = crear_gauge(resultado['score'])
                    st.plotly_chart(fig_gauge, use_container_width=True)

                with col2:
                    st.markdown(f"### Probabilidad de Impago")
                    st.metric("", f"{resultado['probabilidad_default']:.1%}")

                    st.markdown(f"### Confianza del Modelo")
                    st.metric("", f"{resultado['confianza']:.0%}")

                # Decisión
                decision = resultado['decision']
                if decision == "APROBAR":
                    st.markdown(f"""
                    <div class="score-card score-approved">
                        <h1>✅ CRÉDITO APROBADO</h1>
                        <h3>Score: {resultado['score']}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.success(f"💰 **Monto Aprobado:** ${monto_solicitado:,.0f}")
                        st.success(f"📅 **Plazo:** {plazo_meses} meses")
                    with col2:
                        st.success(f"📊 **Tasa Sugerida:** {resultado['tasa_sugerida']:.1f}% anual")
                        pago_mensual = (monto_solicitado * (1 + resultado['tasa_sugerida']/100)) / plazo_meses
                        st.success(f"💵 **Pago Mensual:** ${pago_mensual:,.0f}")

                elif decision == "RECHAZAR":
                    st.markdown(f"""
                    <div class="score-card score-rejected">
                        <h1>❌ CRÉDITO RECHAZADO</h1>
                        <h3>Score: {resultado['score']}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    st.error("**Motivo:** Riesgo crediticio demasiado alto")
                    st.info("**Recomendación:** El cliente puede reaplicar en 6 meses mejorando su historial crediticio.")

                else:  # REVISAR MANUAL
                    st.markdown(f"""
                    <div class="score-card score-review">
                        <h1>⚠️ REVISAR MANUALMENTE</h1>
                        <h3>Score: {resultado['score']}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                    monto_reducido = monto_solicitado * 0.7
                    st.warning(f"**Sugerencia:** Aprobar con condiciones especiales")
                    st.info(f"- Reducir monto a: ${monto_reducido:,.0f}")
                    st.info(f"- Solicitar aval solidario")
                    st.info(f"- Verificar referencias personales")

                # Análisis
                st.markdown("---")
                st.subheader("🔍 Análisis de Factores")

                # Factores positivos y negativos
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Factores Positivos:**")
                    if puntualidad > 0.8:
                        st.success(f"✓ Buena puntualidad en pagos ({puntualidad:.0%})")
                    if ingreso_mensual > 20000:
                        st.success(f"✓ Ingreso estable (${ingreso_mensual:,.0f})")
                    if prestamos_pagados >= 2:
                        st.success(f"✓ Historial de préstamos pagados ({prestamos_pagados})")
                    if antiguedad_trabajo > 24:
                        st.success(f"✓ Estabilidad laboral ({antiguedad_trabajo} meses)")

                with col2:
                    st.markdown("**Factores de Riesgo:**")
                    if ratio_deuda > 0.5:
                        st.error(f"✗ Alto nivel de endeudamiento ({ratio_deuda:.0%})")
                    if dias_atraso > 15:
                        st.error(f"✗ Historial de atrasos ({dias_atraso} días promedio)")
                    if puntualidad < 0.7:
                        st.error(f"✗ Baja puntualidad ({puntualidad:.0%})")
                    if antiguedad_cliente < 6:
                        st.warning(f"⚠ Cliente nuevo ({antiguedad_cliente} meses)")

    with tab2:
        st.subheader("ℹ️ Información del Sistema")

        st.markdown("""
        ### Sistema de Credit Scoring - Credisonar

        **Versión:** 1.0.0
        **Modelo:** XGBoost Classifier

        #### ¿Cómo funciona?

        El sistema analiza múltiples factores del cliente para predecir el riesgo crediticio:

        1. **Datos Demográficos**: Edad, ocupación, educación
        2. **Información Financiera**: Ingresos, monto solicitado, endeudamiento
        3. **Historial Crediticio**: Préstamos previos, puntualidad de pagos
        4. **Comportamiento**: Antigüedad como cliente, consultas de crédito

        #### Rangos de Score

        - **300-500**: Alto riesgo → Rechazar
        - **500-650**: Riesgo medio → Revisar manualmente
        - **650-850**: Bajo riesgo → Aprobar

        #### Tasas de Interés Sugeridas

        - **800-850**: 15% anual
        - **700-800**: 18% anual
        - **600-700**: 22% anual
        - **500-600**: 28% anual

        ---

        💼 **Producto B2B de Credisonar**
        Para más información: contacto@credisonar.com
        """)

        # Estadísticas del modelo
        if modelo_cargado:
            st.markdown("### 📊 Estado del Modelo")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Estado", "✅ Operativo")
            with col2:
                st.metric("Tipo", "XGBoost")
            with col3:
                st.metric("Versión", "1.0")


if __name__ == "__main__":
    main()
