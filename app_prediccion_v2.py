"""
Aplicación Web de Predicción de Crédito V2
Interfaz Streamlit mejorada con campos de Datacrédito actuales
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import sqlite3
from pathlib import Path

# Configuración
SQLITE_DB = r"c:\Desarrollos\projectos2026\proyecto1ML\data\credisonar.db"
MODEL_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\models\best_model_v2.pkl"
SCALER_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\models\scaler_v2.pkl"
FEATURE_NAMES_FILE = r"c:\Desarrollos\projectos2026\proyecto1ML\models\feature_names_v2.pkl"

# Cargar modelo
@st.cache_resource
def cargar_modelo():
    """Carga el modelo, scaler y feature names"""
    with open(MODEL_FILE, 'rb') as f:
        modelo = pickle.load(f)

    with open(SCALER_FILE, 'rb') as f:
        scaler = pickle.load(f)

    with open(FEATURE_NAMES_FILE, 'rb') as f:
        feature_names = pickle.load(f)

    return modelo, scaler, feature_names

def conectar_bd():
    """Conecta a la base de datos"""
    return sqlite3.connect(SQLITE_DB)

def buscar_cliente(cedula):
    """Busca datos históricos del cliente en la BD"""
    conn = conectar_bd()

    # Datos del cliente
    query_cliente = f"SELECT * FROM Cobranza_clientes WHERE cedula = '{cedula}'"
    df_cliente = pd.read_sql(query_cliente, conn)

    if len(df_cliente) == 0:
        conn.close()
        return None

    # Calcular edad
    fecha_nac = pd.to_datetime(df_cliente['fecha_nacimiento'].iloc[0])
    edad = (pd.Timestamp.now() - fecha_nac).days // 365
    sexo = 1 if df_cliente['sexo'].iloc[0] == 'M' else 0
    estado_civil_map = {'S': 0, 'C': 1, 'V': 2, 'D': 3}
    estado_civil = estado_civil_map.get(df_cliente['estado_civil'].iloc[0], 0)

    # Datos de cartera
    query_cartera = f"""
    SELECT
        COUNT(*) as num_prestamos,
        SUM(CASE WHEN estado = 'C' THEN 1 ELSE 0 END) as cancelados,
        SUM(CASE WHEN estado = 'A' THEN 1 ELSE 0 END) as activos,
        AVG(valor_desembolsado) as monto_promedio,
        MAX(valor_desembolsado) as monto_maximo,
        MIN(valor_desembolsado) as monto_minimo,
        AVG(dias_mora) as mora_promedio,
        MAX(dias_mora) as mora_maximo,
        SUM(CASE WHEN calificacion = 'A' THEN 1 ELSE 0 END) as calif_A,
        SUM(CASE WHEN calificacion = 'B' THEN 1 ELSE 0 END) as calif_B,
        SUM(CASE WHEN calificacion = 'E' THEN 1 ELSE 0 END) as calif_E,
        SUM(CASE WHEN restructurado = 'S' THEN 1 ELSE 0 END) as restructurados,
        SUM(CASE WHEN en_juridica = 'S' THEN 1 ELSE 0 END) as juridica,
        MIN(fecha_desembolso) as fecha_primer_prestamo,
        MAX(fecha_desembolso) as fecha_ultimo_prestamo
    FROM Cobranza_cartera
    WHERE cedula_id = '{cedula}'
    """
    df_cartera = pd.read_sql(query_cartera, conn)

    # Datos de pagos
    query_pagos = f"""
    SELECT
        COUNT(p.id) as total_pagos,
        SUM(p.valor_pagado) as monto_total_pagado,
        AVG(p.valor_pagado) as promedio_pago
    FROM Cobranza_cartera car
    LEFT JOIN Cobranza_pagos3 p ON car.pagare = p.pagare_id
    WHERE car.cedula_id = '{cedula}'
    """
    df_pagos = pd.read_sql(query_pagos, conn)

    # Última asesoría
    query_asesoria = f"""
    SELECT vivienda_propia
    FROM Cobranza_asesorias
    WHERE cedula_id = '{cedula}'
    ORDER BY fecha_asesoria DESC
    LIMIT 1
    """
    df_asesoria = pd.read_sql(query_asesoria, conn)

    conn.close()

    # Construir diccionario de datos históricos
    if df_cartera['num_prestamos'].iloc[0] > 0:
        num_prestamos = int(df_cartera['num_prestamos'].iloc[0])

        # Calcular antigüedad
        fecha_primer = pd.to_datetime(df_cartera['fecha_primer_prestamo'].iloc[0])
        fecha_ultimo = pd.to_datetime(df_cartera['fecha_ultimo_prestamo'].iloc[0])
        antiguedad_meses = int((pd.Timestamp.now() - fecha_primer).days / 30)
        meses_ultimo = int((pd.Timestamp.now() - fecha_ultimo).days / 30)

        datos_historicos = {
            'edad': edad,
            'sexo': sexo,
            'estado_civil': estado_civil,
            'vivienda_propia_num': 1 if df_asesoria['vivienda_propia'].iloc[0] == 'S' else 0 if len(df_asesoria) > 0 else 0,
            'num_prestamos_historicos': num_prestamos,
            'prestamos_cancelados': int(df_cartera['cancelados'].iloc[0]),
            'prestamos_activos': int(df_cartera['activos'].iloc[0]),
            'monto_promedio_historico': float(df_cartera['monto_promedio'].iloc[0]),
            'monto_maximo_historico': float(df_cartera['monto_maximo'].iloc[0]),
            'monto_minimo_historico': float(df_cartera['monto_minimo'].iloc[0]),
            'dias_mora_promedio': float(df_cartera['mora_promedio'].iloc[0]),
            'dias_mora_maximo': float(df_cartera['mora_maximo'].iloc[0]),
            'prestamos_calificacion_A': int(df_cartera['calif_A'].iloc[0]),
            'prestamos_calificacion_B': int(df_cartera['calif_B'].iloc[0]),
            'prestamos_calificacion_E': int(df_cartera['calif_E'].iloc[0]),
            'prestamos_restructurados': int(df_cartera['restructurados'].iloc[0]),
            'prestamos_en_juridica': int(df_cartera['juridica'].iloc[0]),
            'antiguedad_cliente_meses': antiguedad_meses,
            'meses_desde_ultimo_prestamo': meses_ultimo,
            'ratio_prestamos_buenos': (int(df_cartera['calif_A'].iloc[0]) + int(df_cartera['calif_B'].iloc[0])) / num_prestamos,
            'ratio_prestamos_malos': int(df_cartera['calif_E'].iloc[0]) / num_prestamos,
            'ratio_cancelacion': int(df_cartera['cancelados'].iloc[0]) / num_prestamos,
            'ratio_activos': int(df_cartera['activos'].iloc[0]) / num_prestamos,
            'total_pagos_realizados': int(df_pagos['total_pagos'].iloc[0]) if df_pagos['total_pagos'].iloc[0] else 0,
            'monto_total_pagado': float(df_pagos['monto_total_pagado'].iloc[0]) if df_pagos['monto_total_pagado'].iloc[0] else 0,
            'promedio_valor_pago': float(df_pagos['promedio_pago'].iloc[0]) if df_pagos['promedio_pago'].iloc[0] else 0,
        }
    else:
        # Cliente sin historial
        datos_historicos = {
            'edad': edad,
            'sexo': sexo,
            'estado_civil': estado_civil,
            'vivienda_propia_num': 0,
            'num_prestamos_historicos': 0,
            'prestamos_cancelados': 0,
            'prestamos_activos': 0,
            'monto_promedio_historico': 0,
            'monto_maximo_historico': 0,
            'monto_minimo_historico': 0,
            'dias_mora_promedio': 0,
            'dias_mora_maximo': 0,
            'prestamos_calificacion_A': 0,
            'prestamos_calificacion_B': 0,
            'prestamos_calificacion_E': 0,
            'prestamos_restructurados': 0,
            'prestamos_en_juridica': 0,
            'antiguedad_cliente_meses': 0,
            'meses_desde_ultimo_prestamo': 0,
            'ratio_prestamos_buenos': 0,
            'ratio_prestamos_malos': 0,
            'ratio_cancelacion': 0,
            'ratio_activos': 0,
            'total_pagos_realizados': 0,
            'monto_total_pagado': 0,
            'promedio_valor_pago': 0,
        }

    return datos_historicos

def predecir_credito(datos, modelo, scaler, feature_names):
    """Realiza la predicción"""
    # Crear DataFrame con todas las features
    df = pd.DataFrame([datos])[feature_names]

    # Escalar
    datos_scaled = scaler.transform(df)

    # Predecir
    probabilidad = modelo.predict_proba(datos_scaled)[0][1]
    decision = modelo.predict(datos_scaled)[0]

    return probabilidad, decision

def calcular_monto_sugerido(probabilidad, monto_solicitado, plazo, sueldo_mensual, total_deudas_datacredito, valor_mensual_datacredito):
    """Calcula el monto sugerido a prestar basado en la probabilidad y capacidad de pago"""

    # Tasa de interés mensual: 3.0%
    tasa_mensual = 0.03

    # Capacidad de pago disponible
    capacidad_disponible = (sueldo_mensual * 0.4) - valor_mensual_datacredito  # 40% del sueldo - deudas actuales

    if probabilidad >= 0.8:
        # Clientes excelentes: hasta 100% de lo solicitado
        monto_sugerido = monto_solicitado
    elif probabilidad >= 0.6:
        # Clientes buenos: hasta 80% de lo solicitado
        monto_sugerido = monto_solicitado * 0.8
    elif probabilidad >= 0.4:
        # Clientes regulares: hasta 60% de lo solicitado
        monto_sugerido = monto_solicitado * 0.6
    else:
        # Clientes con riesgo: hasta 40% o rechazar
        monto_sugerido = monto_solicitado * 0.4

    # Ajustar por capacidad de pago (cuota no debe superar capacidad disponible)
    # Calcular cuota con 3% mensual
    if plazo > 0:
        cuota_estimada = (monto_sugerido * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo))
    else:
        cuota_estimada = 0

    if cuota_estimada > capacidad_disponible and capacidad_disponible > 0 and plazo > 0:
        # Reducir monto para que cuota quepa en capacidad
        monto_sugerido = (capacidad_disponible * (1 - (1 + tasa_mensual) ** (-plazo))) / tasa_mensual

    return max(0, int(monto_sugerido))

# Interfaz de Streamlit
def main():
    st.set_page_config(page_title="Sistema de Decisión de Crédito V2", page_icon="💰", layout="wide")

    st.title("💰 Sistema de Decisión de Crédito V2")
    st.markdown("**Versión mejorada con Datacrédito actual y sin reglas hardcodeadas**")

    # Cargar modelo
    try:
        modelo, scaler, feature_names = cargar_modelo()
        st.success("✅ Modelo cargado correctamente")
    except Exception as e:
        st.error(f"❌ Error cargando el modelo: {e}")
        return

    st.markdown("---")

    # Tabs
    tab1, tab2 = st.tabs(["📋 Nueva Solicitud", "ℹ️ Información del Modelo"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📝 Datos del Cliente")

            cedula = st.text_input("Cédula del Cliente", key="cedula")

            if cedula and st.button("🔍 Buscar Cliente"):
                with st.spinner("Buscando información histórica..."):
                    datos_historicos = buscar_cliente(cedula)
                    if datos_historicos:
                        st.session_state['datos_historicos'] = datos_historicos
                        st.success(f"✅ Cliente encontrado - {datos_historicos['num_prestamos_historicos']} préstamos previos")

                        # Mostrar resumen del historial
                        with st.expander("Ver historial del cliente"):
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Préstamos Totales", datos_historicos['num_prestamos_historicos'])
                                st.metric("Préstamos Cancelados", datos_historicos['prestamos_cancelados'])
                            with col_b:
                                st.metric("Días Mora Promedio", f"{datos_historicos['dias_mora_promedio']:.0f}")
                                st.metric("Días Mora Máximo", datos_historicos['dias_mora_maximo'])
                            with col_c:
                                st.metric("Calificación A", datos_historicos['prestamos_calificacion_A'])
                                st.metric("Calificación E", datos_historicos['prestamos_calificacion_E'])
                    else:
                        st.info("ℹ️ Cliente nuevo - No hay historial previo en Credisonar")
                        # Pedir datos básicos para cliente nuevo
                        edad = st.number_input("Edad", min_value=18, max_value=100, value=30)
                        sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
                        estado_civil = st.selectbox("Estado Civil", ["Soltero", "Casado", "Viudo", "Divorciado"])
                        vivienda_propia = st.selectbox("Vivienda Propia", ["Sí", "No"])

                        # Crear datos históricos vacíos para cliente nuevo
                        estado_civil_map = {"Soltero": 0, "Casado": 1, "Viudo": 2, "Divorciado": 3}
                        datos_historicos = {
                            'edad': edad,
                            'sexo': 1 if sexo == "Masculino" else 0,
                            'estado_civil': estado_civil_map[estado_civil],
                            'vivienda_propia_num': 1 if vivienda_propia == "Sí" else 0,
                            'num_prestamos_historicos': 0,
                            'prestamos_cancelados': 0,
                            'prestamos_activos': 0,
                            'monto_promedio_historico': 0,
                            'monto_maximo_historico': 0,
                            'monto_minimo_historico': 0,
                            'dias_mora_promedio': 0,
                            'dias_mora_maximo': 0,
                            'prestamos_calificacion_A': 0,
                            'prestamos_calificacion_B': 0,
                            'prestamos_calificacion_E': 0,
                            'prestamos_restructurados': 0,
                            'prestamos_en_juridica': 0,
                            'antiguedad_cliente_meses': 0,
                            'meses_desde_ultimo_prestamo': 0,
                            'ratio_prestamos_buenos': 0,
                            'ratio_prestamos_malos': 0,
                            'ratio_cancelacion': 0,
                            'ratio_activos': 0,
                            'total_pagos_realizados': 0,
                            'monto_total_pagado': 0,
                            'promedio_valor_pago': 0,
                        }
                        st.session_state['datos_historicos'] = datos_historicos

            st.markdown("---")

            # Datos de la solicitud actual
            st.subheader("💵 Datos de la Solicitud")
            monto_solicitado = st.number_input("Monto Solicitado", min_value=100000, max_value=50000000, value=2000000, step=100000)
            plazo = st.selectbox("Plazo (meses)", [6, 12, 18, 24, 36, 48])

        with col2:
            st.subheader("📊 Datos de Datacrédito ACTUALES")
            st.markdown("*Información al día de hoy*")

            score_datacredito_actual = st.number_input(
                "Score Datacrédito HOY",
                min_value=0,
                max_value=950,
                value=600,
                help="Score actual reportado en Datacrédito"
            )

            total_deudas_datacredito = st.number_input(
                "Total Deudas Reportadas en Datacrédito HOY",
                min_value=0,
                max_value=500000000,
                value=0,
                step=100000,
                help="Suma total de deudas vigentes en Datacrédito"
            )

            valor_mensual_datacredito = st.number_input(
                "Valor Mensual Reportado en Datacrédito HOY",
                min_value=0,
                max_value=50000000,
                value=0,
                step=50000,
                help="Cuota mensual total que paga actualmente"
            )

            st.markdown("---")
            st.subheader("💼 Datos Financieros ACTUALES")

            sueldo_mensual_actual = st.number_input(
                "Sueldo Mensual HOY",
                min_value=0,
                max_value=100000000,
                value=2000000,
                step=100000,
                help="Ingreso mensual actual del cliente"
            )

            total_egresos_actual = st.number_input(
                "Total Egresos Mensuales",
                min_value=0,
                max_value=100000000,
                value=1000000,
                step=100000,
                help="Gastos fijos mensuales (sin incluir deudas Datacrédito)"
            )

        # Botón de predicción
        st.markdown("---")
        if st.button("🔮 EVALUAR SOLICITUD", type="primary", use_container_width=True):
            if 'datos_historicos' not in st.session_state:
                st.error("❌ Primero debes buscar el cliente o ingresar datos para cliente nuevo")
            else:
                with st.spinner("Analizando solicitud..."):
                    # Combinar datos históricos + datos actuales
                    datos_completos = st.session_state['datos_historicos'].copy()

                    # Agregar datos de la solicitud actual
                    datos_completos['monto_solicitado'] = monto_solicitado
                    datos_completos['plazo'] = plazo
                    datos_completos['score_datacredito_historico'] = score_datacredito_actual
                    datos_completos['sueldo_mensual'] = sueldo_mensual_actual
                    datos_completos['total_egresos'] = total_egresos_actual
                    datos_completos['capacidad_pago'] = sueldo_mensual_actual - total_egresos_actual - valor_mensual_datacredito
                    datos_completos['ratio_ingresos_egresos'] = total_egresos_actual / sueldo_mensual_actual if sueldo_mensual_actual > 0 else 0

                    # Hacer predicción
                    probabilidad, decision = predecir_credito(datos_completos, modelo, scaler, feature_names)

                    # Calcular monto sugerido
                    monto_sugerido = calcular_monto_sugerido(
                        probabilidad,
                        monto_solicitado,
                        plazo,
                        sueldo_mensual_actual,
                        total_deudas_datacredito,
                        valor_mensual_datacredito
                    )

                    # Mostrar resultados
                    st.markdown("---")
                    st.subheader("📊 RESULTADO DE LA EVALUACIÓN")

                    col_res1, col_res2, col_res3 = st.columns(3)

                    with col_res1:
                        if decision == 1:
                            st.success("✅ **APROBADO**")
                        else:
                            st.error("❌ **RECHAZADO**")

                    with col_res2:
                        color = "green" if probabilidad >= 0.7 else "orange" if probabilidad >= 0.4 else "red"
                        st.metric(
                            "Probabilidad de Buen Pagador",
                            f"{probabilidad*100:.1f}%",
                        )

                    with col_res3:
                        st.metric(
                            "Monto Sugerido",
                            f"${monto_sugerido:,.0f}"
                        )

                    # Calcular cuotas mensuales estimadas (3% mensual)
                    tasa_mensual = 0.03

                    # Cuota para monto solicitado
                    if plazo > 0:
                        cuota_solicitado = (monto_solicitado * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo))
                    else:
                        cuota_solicitado = 0

                    # Cuota para monto sugerido
                    if plazo > 0 and monto_sugerido > 0:
                        cuota_sugerido = (monto_sugerido * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo))
                    else:
                        cuota_sugerido = 0

                    # Análisis detallado
                    with st.expander("📈 Ver Análisis Detallado", expanded=True):
                        col_det1, col_det2 = st.columns(2)

                        with col_det1:
                            st.markdown("**💰 Análisis de Capacidad de Pago:**")
                            capacidad = datos_completos['capacidad_pago']
                            st.write(f"- Ingreso mensual: ${sueldo_mensual_actual:,.0f}")
                            st.write(f"- Egresos mensuales: ${total_egresos_actual:,.0f}")
                            st.write(f"- Deudas Datacrédito mensuales: ${valor_mensual_datacredito:,.0f}")
                            st.write(f"- **Capacidad disponible: ${capacidad:,.0f}**")

                            st.markdown("")
                            st.markdown("**📅 Cuotas Mensuales Estimadas (3.0% mensual):**")
                            st.write(f"- Cuota si presta ${monto_solicitado:,.0f}: **${cuota_solicitado:,.0f}**/mes")
                            st.write(f"- Cuota si presta ${monto_sugerido:,.0f}: **${cuota_sugerido:,.0f}**/mes")

                            # Indicador de viabilidad
                            if cuota_sugerido > 0:
                                if cuota_sugerido <= capacidad:
                                    st.success(f"✅ La cuota sugerida CABE en la capacidad de pago")
                                elif capacidad > 0:
                                    st.warning(f"⚠️ La cuota sugerida es {cuota_sugerido/capacidad:.1f}x la capacidad disponible")
                                else:
                                    st.error(f"❌ No hay capacidad de pago disponible")

                        with col_det2:
                            st.markdown("**📊 Historial Credisonar:**")
                            if datos_completos['num_prestamos_historicos'] > 0:
                                st.write(f"- Préstamos previos: {datos_completos['num_prestamos_historicos']}")
                                st.write(f"- Tasa cancelación: {datos_completos['ratio_cancelacion']*100:.0f}%")
                                st.write(f"- Mora máxima: {datos_completos['dias_mora_maximo']:.0f} días")
                                st.write(f"- Préstamos buenos: {datos_completos['ratio_prestamos_buenos']*100:.0f}%")

                                if datos_completos['prestamos_en_juridica'] > 0:
                                    st.error(f"🚨 {datos_completos['prestamos_en_juridica']} préstamo(s) en jurídica")
                                if datos_completos['prestamos_restructurados'] > 0:
                                    st.warning(f"⚠️ {datos_completos['prestamos_restructurados']} préstamo(s) restructurado(s)")
                            else:
                                st.info("- Cliente nuevo sin historial")
                                st.write("- Primera vez en Credisonar")
                                st.write("- Evaluación basada en Datacrédito")

                    # Recomendación
                    st.markdown("---")
                    st.subheader("💡 Recomendación")
                    if decision == 1 and probabilidad >= 0.7:
                        st.success(f"✅ Se recomienda APROBAR el préstamo por **${monto_sugerido:,.0f}** a {plazo} meses. El cliente tiene alta probabilidad de cumplir con sus obligaciones.")
                    elif decision == 1:
                        st.warning(f"⚠️ Se puede APROBAR con precaución por **${monto_sugerido:,.0f}**. Considerar garantías adicionales o codeudor.")
                    else:
                        st.error(f"❌ Se recomienda RECHAZAR la solicitud. El perfil presenta alto riesgo de mora.")

    with tab2:
        st.subheader("ℹ️ Información del Modelo")
        st.write(f"""
        - **Modelo**: Gradient Boosting Classifier V2
        - **Features**: {len(feature_names)} variables
        - **Dataset**: 228 clientes históricos
        - **Balance**: 59% buenos pagadores, 41% malos

        **Mejoras en V2:**
        - ✅ Sin reglas hardcodeadas (100% Machine Learning)
        - ✅ Incluye datos de Datacrédito ACTUALES
        - ✅ Considera capacidad de pago real
        - ✅ Regularización para evitar overfitting
        - ✅ Funciona con clientes nuevos SIN historial

        **Features más importantes:**
        1. Días de mora promedio (histórico)
        2. Días de mora máximo (histórico)
        3. Préstamos en jurídica (histórico)
        4. Ratio de cancelación
        5. Capacidad de pago actual
        """)

if __name__ == "__main__":
    main()
