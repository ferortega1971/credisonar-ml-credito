"""
Aplicación Web de Predicción de Crédito V3
Interfaz reorganizada con flujo lógico: Cliente → Info Actual → Crédito → Resultado
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import pymysql
from pathlib import Path
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Configuración de rutas (relativas para Streamlit Cloud)
BASE_DIR = Path(__file__).parent
MODEL_FILE = BASE_DIR / "models" / "best_model_v2.pkl"
SCALER_FILE = BASE_DIR / "models" / "scaler_v2.pkl"
FEATURE_NAMES_FILE = BASE_DIR / "models" / "feature_names_v2.pkl"

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
    """Conecta a la base de datos MySQL (local o Streamlit Cloud)"""
    try:
        mysql_config = st.secrets["mysql"]
        conn = pymysql.connect(
            host=mysql_config["host"],
            port=int(mysql_config.get("port", 3306)),
            database=mysql_config["database"],
            user=mysql_config["user"],
            password=mysql_config["password"]
        )
        return conn
    except (FileNotFoundError, KeyError) as e:
        st.error("""
        ⚠️ **Error de configuración de base de datos**

        No se encontraron las credenciales MySQL.

        **Para desarrollo local:** Crea el archivo `.streamlit/secrets.toml` con las credenciales.
        **Para Streamlit Cloud:** Configura los secrets en Settings > Secrets.
        """)
        st.stop()
        return None

def buscar_cliente(cedula):
    """Busca datos del cliente en la BD"""
    try:
        conn = conectar_bd()

        # Datos básicos del cliente
        query_cliente = f"SELECT * FROM Cobranza_clientes WHERE cedula = '{cedula}'"
        df_cliente = pd.read_sql(query_cliente, conn)

        if len(df_cliente) == 0:
            conn.close()
            return None

        # Calcular edad
        fecha_nac = pd.to_datetime(df_cliente['fecha_nacimiento'].iloc[0], errors='coerce')
        if pd.isna(fecha_nac):
            st.error(f"Error: Fecha de nacimiento inválida para cliente {cedula}")
            conn.close()
            return None

        edad = (pd.Timestamp.now() - fecha_nac).days // 365
        sexo = 1 if df_cliente['sexo'].iloc[0] == 'M' else 0
        estado_civil_map = {'S': 0, 'C': 1, 'V': 2, 'D': 3}
        estado_civil = estado_civil_map.get(df_cliente['estado_civil'].iloc[0], 0)

        # Datos de contacto
        nombres = df_cliente['nombres'].iloc[0] if pd.notna(df_cliente['nombres'].iloc[0]) else ''
        apellidos = df_cliente['apellidos'].iloc[0] if pd.notna(df_cliente['apellidos'].iloc[0]) else ''
        nombre = f"{nombres} {apellidos}".strip()

        # Obtener correo de Cobranza_clientes si existe
        correo = df_cliente['correo'].iloc[0] if 'correo' in df_cliente.columns and pd.notna(df_cliente['correo'].iloc[0]) else ''

        # Datos de cartera (historial)
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

        # Última asesoría (para obtener contacto y vivienda)
        query_asesoria = f"""
        SELECT vivienda_propia, tel_celular, direccion_of, fecha_asesoria
        FROM Cobranza_asesorias
        WHERE cedula_id = '{cedula}'
        ORDER BY fecha_asesoria DESC
        LIMIT 1
        """
        df_asesoria = pd.read_sql(query_asesoria, conn)

        # Obtener teléfono, dirección y fecha de asesoría si existe
        telefono = ''
        direccion = ''
        fecha_ultima_asesoria = None
        if len(df_asesoria) > 0:
            telefono = df_asesoria['tel_celular'].iloc[0] if pd.notna(df_asesoria['tel_celular'].iloc[0]) else ''
            direccion = df_asesoria['direccion_of'].iloc[0] if pd.notna(df_asesoria['direccion_of'].iloc[0]) else ''
            if pd.notna(df_asesoria['fecha_asesoria'].iloc[0]):
                fecha_ultima_asesoria = pd.to_datetime(df_asesoria['fecha_asesoria'].iloc[0])

        # Créditos activos en Credisonar (estado = 'A')
        query_activos = f"""
        SELECT
            COUNT(*) as creditos_vigentes,
            SUM(saldo_capital) as saldo_capital_total,
            SUM(valor_cuota) as cuota_mensual_total,
            AVG(valor_desembolsado) as monto_promedio_aprobado,
            MAX(valor_desembolsado) as monto_maximo_aprobado,
            GROUP_CONCAT(DISTINCT calificacion) as calificaciones
        FROM Cobranza_cartera
        WHERE cedula_id = '{cedula}' AND estado = 'A'
        """
        df_activos = pd.read_sql(query_activos, conn)

        # Historial de préstamos (para mostrar tabla de historia)
        query_historial_prestamos = f"""
        SELECT
            c.pagare,
            c.fecha_desembolso,
            MAX(p.fecha_pago) as fecha_ultimo_pago,
            c.valor_desembolsado as monto_aprobado,
            MAX(pc.valor) as valor_cuota,
            c.estado,
            c.calificacion
        FROM Cobranza_cartera c
        LEFT JOIN Cobranza_pagos3 p ON c.pagare = p.pagare_id
        LEFT JOIN Cobranza_plan_cuotas pc ON c.pagare = pc.pagare_id
        WHERE c.cedula_id = '{cedula}'
        GROUP BY c.pagare, c.fecha_desembolso, c.valor_desembolsado, c.estado, c.calificacion
        ORDER BY c.fecha_desembolso DESC
        LIMIT 10
        """
        df_historial_prestamos = pd.read_sql(query_historial_prestamos, conn)

        conn.close()

        # Datos de créditos activos en Credisonar
        creditos_activos = {
            'creditos_vigentes': int(df_activos['creditos_vigentes'].iloc[0]) if df_activos['creditos_vigentes'].iloc[0] else 0,
            'saldo_capital': float(df_activos['saldo_capital_total'].iloc[0]) if df_activos['saldo_capital_total'].iloc[0] else 0,
            'cuota_mensual': float(df_activos['cuota_mensual_total'].iloc[0]) if df_activos['cuota_mensual_total'].iloc[0] else 0,
            'monto_aprobado': float(df_activos['monto_maximo_aprobado'].iloc[0]) if df_activos['monto_maximo_aprobado'].iloc[0] else 0,
            'calificaciones': df_activos['calificaciones'].iloc[0] if pd.notna(df_activos['calificaciones'].iloc[0]) else '',
            'tiene_calificacion_E': 'E' in str(df_activos['calificaciones'].iloc[0]) if pd.notna(df_activos['calificaciones'].iloc[0]) else False
        }

        # Construir diccionario completo
        cliente = {
            'cedula': cedula,
            'nombre': nombre,
            'telefono': telefono,
            'correo': correo,
            'direccion': direccion,
            'fecha_nacimiento': fecha_nac,
            'fecha_ultima_asesoria': fecha_ultima_asesoria,
            'edad': edad,
            'sexo': sexo,
            'sexo_texto': df_cliente['sexo'].iloc[0],
            'estado_civil': estado_civil,
            'estado_civil_texto': df_cliente['estado_civil'].iloc[0],
            'creditos_activos': creditos_activos,
            'historial_prestamos': df_historial_prestamos,
        }

        # Historial de créditos
        if df_cartera['num_prestamos'].iloc[0] > 0:
            num_prestamos = int(df_cartera['num_prestamos'].iloc[0])
            fecha_primer = pd.to_datetime(df_cartera['fecha_primer_prestamo'].iloc[0])
            fecha_ultimo = pd.to_datetime(df_cartera['fecha_ultimo_prestamo'].iloc[0])
            antiguedad_meses = int((pd.Timestamp.now() - fecha_primer).days / 30)
            meses_ultimo = int((pd.Timestamp.now() - fecha_ultimo).days / 30)

            cliente['historial'] = {
                'vivienda_propia_num': 1 if len(df_asesoria) > 0 and df_asesoria['vivienda_propia'].iloc[0] == 'S' else 0,
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
            cliente['historial'] = {
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
            # Si no hay historial, asegurar que creditos_activos esté inicializado
            if 'creditos_activos' not in cliente:
                cliente['creditos_activos'] = {
                    'creditos_vigentes': 0,
                    'saldo_capital': 0,
                    'cuota_mensual': 0,
                    'monto_aprobado': 0,
                    'calificaciones': '',
                    'tiene_calificacion_E': False
                }

        return cliente

    except Exception as e:
        st.error(f"❌ Error al buscar cliente: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        try:
            conn.close()
        except:
            pass
        return None

def predecir_credito(datos, modelo, scaler, feature_names):
    """Realiza la predicción"""
    df = pd.DataFrame([datos])[feature_names]
    datos_scaled = scaler.transform(df)
    probabilidad = modelo.predict_proba(datos_scaled)[0][1]
    decision = modelo.predict(datos_scaled)[0]
    return probabilidad, decision

def calcular_monto_sugerido(probabilidad, monto_solicitado, plazo, sueldo_mensual, total_deudas_datacredito, valor_mensual_datacredito):
    """Calcula el monto sugerido basado en probabilidad y capacidad de pago"""
    tasa_mensual = 0.03
    capacidad_disponible = (sueldo_mensual * 0.4) - valor_mensual_datacredito

    if probabilidad >= 0.8:
        monto_sugerido = monto_solicitado
    elif probabilidad >= 0.6:
        monto_sugerido = monto_solicitado * 0.8
    elif probabilidad >= 0.4:
        monto_sugerido = monto_solicitado * 0.6
    else:
        monto_sugerido = monto_solicitado * 0.4

    if plazo > 0:
        cuota_estimada = (monto_sugerido * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo))
    else:
        cuota_estimada = 0

    if cuota_estimada > capacidad_disponible and capacidad_disponible > 0 and plazo > 0:
        monto_sugerido = (capacidad_disponible * (1 - (1 + tasa_mensual) ** (-plazo))) / tasa_mensual

    return max(0, int(monto_sugerido))

def generar_pdf(cliente, datos_financieros, resultado_evaluacion):
    """Genera un PDF con el resultado de la evaluación de crédito"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#FF4B4B'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    # Fecha y hora de generación
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Título
    elements.append(Paragraph("EVALUACIÓN DE CRÉDITO - CREDISONAR", title_style))
    elements.append(Paragraph(f"Fecha de generación: {fecha_hora}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

    # Datos del cliente
    elements.append(Paragraph("DATOS DEL CLIENTE", styles['Heading2']))
    cliente_data = [
        ['Cédula:', cliente['cedula']],
        ['Nombre:', cliente['nombre']],
        ['Teléfono:', cliente['telefono']],
        ['Dirección:', cliente['direccion']]
    ]
    cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(cliente_table)
    elements.append(Spacer(1, 0.3*inch))

    # Información financiera
    elements.append(Paragraph("INFORMACIÓN FINANCIERA", styles['Heading2']))
    financiera_data = [
        ['Concepto', 'Valor'],
        ['Ingresos Mensuales', f"${datos_financieros['ingresos']:,.0f}"],
        ['Arriendo', f"${datos_financieros['arriendo']:,.0f}"],
        ['Servicios', f"${datos_financieros['servicios']:,.0f}"],
        ['Préstamos Personales', f"${datos_financieros['prestamos_personales']:,.0f}"],
        ['Score Datacrédito', f"{datos_financieros['score_datacredito']}"],
        ['Deudas Datacrédito', f"${datos_financieros['total_deudas_datacredito']:,.0f}"],
        ['Cuota Datacrédito', f"${datos_financieros['cuota_datacredito']:,.0f}"],
        ['Cuota Credisonar', f"${datos_financieros['cuota_credisonar']:,.0f}"],
        ['Total Egresos', f"${datos_financieros['total_egresos']:,.0f}"],
        ['Capacidad Disponible', f"${datos_financieros['capacidad_disponible']:,.0f}"]
    ]
    financiera_table = Table(financiera_data, colWidths=[3*inch, 3*inch])
    financiera_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(financiera_table)
    elements.append(Spacer(1, 0.3*inch))

    # Resultado de la evaluación
    elements.append(Paragraph("RESULTADO DE LA EVALUACIÓN", styles['Heading2']))

    decision_color = colors.green if resultado_evaluacion['decision'] == 'APROBADO' else colors.red
    decision_data = [
        ['Decisión:', resultado_evaluacion['decision']],
        ['Probabilidad Buen Pagador:', f"{resultado_evaluacion['probabilidad']}%"],
        ['Monto Solicitado:', f"${resultado_evaluacion['monto_solicitado']:,.0f}"],
        ['Monto Aprobado:', f"${resultado_evaluacion['monto_aprobado']:,.0f}"],
        ['Plazo:', f"{resultado_evaluacion['plazo']} meses"],
        ['Cuota Mensual:', f"${resultado_evaluacion['cuota_mensual']:,.0f}"],
        ['Nivel de Riesgo:', resultado_evaluacion['nivel_riesgo']]
    ]
    decision_table = Table(decision_data, colWidths=[3*inch, 3*inch])
    decision_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('BACKGROUND', (1, 0), (1, 0), decision_color),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(decision_table)
    elements.append(Spacer(1, 0.3*inch))

    # Recomendación
    elements.append(Paragraph("RECOMENDACIÓN", styles['Heading2']))
    recomendacion = Paragraph(resultado_evaluacion['recomendacion'], styles['Normal'])
    elements.append(recomendacion)

    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Configuración de la aplicación
st.set_page_config(page_title="Sistema de Decisión de Crédito", page_icon="💰", layout="centered")

# CSS personalizado para ampliar el contenedor y estandarizar textos
st.markdown("""
<style>
    /* Ampliar el contenedor principal en 20% */
    .main .block-container {
        max-width: 1000px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Estandarizar tamaños de texto */
    h1 {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }

    h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }

    h3 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        margin-top: 1rem !important;
        margin-bottom: 0.75rem !important;
    }

    /* Estandarizar métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
    }

    /* Espaciado consistente */
    .stMarkdown p {
        margin-bottom: 0.5rem !important;
    }

    /* Input labels más consistentes */
    .stNumberInput label, .stTextInput label, .stSelectbox label {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Sistema de Decisión de Crédito - Credisonar")
st.markdown("**Evaluación inteligente con Machine Learning**")

# Cargar modelo
try:
    modelo, scaler, feature_names = cargar_modelo()
except Exception as e:
    st.error(f"❌ Error cargando el modelo: {e}")
    st.stop()

st.markdown("---")

# ========== SECCIÓN 1: DATOS DEL CLIENTE ==========
st.header("👤 1. Datos del Cliente")

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    cedula = st.text_input("Cédula *", placeholder="Ingrese el número de cédula", key="cedula_input")

with col2:
    st.write("")  # Spacer for alignment
    buscar_btn = st.button("🔍 Buscar", type="primary")

with col3:
    st.write("")  # Spacer for alignment
    if st.button("🔄 Nueva Consulta", type="secondary"):
        # Limpiar todos los datos de la sesión
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

if buscar_btn and cedula:
    with st.spinner("Buscando cliente..."):
        cliente = buscar_cliente(cedula)
        if cliente:
            st.session_state['cliente'] = cliente
            st.success(f"✅ Cliente encontrado: {cliente['nombre']}")
        else:
            st.warning("⚠️ Cliente no encontrado. Ingrese los datos manualmente.")
            st.session_state['cliente'] = None

# Mostrar datos del cliente si existe
if 'cliente' in st.session_state and st.session_state['cliente']:
    cliente = st.session_state['cliente']

    st.markdown("### 📋 Información del Cliente")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.text_input("Nombre Completo", value=cliente['nombre'], disabled=True)
    with col_b:
        st.text_input("Cédula", value=cliente['cedula'], disabled=True)
    with col_c:
        fecha_nac_str = cliente['fecha_nacimiento'].strftime('%d/%m/%Y') if pd.notna(cliente['fecha_nacimiento']) else 'N/A'
        st.text_input("Fecha de Nacimiento", value=fecha_nac_str, disabled=True)

    col_d, col_e, col_f = st.columns(3)

    with col_d:
        st.text_input("Teléfono", value=cliente['telefono'], disabled=True)
    with col_e:
        st.text_input("Correo", value=cliente['correo'], disabled=True)
    with col_f:
        fecha_update_str = cliente['fecha_ultima_asesoria'].strftime('%d/%m/%Y') if cliente['fecha_ultima_asesoria'] and pd.notna(cliente['fecha_ultima_asesoria']) else 'N/A'
        st.text_input("Fecha de Update", value=fecha_update_str, disabled=True)

    st.text_input("Dirección", value=cliente['direccion'], disabled=True)

    # Historia en Credisonar
    st.markdown("### 📚 Historia en Credisonar")

    if len(cliente['historial_prestamos']) > 0:
        # Formatear datos para mostrar
        df_display = cliente['historial_prestamos'].copy()

        # Formatear pagaré como YYYY-#####
        df_display['pagare'] = df_display['pagare'].apply(
            lambda x: f"{str(x)[:4]}-{str(x)[4:]}" if len(str(x)) > 4 else str(x)
        )

        df_display['fecha_desembolso'] = pd.to_datetime(df_display['fecha_desembolso']).dt.strftime('%d/%m/%Y')
        df_display['fecha_ultimo_pago'] = pd.to_datetime(df_display['fecha_ultimo_pago'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_display['fecha_ultimo_pago'] = df_display['fecha_ultimo_pago'].fillna('N/A')
        df_display['monto_aprobado'] = df_display['monto_aprobado'].apply(lambda x: f"${x:,.0f}")
        df_display['valor_cuota'] = df_display['valor_cuota'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")

        # Renombrar columnas para mostrar
        df_display = df_display.rename(columns={
            'pagare': 'Pagaré',
            'fecha_desembolso': 'Fecha Desembolso',
            'fecha_ultimo_pago': 'Último Pago',
            'monto_aprobado': 'Monto Aprobado',
            'valor_cuota': 'Cuota',
            'estado': 'Estado',
            'calificacion': 'Calificación'
        })

        # Mostrar tabla
        st.dataframe(
            df_display[['Pagaré', 'Fecha Desembolso', 'Último Pago', 'Monto Aprobado', 'Cuota', 'Estado', 'Calificación']],
            use_container_width=True,
            hide_index=True
        )

        # Mostrar resumen de historial
        if cliente['historial']['num_prestamos_historicos'] > 0:
            col_h1, col_h2, col_h3, col_h4 = st.columns(4)
            with col_h1:
                st.metric("Préstamos Totales", cliente['historial']['num_prestamos_historicos'])
            with col_h2:
                st.metric("Cancelados", cliente['historial']['prestamos_cancelados'])
            with col_h3:
                st.metric("Mora Máxima", f"{cliente['historial']['dias_mora_maximo']:.0f} días")
            with col_h4:
                st.metric("Calificación A", cliente['historial']['prestamos_calificacion_A'])

            # Alertas de riesgo
            if cliente['historial']['dias_mora_maximo'] > 90:
                st.error(f"🚨 ALERTA: Mora histórica de {cliente['historial']['dias_mora_maximo']:.0f} días")
            if cliente['historial']['prestamos_calificacion_E'] > 0:
                st.error(f"🚨 ALERTA: {cliente['historial']['prestamos_calificacion_E']} préstamo(s) en calificación E")
            if cliente['historial']['prestamos_en_juridica'] > 0:
                st.error(f"🚨 ALERTA: {cliente['historial']['prestamos_en_juridica']} préstamo(s) en proceso jurídico")
    else:
        st.info("ℹ️ Cliente nuevo - Sin historial previo en Credisonar")

elif 'cliente' in st.session_state and st.session_state['cliente'] is None:
    # Cliente nuevo - pedir datos básicos
    st.markdown("### 📝 Datos Básicos (Cliente Nuevo)")
    col_n1, col_n2, col_n3 = st.columns(3)
    with col_n1:
        nombre_nuevo = st.text_input("Nombre Completo *")
    with col_n2:
        telefono_nuevo = st.text_input("Teléfono *")
    with col_n3:
        direccion_nuevo = st.text_input("Dirección")

    col_n4, col_n5, col_n6 = st.columns(3)
    with col_n4:
        edad_nuevo = st.number_input("Edad *", min_value=18, max_value=100, value=30)
    with col_n5:
        sexo_nuevo = st.selectbox("Sexo *", ["Masculino", "Femenino"])
    with col_n6:
        estado_civil_nuevo = st.selectbox("Estado Civil *", ["Soltero", "Casado", "Viudo", "Divorciado"])

    # Guardar cliente nuevo en sesión
    if nombre_nuevo and telefono_nuevo:
        estado_civil_map = {"Soltero": 0, "Casado": 1, "Viudo": 2, "Divorciado": 3}
        st.session_state['cliente'] = {
            'cedula': cedula,
            'nombre': nombre_nuevo,
            'telefono': telefono_nuevo,
            'direccion': direccion_nuevo,
            'edad': edad_nuevo,
            'sexo': 1 if sexo_nuevo == "Masculino" else 0,
            'sexo_texto': sexo_nuevo[0],
            'estado_civil': estado_civil_map[estado_civil_nuevo],
            'estado_civil_texto': estado_civil_nuevo[0],
            'creditos_activos': {
                'creditos_vigentes': 0,
                'saldo_capital': 0,
                'cuota_mensual': 0,
                'monto_aprobado': 0,
                'calificaciones': '',
                'tiene_calificacion_E': False
            },
            'historial': {
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
        }

# ========== SECCIÓN 2: INFORMACIÓN ACTUAL ==========
if 'cliente' in st.session_state and st.session_state['cliente']:
    st.markdown("---")
    st.header("📊 2. Información Financiera Actual")
    st.caption("Datos al día de hoy")

    # Ingresos
    st.markdown("### 💰 Ingresos")
    sueldo_mensual = st.number_input(
        "Ingresos Mensuales Demostrables *",
        min_value=0,
        max_value=100000000,
        value=0,
        step=100000,
        help="Ingreso mensual total demostrable del cliente"
    )

    # Egresos
    st.markdown("### 💸 Egresos")
    col_e1, col_e2, col_e3 = st.columns(3)

    with col_e1:
        arriendo = st.number_input(
            "Arriendo *",
            min_value=0,
            max_value=50000000,
            value=0,
            step=50000,
            help="Valor mensual del arriendo"
        )

    with col_e2:
        servicios = st.number_input(
            "Servicios *",
            min_value=0,
            max_value=10000000,
            value=0,
            step=50000,
            help="Valor mensual de servicios públicos"
        )

    with col_e3:
        prestamos_personales = st.number_input(
            "Préstamos Personales *",
            min_value=0,
            max_value=50000000,
            value=0,
            step=50000,
            help="Cuota mensual de préstamos personales (sin Datacrédito)"
        )

    # Datacrédito
    st.markdown("### 📋 Datacrédito")
    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        score_datacredito = st.number_input(
            "Score *",
            min_value=0,
            max_value=950,
            value=0,
            help="Score actual reportado en Datacrédito"
        )

    with col_d2:
        total_deudas_datacredito = st.number_input(
            "Total Deudas *",
            min_value=0,
            max_value=500000000,
            value=0,
            step=100000,
            help="Suma total de deudas vigentes reportadas en Datacrédito"
        )

    with col_d3:
        valor_mensual_datacredito = st.number_input(
            "Cuota Mensual *",
            min_value=0,
            max_value=50000000,
            value=0,
            step=50000,
            help="Cuota mensual total reportada en Datacrédito"
        )

    # Credisonar - Datos automáticos de la BD
    st.markdown("### 🏦 Credisonar")

    # Obtener datos de créditos activos
    cliente = st.session_state['cliente']
    creditos_activos = cliente.get('creditos_activos', {})

    # VALIDACIÓN CRÍTICA: Si tiene calificación E, bloquear
    if creditos_activos.get('tiene_calificacion_E', False):
        st.error("🚨 **¡CLIENTE BLOQUEADO!** - NO PUEDE SOLICITAR OTRO CRÉDITO")
        st.error(f"**Motivo:** Tiene crédito(s) con calificación E (Muy Mala) en Credisonar")
        st.warning("El cliente debe regularizar sus créditos actuales antes de solicitar uno nuevo.")
        st.stop()  # Bloquear el resto de la aplicación

    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)

    with col_c1:
        st.metric("Créditos Vigentes", creditos_activos.get('creditos_vigentes', 0))

    with col_c2:
        st.metric("Saldo Capital", f"${creditos_activos.get('saldo_capital', 0):,.0f}")

    with col_c3:
        calificaciones = creditos_activos.get('calificaciones', 'N/A')
        if calificaciones == '':
            calificaciones = 'N/A'
        st.metric("Calificación", calificaciones)

    with col_c4:
        st.metric("Monto Aprobado", f"${creditos_activos.get('monto_aprobado', 0):,.0f}")

    with col_c5:
        cuota_mensual_credisonar = creditos_activos.get('cuota_mensual', 0)
        st.metric("Cuota Mensual", f"${cuota_mensual_credisonar:,.0f}")

    # Resumen
    total_egresos = arriendo + servicios + prestamos_personales
    total_egresos_completo = total_egresos + valor_mensual_datacredito + cuota_mensual_credisonar

    st.markdown("---")
    st.markdown("### 📊 Resumen Financiero")
    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        st.metric("Total Ingresos", f"${sueldo_mensual:,.0f}")

    with col_s2:
        st.metric("Total Egresos", f"${total_egresos_completo:,.0f}")

    with col_s3:
        capacidad_disponible = sueldo_mensual - total_egresos_completo
        st.metric(
            "Capacidad Disponible",
            f"${capacidad_disponible:,.0f}",
            delta="Positiva" if capacidad_disponible > 0 else "Negativa",
            delta_color="normal" if capacidad_disponible > 0 else "inverse"
        )

    # ========== SECCIÓN 3: INFORMACIÓN DEL NUEVO CRÉDITO ==========
    st.markdown("---")
    st.header("💵 3. Información del Nuevo Crédito")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        monto_solicitado = st.number_input(
            "Monto Solicitado *",
            min_value=100000,
            max_value=50000000,
            value=3000000,
            step=100000,
            help="Monto que el cliente está solicitando"
        )

    with col_c2:
        plazo = st.selectbox(
            "Plazo (meses) *",
            [6, 12, 18, 24, 36, 48],
            index=2,
            help="Plazo en meses para pagar el crédito"
        )

    # ========== BOTÓN DE EVALUACIÓN ==========
    st.markdown("---")

    # Validar campos obligatorios
    campos_vacios = []
    if sueldo_mensual == 0:
        campos_vacios.append("Ingresos Mensuales Demostrables")
    if score_datacredito == 0:
        campos_vacios.append("Score Datacrédito")
    if monto_solicitado == 0:
        campos_vacios.append("Monto Solicitado")

    if campos_vacios:
        st.warning(f"⚠️ Por favor complete los siguientes campos obligatorios: {', '.join(campos_vacios)}")

    evaluar_btn = st.button("🔮 EVALUAR SOLICITUD", type="primary", use_container_width=True, disabled=len(campos_vacios) > 0)

    if evaluar_btn:
        with st.spinner("Analizando solicitud..."):
            cliente = st.session_state['cliente']

            # Combinar todos los datos
            datos_completos = cliente['historial'].copy()
            datos_completos['edad'] = cliente['edad']
            datos_completos['sexo'] = cliente['sexo']
            datos_completos['estado_civil'] = cliente['estado_civil']
            datos_completos['monto_solicitado'] = monto_solicitado
            datos_completos['plazo'] = plazo
            datos_completos['score_datacredito_historico'] = score_datacredito
            datos_completos['sueldo_mensual'] = sueldo_mensual
            datos_completos['total_egresos'] = total_egresos
            datos_completos['capacidad_pago'] = sueldo_mensual - total_egresos - valor_mensual_datacredito
            datos_completos['ratio_ingresos_egresos'] = total_egresos / sueldo_mensual if sueldo_mensual > 0 else 0

            # Hacer predicción
            probabilidad, decision = predecir_credito(datos_completos, modelo, scaler, feature_names)

            # Calcular monto sugerido
            monto_sugerido = calcular_monto_sugerido(
                probabilidad,
                monto_solicitado,
                plazo,
                sueldo_mensual,
                total_deudas_datacredito,
                valor_mensual_datacredito
            )

            # Calcular cuotas (3% mensual)
            tasa_mensual = 0.03
            cuota_solicitado = (monto_solicitado * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo)) if plazo > 0 else 0
            cuota_sugerido = (monto_sugerido * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo)) if plazo > 0 and monto_sugerido > 0 else 0
            capacidad = datos_completos['capacidad_pago']

            # ========== VALIDACIONES SEGÚN BUENAS PRÁCTICAS FINANCIERAS COLOMBIA ==========
            rechazo_automatico = False
            razones_rechazo = []
            nivel_riesgo = ""

            # Calcular ratio deuda/ingreso (según estándares colombianos)
            deuda_total_mensual = total_egresos + valor_mensual_datacredito + cuota_sugerido
            ratio_deuda_ingreso = (deuda_total_mensual / sueldo_mensual * 100) if sueldo_mensual > 0 else 100

            # 1. RECHAZOS AUTOMÁTICOS (según mejores prácticas Colombia)

            # Score Datacrédito < 500 = MUY RIESGOSO
            if score_datacredito < 500:
                rechazo_automatico = True
                razones_rechazo.append(f"Score Datacrédito muy bajo ({score_datacredito} < 500)")

            # Ratio deuda/ingreso > 50% = SOBREENDEUDADO
            if ratio_deuda_ingreso > 50:
                rechazo_automatico = True
                razones_rechazo.append(f"Ratio deuda/ingreso crítico ({ratio_deuda_ingreso:.1f}% > 50%)")

            # Capacidad de pago negativa o cero
            if capacidad <= 0:
                rechazo_automatico = True
                razones_rechazo.append("Sin capacidad de pago disponible")

            # Mora histórica > 30 días (estándar colombiano)
            if cliente['historial']['dias_mora_maximo'] > 30:
                rechazo_automatico = True
                razones_rechazo.append(f"Mora histórica alta ({cliente['historial']['dias_mora_maximo']:.0f} días > 30)")

            # Préstamos en jurídica
            if cliente['historial']['prestamos_en_juridica'] > 0:
                rechazo_automatico = True
                razones_rechazo.append(f"{cliente['historial']['prestamos_en_juridica']} préstamo(s) en cobro jurídico")

            # Calificación E en Datacrédito/Credisonar
            if cliente['historial']['prestamos_calificacion_E'] > 0:
                rechazo_automatico = True
                razones_rechazo.append(f"{cliente['historial']['prestamos_calificacion_E']} préstamo(s) en calificación E (muy mala)")

            # 2. DETERMINAR NIVEL DE RIESGO
            if not rechazo_automatico:
                if score_datacredito >= 700 and ratio_deuda_ingreso <= 35:
                    nivel_riesgo = "BAJO"  # Cliente ideal
                elif score_datacredito >= 700 and ratio_deuda_ingreso <= 40:
                    nivel_riesgo = "MEDIO-BAJO"  # Buen score pero cerca del límite
                elif score_datacredito >= 500 and ratio_deuda_ingreso <= 40:
                    nivel_riesgo = "MEDIO"  # Requiere precaución
                else:
                    nivel_riesgo = "ALTO"  # Zona peligrosa

            # Si hay rechazo automático, forzar decisión
            if rechazo_automatico:
                decision = 0
                monto_sugerido = 0

            # ========== SECCIÓN 4: RESULTADO ==========
            st.markdown("---")
            st.header("📊 4. Resultado de la Evaluación")

            col_r1, col_r2, col_r3 = st.columns(3)

            with col_r1:
                if rechazo_automatico:
                    st.error("### ❌ RECHAZADO")
                    st.caption("⚠️ No cumple criterios Colombia")
                elif decision == 1:
                    if nivel_riesgo == "BAJO":
                        st.success("### ✅ APROBADO")
                        st.caption(f"🟢 Riesgo {nivel_riesgo}")
                    else:
                        st.warning("### ⚠️ APROBADO")
                        st.caption(f"🟡 Riesgo {nivel_riesgo}")
                else:
                    st.error("### ❌ RECHAZADO")
                    st.caption("ML: Alto riesgo crediticio")

            with col_r2:
                st.metric(
                    "Probabilidad de Buen Pagador",
                    f"{probabilidad*100:.1f}%",
                    delta=f"{'Alta' if probabilidad >= 0.7 else 'Media' if probabilidad >= 0.4 else 'Baja'} confiabilidad"
                )

            with col_r3:
                st.metric(
                    "Monto Aprobado",
                    f"${monto_sugerido:,.0f}",
                    delta=f"{(monto_sugerido/monto_solicitado*100):.0f}% de lo solicitado" if monto_solicitado > 0 else ""
                )

            # ========== SECCIÓN 5: RECOMENDACIÓN Y CUOTA ==========
            st.markdown("---")
            st.header("💡 5. Recomendación y Cuota Aproximada")

            # Cuadro de cuotas y análisis financiero
            st.markdown("### 💰 Análisis Financiero según Estándares Colombia")

            col_q1, col_q2, col_q3, col_q4 = st.columns(4)

            with col_q1:
                st.metric("Cuota Propuesta", f"${cuota_sugerido:,.0f}/mes")

            with col_q2:
                st.metric("Capacidad de Pago", f"${capacidad:,.0f}/mes")

            with col_q3:
                # Determinar color según ratio
                if ratio_deuda_ingreso <= 30:
                    delta_color = "normal"  # Verde
                    nivel_endeuda = "IDEAL ✅"
                elif ratio_deuda_ingreso <= 40:
                    delta_color = "off"  # Amarillo
                    nivel_endeuda = "LÍMITE ⚠️"
                else:
                    delta_color = "inverse"  # Rojo
                    nivel_endeuda = "CRÍTICO ❌"

                st.metric(
                    "Ratio Deuda/Ingreso",
                    f"{ratio_deuda_ingreso:.1f}%",
                    delta=nivel_endeuda,
                    delta_color=delta_color
                )

            with col_q4:
                st.metric("Score Datacrédito", score_datacredito)

            # Indicador según estándares colombianos
            st.markdown("")
            if ratio_deuda_ingreso <= 30:
                st.success(f"✅ **ENDEUDAMIENTO IDEAL** (0-30%): Bajo riesgo de sobreendeudamiento según estándares colombianos")
            elif ratio_deuda_ingreso <= 40:
                st.warning(f"⚠️ **UMBRAL PELIGROSO** (31-40%): En el límite aceptable. Requiere ajustes para volver al rango ideal")
            elif ratio_deuda_ingreso <= 50:
                st.error(f"❌ **ZONA CRÍTICA** (41-50%): Alto riesgo de iliquidez que compromete la salud financiera")
            else:
                st.error(f"🚨 **SOBREENDEUDADO** (>50%): Cliente NO puede asumir más deuda. Riesgo extremo de mora")

            st.markdown("")

            # Recomendación final según estándares Colombia
            if rechazo_automatico:
                st.error(f"""
                ### ❌ RECOMENDACIÓN: RECHAZAR AUTOMÁTICAMENTE

                **❌ NO CUMPLE con criterios mínimos de buenas prácticas financieras Colombia:**

                {chr(10).join([f"- {razon}" for razon in razones_rechazo])}

                **Análisis Financiero:**
                - Score Datacrédito: {score_datacredito} {"✅" if score_datacredito >= 700 else "⚠️" if score_datacredito >= 500 else "❌"}
                - Ratio deuda/ingreso: {ratio_deuda_ingreso:.1f}% {"✅" if ratio_deuda_ingreso <= 35 else "⚠️" if ratio_deuda_ingreso <= 50 else "❌"}
                - Ingreso mensual: ${sueldo_mensual:,.0f}
                - Deuda total mensual: ${deuda_total_mensual:,.0f}
                - Capacidad disponible: ${capacidad:,.0f}

                **🚨 APROBAR este crédito violaría las buenas prácticas financieras y llevaría al cliente a sobreendeudamiento.**

                **Recomendaciones al cliente:**
                - Reducir gastos o liquidar deudas actuales
                - Aumentar ingresos
                - Mejorar score Datacrédito pagando a tiempo
                - Re-evaluar en 6-12 meses
                """)
            elif nivel_riesgo == "BAJO":
                st.success(f"""
                ### ✅ RECOMENDACIÓN: APROBAR

                **✅ Cliente IDEAL según estándares Colombia:**

                - **Monto aprobado:** ${monto_sugerido:,.0f}
                - **Plazo:** {plazo} meses
                - **Cuota mensual:** ${cuota_sugerido:,.0f}
                - **Score Datacrédito:** {score_datacredito} (Excelente ≥700)
                - **Ratio deuda/ingreso:** {ratio_deuda_ingreso:.1f}% (Ideal ≤35%)
                - **Probabilidad ML:** {probabilidad*100:.1f}%

                **✅ Cliente presenta:**
                - Score crediticio EXCELENTE
                - Endeudamiento en rango IDEAL
                - Capacidad de pago SUFICIENTE
                - Historial crediticio POSITIVO

                **👍 APROBAR sin requisitos adicionales. Cliente de bajo riesgo.**
                """)
            elif nivel_riesgo in ["MEDIO-BAJO", "MEDIO"]:
                st.warning(f"""
                ### ⚠️ RECOMENDACIÓN: APROBAR CON PRECAUCIÓN

                **⚠️ Cliente en zona de precaución:**

                - **Monto aprobado:** ${monto_sugerido:,.0f}
                - **Plazo:** {plazo} meses
                - **Cuota mensual:** ${cuota_sugerido:,.0f}
                - **Score Datacrédito:** {score_datacredito} {"(Bueno 700-799)" if score_datacredito >= 700 else "(Promedio 500-699)"}
                - **Ratio deuda/ingreso:** {ratio_deuda_ingreso:.1f}% {"(Límite 36-40%)" if ratio_deuda_ingreso > 35 else "(Aceptable <35%)"}
                - **Probabilidad ML:** {probabilidad*100:.1f}%

                **⚠️ Medidas de mitigación requeridas:**
                - Solicitar **garantías adicionales** (hipoteca, prenda)
                - Evaluar posibilidad de **codeudor** con buen perfil
                - Considerar **reducir monto** o **extender plazo** para bajar cuota
                - Seguimiento mensual durante primeros 6 meses

                **👍 APROBAR condicionado a requisitos adicionales.**
                """)
            else:
                st.error(f"""
                ### ❌ RECOMENDACIÓN: RECHAZAR

                **❌ Alto riesgo crediticio:**

                - **Score Datacrédito:** {score_datacredito}
                - **Ratio deuda/ingreso:** {ratio_deuda_ingreso:.1f}%
                - **Probabilidad de mora:** {(1-probabilidad)*100:.1f}%

                El perfil del cliente presenta **alto riesgo** basado en:
                - Historial crediticio deficiente
                - Alta probabilidad de incumplimiento según modelo ML
                - Indicadores financieros en zona de riesgo

                **🚫 NO se recomienda aprobar el crédito en estas condiciones.**
                """)

            # Detalles adicionales
            with st.expander("📈 Ver Análisis Detallado"):
                col_d1, col_d2 = st.columns(2)

                with col_d1:
                    st.markdown("**💰 Capacidad Financiera:**")
                    st.write(f"- Ingreso mensual: ${sueldo_mensual:,.0f}")
                    st.write(f"- Egresos fijos: ${total_egresos:,.0f}")
                    st.write(f"- Deudas Datacrédito: ${valor_mensual_datacredito:,.0f}")
                    st.write(f"- **Disponible: ${capacidad:,.0f}**")
                    st.write(f"- Ratio deuda/ingreso: {(total_egresos+valor_mensual_datacredito)/sueldo_mensual*100:.1f}%")

                with col_d2:
                    st.markdown("**📊 Información Datacrédito:**")
                    st.write(f"- Score actual: {score_datacredito}")
                    st.write(f"- Total deudas: ${total_deudas_datacredito:,.0f}")
                    st.write(f"- Cuota mensual: ${valor_mensual_datacredito:,.0f}")

                    if cliente['historial']['num_prestamos_historicos'] > 0:
                        st.markdown("**📜 Historial Credisonar:**")
                        st.write(f"- Préstamos históricos: {cliente['historial']['num_prestamos_historicos']}")
                        st.write(f"- Tasa cancelación: {cliente['historial']['ratio_cancelacion']*100:.0f}%")
                        st.write(f"- Mora máxima: {cliente['historial']['dias_mora_maximo']:.0f} días")

            # Preparar datos para PDF
            resultado_evaluacion = {
                'decision': 'APROBADO' if decision == 1 and not rechazo_automatico else 'RECHAZADO',
                'probabilidad': round(probabilidad * 100, 1),
                'monto_solicitado': monto_solicitado,
                'monto_aprobado': monto_sugerido,
                'plazo': plazo,
                'cuota_mensual': cuota_sugerido,
                'nivel_riesgo': nivel_riesgo if not rechazo_automatico else 'CRÍTICO',
                'recomendacion': f"Cliente {'APROBADO' if decision == 1 and not rechazo_automatico else 'RECHAZADO'} con nivel de riesgo {nivel_riesgo if not rechazo_automatico else 'CRÍTICO'}. Ratio deuda/ingreso: {ratio_deuda_ingreso:.1f}%"
            }
            datos_financieros = {
                'ingresos': sueldo_mensual,
                'arriendo': arriendo,
                'servicios': servicios,
                'prestamos_personales': prestamos_personales,
                'score_datacredito': score_datacredito,
                'total_deudas_datacredito': total_deudas_datacredito,
                'cuota_datacredito': valor_mensual_datacredito,
                'cuota_credisonar': cuota_mensual_credisonar,
                'total_egresos': total_egresos_completo,
                'capacidad_disponible': capacidad_disponible
            }

            # Generar PDF automáticamente
            st.markdown("---")
            st.markdown("### 📄 Descargar Evaluación")
            pdf_buffer = generar_pdf(cliente, datos_financieros, resultado_evaluacion)
            fecha_nombre = datetime.now().strftime("%Y%m%d_%H%M%S")

            st.download_button(
                label="⬇️ Descargar PDF de la Evaluación",
                data=pdf_buffer,
                file_name=f"Evaluacion_Credito_{cliente['cedula']}_{fecha_nombre}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

else:
    st.info("👆 Por favor ingrese una cédula y busque el cliente para comenzar la evaluación.")

# IMPORTANTE: En Streamlit Cloud, el código debe ejecutarse directamente
# NO dentro de if __name__ == "__main__": porque Streamlit no lo ejecuta
