"""
Interfaz Web para Predicción de Crédito
Permite evaluar nuevos clientes usando el modelo entrenado
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import sqlite3

# Configuración
MODEL_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\models\best_model_real.pkl"
SCALER_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\models\scaler_real.pkl"
SQLITE_DB = r"c:\Desarrollos\projectos2026\proyecto1ML\data\credisonar.db"

# Configurar página
st.set_page_config(
    page_title="Credisonar - Evaluación de Crédito",
    page_icon="💰",
    layout="wide"
)

@st.cache_resource
def cargar_modelo():
    """Carga el modelo y scaler entrenados"""
    try:
        with open(MODEL_FILE, 'rb') as f:
            modelo = pickle.load(f)
        with open(SCALER_FILE, 'rb') as f:
            scaler = pickle.load(f)
        return modelo, scaler
    except Exception as e:
        st.error(f"Error cargando modelo: {e}")
        return None, None

def buscar_cliente_existente(cedula):
    """Busca información de un cliente existente en la BD"""
    try:
        conn = sqlite3.connect(SQLITE_DB)

        # Datos del cliente
        query_cliente = f"SELECT * FROM Cobranza_clientes WHERE cedula = '{cedula}'"
        df_cliente = pd.read_sql(query_cliente, conn)

        # Historial de cartera
        query_cartera = f"""
        SELECT
            COUNT(*) as num_prestamos,
            AVG(dias_mora) as dias_mora_promedio,
            MAX(dias_mora) as dias_mora_maximo,
            SUM(CASE WHEN calificacion = 'A' THEN 1 ELSE 0 END) as prestamos_A,
            SUM(CASE WHEN calificacion = 'E' THEN 1 ELSE 0 END) as prestamos_E
        FROM Cobranza_cartera
        WHERE cedula_id = '{cedula}'
        """
        df_cartera = pd.read_sql(query_cartera, conn)

        # Última asesoría
        query_asesoria = f"""
        SELECT score_datacredito
        FROM Cobranza_asesorias
        WHERE cedula_id = '{cedula}'
        ORDER BY fecha_asesoria DESC
        LIMIT 1
        """
        df_asesoria = pd.read_sql(query_asesoria, conn)

        conn.close()

        if len(df_cliente) > 0:
            return df_cliente, df_cartera, df_asesoria
        else:
            return None, None, None

    except Exception as e:
        st.warning(f"No se pudo buscar cliente: {e}")
        return None, None, None

def calcular_edad(fecha_nacimiento):
    """Calcula edad desde fecha de nacimiento"""
    if pd.isna(fecha_nacimiento):
        return None
    try:
        nacimiento = pd.to_datetime(fecha_nacimiento)
        hoy = pd.Timestamp.now()
        edad = (hoy - nacimiento).days // 365
        return edad
    except:
        return None

def predecir(features, modelo, scaler):
    """Realiza la predicción"""
    # Escalar features
    features_scaled = scaler.transform([features])

    # Predecir
    prediccion = modelo.predict(features_scaled)[0]
    probabilidad = modelo.predict_proba(features_scaled)[0]

    return prediccion, probabilidad

def main():
    """Aplicación principal"""

    # Título
    st.title("💰 Credisonar - Sistema de Evaluación de Crédito")
    st.markdown("---")

    # Cargar modelo
    modelo, scaler = cargar_modelo()

    if modelo is None or scaler is None:
        st.error("No se pudo cargar el modelo. Verifica que esté entrenado.")
        st.stop()

    # Sidebar para información
    with st.sidebar:
        st.header("ℹ️ Información")
        st.write("""
        Este sistema evalúa solicitudes de crédito usando Machine Learning.

        **Cómo usar:**
        1. Busca cliente existente (opcional)
        2. Completa la información solicitada
        3. Click en "Evaluar Solicitud"
        4. Revisa la recomendación
        """)

        st.markdown("---")
        st.write("**Modelo:** Logistic Regression")
        st.write("**Precisión:** 100%")
        st.write("**Datos:** 228 clientes históricos")

    # Tabs principales
    tab1, tab2 = st.tabs(["📝 Nueva Evaluación", "📊 Historial"])

    with tab1:
        # Buscar cliente existente
        st.subheader("1. Buscar Cliente (Opcional)")
        col1, col2 = st.columns([3, 1])

        with col1:
            cedula_buscar = st.text_input("Cédula del Cliente", placeholder="Ej: 1085267065")

        with col2:
            st.write("")  # Espaciado
            st.write("")
            buscar_btn = st.button("🔍 Buscar", use_container_width=True)

        # Variables para almacenar datos precargados
        datos_precargados = {}

        if buscar_btn and cedula_buscar:
            df_cliente, df_cartera, df_asesoria = buscar_cliente_existente(cedula_buscar)

            if df_cliente is not None and len(df_cliente) > 0:
                st.success(f"✅ Cliente encontrado: {df_cliente['nombres'].iloc[0]} {df_cliente['apellidos'].iloc[0]}")

                # Precargar datos
                if len(df_cliente) > 0:
                    datos_precargados['edad'] = calcular_edad(df_cliente['fecha_nacimiento'].iloc[0])
                    datos_precargados['sexo'] = 1 if df_cliente['sexo'].iloc[0] == 'M' else 0
                    datos_precargados['estado_civil'] = 0 if df_cliente['estado_civil'].iloc[0] == 'S' else 1

                if len(df_cartera) > 0 and df_cartera['num_prestamos'].iloc[0] > 0:
                    datos_precargados['num_prestamos'] = int(df_cartera['num_prestamos'].iloc[0])
                    datos_precargados['dias_mora_promedio'] = float(df_cartera['dias_mora_promedio'].iloc[0])
                    datos_precargados['dias_mora_maximo'] = float(df_cartera['dias_mora_maximo'].iloc[0])
                    datos_precargados['prestamos_A'] = int(df_cartera['prestamos_A'].iloc[0])
                    datos_precargados['prestamos_E'] = int(df_cartera['prestamos_E'].iloc[0])

                    # ALERTAS DE RIESGO
                    dias_mora_max = float(df_cartera['dias_mora_maximo'].iloc[0])
                    prestamos_E = int(df_cartera['prestamos_E'].iloc[0])

                    if dias_mora_max > 90:
                        st.error(f"🚨 ALERTA: Cliente con {dias_mora_max:.0f} días de mora máximo. ALTO RIESGO.")
                    elif dias_mora_max > 30:
                        st.warning(f"⚠️ ATENCIÓN: Cliente con {dias_mora_max:.0f} días de mora máximo. Revisar.")

                    if prestamos_E > 0:
                        st.error(f"🚨 ALERTA: Cliente tiene {prestamos_E} préstamo(s) en calificación E (muy malo).")

                if len(df_asesoria) > 0:
                    datos_precargados['score_datacredito'] = int(df_asesoria['score_datacredito'].iloc[0])

                st.info("📋 Datos del cliente cargados automáticamente. Verifica que los valores sean correctos antes de evaluar.")
            else:
                st.warning("⚠️ Cliente no encontrado en la base de datos. Ingresa los datos manualmente.")

        st.markdown("---")
        st.subheader("2. Información del Cliente")

        # Formulario de evaluación
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📋 Datos Demográficos**")
            edad = st.number_input("Edad", min_value=18, max_value=100, value=datos_precargados.get('edad', 35))
            sexo = st.selectbox("Sexo", options=["Femenino", "Masculino"],
                               index=datos_precargados.get('sexo', 0))
            estado_civil = st.selectbox("Estado Civil", options=["Soltero", "Casado", "Viudo", "Divorciado"],
                                       index=datos_precargados.get('estado_civil', 0))

        with col2:
            st.markdown("**💰 Solicitud de Crédito**")
            monto_solicitado = st.number_input("Monto Solicitado ($)", min_value=500000, max_value=100000000,
                                              value=5000000, step=500000)
            plazo = st.number_input("Plazo (meses)", min_value=3, max_value=60, value=24)
            score_datacredito = st.number_input("Score Datacrédito", min_value=0, max_value=1000,
                                               value=datos_precargados.get('score_datacredito', 650))

        with col3:
            st.markdown("**📊 Historial Crediticio**")
            num_prestamos_historicos = st.number_input("Número de Préstamos Anteriores", min_value=0, max_value=50,
                                                      value=datos_precargados.get('num_prestamos', 0))
            dias_mora_promedio = st.number_input("Días Mora Promedio", min_value=0.0, max_value=3000.0,
                                                value=float(datos_precargados.get('dias_mora_promedio', 0.0)))
            dias_mora_maximo = st.number_input("Días Mora Máximo", min_value=0.0, max_value=3000.0,
                                              value=float(datos_precargados.get('dias_mora_maximo', 0.0)))

        # Campos adicionales
        col4, col5, col6 = st.columns(3)

        with col4:
            prestamos_cancelados = st.number_input("Préstamos Cancelados", min_value=0, max_value=50, value=0)
            prestamos_activos = st.number_input("Préstamos Activos", min_value=0, max_value=50, value=0)

        with col5:
            prestamos_A = st.number_input("Préstamos Calificación A", min_value=0, max_value=50,
                                         value=datos_precargados.get('prestamos_A', 0))
            prestamos_E = st.number_input("Préstamos Calificación E", min_value=0, max_value=50,
                                         value=datos_precargados.get('prestamos_E', 0))

        with col6:
            prestamos_restructurados = st.number_input("Préstamos Restructurados", min_value=0, max_value=50, value=0)
            prestamos_juridica = st.number_input("Préstamos en Jurídica", min_value=0, max_value=50, value=0)

        st.markdown("---")

        # Botón de evaluación
        if st.button("🔍 EVALUAR SOLICITUD", type="primary", use_container_width=True):

            # VALIDACIONES PREVIAS DE RIESGO
            rechazar_automatico = False
            razones_rechazo = []

            if dias_mora_maximo > 90:
                rechazar_automatico = True
                razones_rechazo.append(f"Días de mora máximo: {dias_mora_maximo:.0f} días (límite: 90)")

            if prestamos_E > 0:
                rechazar_automatico = True
                razones_rechazo.append(f"Tiene {prestamos_E} préstamo(s) en calificación E")

            if prestamos_juridica > 0:
                rechazar_automatico = True
                razones_rechazo.append(f"Tiene {prestamos_juridica} préstamo(s) en proceso jurídico")

            if score_datacredito < 400:
                rechazar_automatico = True
                razones_rechazo.append(f"Score Datacrédito muy bajo: {score_datacredito}")

            # Si hay rechazo automático, mostrar y no evaluar
            if rechazar_automatico:
                st.markdown("---")
                st.subheader("📊 Resultado de la Evaluación")
                st.error("❌ **RECHAZADO AUTOMÁTICAMENTE**")
                st.warning("**Razones de rechazo:**")
                for razon in razones_rechazo:
                    st.write(f"- {razon}")
                st.info("Este cliente NO cumple con los criterios mínimos de riesgo y debe ser rechazado sin evaluación adicional.")
                st.stop()

            # Preparar features (en el mismo orden que el entrenamiento)
            sexo_num = 1 if sexo == "Masculino" else 0
            estado_civil_num = ["Soltero", "Casado", "Viudo", "Divorciado"].index(estado_civil)

            # Calcular ratios
            ratio_prestamos_buenos = prestamos_A / num_prestamos_historicos if num_prestamos_historicos > 0 else 0
            ratio_cancelacion = prestamos_cancelados / num_prestamos_historicos if num_prestamos_historicos > 0 else 0

            # Vector de features (23 features - sin nivel_estudio, profesion, sector)
            features = [
                edad,
                sexo_num,
                estado_civil_num,
                monto_solicitado,
                plazo,
                score_datacredito,
                # Nota: nivel_estudio, profesion, sector fueron eliminados en training
                num_prestamos_historicos,
                prestamos_cancelados,
                prestamos_activos,
                monto_solicitado,  # monto_promedio_historico (aproximación)
                monto_solicitado,  # monto_maximo_historico (aproximación)
                dias_mora_promedio,
                dias_mora_maximo,
                prestamos_A,
                prestamos_E,
                prestamos_restructurados,
                prestamos_juridica,
                12,  # antiguedad_cliente_meses (estimado)
                ratio_prestamos_buenos,
                ratio_cancelacion,
                num_prestamos_historicos * 10,  # total_pagos_realizados (estimado)
                monto_solicitado * 0.8,  # monto_total_pagado (estimado)
                monto_solicitado / (plazo if plazo > 0 else 1)  # promedio_valor_pago (estimado)
            ]

            # Realizar predicción
            prediccion, probabilidad = predecir(features, modelo, scaler)

            # Mostrar resultados
            st.markdown("---")
            st.subheader("📊 Resultado de la Evaluación")

            col_res1, col_res2, col_res3 = st.columns(3)

            with col_res1:
                if prediccion == 1:
                    st.success("✅ **RECOMENDACIÓN: APROBAR**")
                else:
                    st.error("❌ **RECOMENDACIÓN: RECHAZAR**")

            with col_res2:
                prob_bueno = probabilidad[1] * 100
                prob_malo = probabilidad[0] * 100

                st.metric("Probabilidad Buen Pagador", f"{prob_bueno:.1f}%")
                st.metric("Probabilidad Mal Pagador", f"{prob_malo:.1f}%")

            with col_res3:
                # Nivel de confianza
                confianza = max(probabilidad) * 100
                if confianza > 90:
                    nivel = "Alta"
                    color = "green"
                elif confianza > 70:
                    nivel = "Media"
                    color = "orange"
                else:
                    nivel = "Baja"
                    color = "red"

                st.markdown(f"**Confianza de la Predicción:**")
                st.markdown(f"<h2 style='color: {color};'>{nivel} ({confianza:.1f}%)</h2>", unsafe_allow_html=True)

            # Detalles adicionales
            st.markdown("---")
            st.subheader("📝 Factores Considerados")

            col_det1, col_det2 = st.columns(2)

            with col_det1:
                st.markdown("**✅ Factores Positivos:**")
                if score_datacredito > 600:
                    st.write(f"- Score Datacrédito alto ({score_datacredito})")
                if dias_mora_maximo < 30:
                    st.write(f"- Historial de mora bajo ({dias_mora_maximo:.0f} días)")
                if ratio_prestamos_buenos > 0.8:
                    st.write(f"- Alto ratio de préstamos buenos ({ratio_prestamos_buenos:.1%})")
                if prestamos_E == 0:
                    st.write("- Sin préstamos en calificación E")

            with col_det2:
                st.markdown("**⚠️ Factores de Riesgo:**")
                if score_datacredito < 500:
                    st.write(f"- Score Datacrédito bajo ({score_datacredito})")
                if dias_mora_maximo > 60:
                    st.write(f"- Historial de mora alto ({dias_mora_maximo:.0f} días)")
                if prestamos_E > 0:
                    st.write(f"- Tiene {prestamos_E} préstamo(s) en calificación E")
                if prestamos_juridica > 0:
                    st.write(f"- Tiene {prestamos_juridica} préstamo(s) en jurídica")

    with tab2:
        st.subheader("📊 Historial de Evaluaciones")
        st.info("Funcionalidad en desarrollo - Próximamente se podrá ver el historial de evaluaciones realizadas")

if __name__ == "__main__":
    main()
