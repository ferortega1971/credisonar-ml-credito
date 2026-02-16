"""
API REST para Credit Scoring - Credisonar
Endpoints para evaluar solicitudes de crédito
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import pandas as pd
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.credit_model import CreditScoringModel
from src.data.data_processor import CreditDataProcessor

# Inicializar FastAPI
app = FastAPI(
    title="Credisonar Credit Scoring API",
    description="API para evaluación de riesgo crediticio",
    version="1.0.0"
)

# CORS - permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar modelo y procesador (en producción, cargar desde archivos)
modelo = None
procesador = None


# Modelos Pydantic para request/response
class ClienteInput(BaseModel):
    """Datos de entrada del cliente"""
    # Demográficos
    edad: int = Field(..., ge=18, le=100, description="Edad del cliente")
    genero: str = Field(..., description="M o F")
    estado_civil: str = Field(..., description="soltero, casado, divorciado, viudo")
    nivel_educacion: str = Field(..., description="primaria, secundaria, preparatoria, universitario, posgrado")
    ocupacion: str = Field(..., description="empleado, independiente, profesionista, comerciante, otro")
    antiguedad_trabajo_meses: int = Field(..., ge=0, description="Antigüedad en el trabajo actual (meses)")

    # Financieros
    ingreso_mensual: float = Field(..., gt=0, description="Ingreso mensual")
    monto_solicitado: float = Field(..., gt=0, description="Monto del préstamo solicitado")
    plazo_meses: int = Field(..., ge=1, le=60, description="Plazo del préstamo en meses")
    ratio_deuda_ingreso: float = Field(..., ge=0, le=1, description="Ratio deuda/ingreso actual")

    # Historial crediticio
    prestamos_anteriores: int = Field(0, ge=0, description="Número de préstamos anteriores")
    prestamos_pagados_completos: int = Field(0, ge=0, description="Préstamos pagados completos")
    dias_atraso_promedio: int = Field(0, ge=0, description="Días de atraso promedio")
    max_dias_atraso: int = Field(0, ge=0, description="Máximo días de atraso")
    pagos_puntuales_pct: float = Field(1.0, ge=0, le=1, description="% de pagos puntuales")

    # Comportamiento
    antiguedad_cliente_meses: int = Field(0, ge=0, description="Antigüedad como cliente")
    consultas_credito_ultimos_6m: int = Field(0, ge=0, description="Consultas de crédito últimos 6 meses")

    class Config:
        json_schema_extra = {
            "example": {
                "edad": 35,
                "genero": "M",
                "estado_civil": "casado",
                "nivel_educacion": "universitario",
                "ocupacion": "empleado",
                "antiguedad_trabajo_meses": 48,
                "ingreso_mensual": 25000,
                "monto_solicitado": 50000,
                "plazo_meses": 12,
                "ratio_deuda_ingreso": 0.35,
                "prestamos_anteriores": 3,
                "prestamos_pagados_completos": 2,
                "dias_atraso_promedio": 5,
                "max_dias_atraso": 30,
                "pagos_puntuales_pct": 0.85,
                "antiguedad_cliente_meses": 24,
                "consultas_credito_ultimos_6m": 2
            }
        }


class EvaluacionResponse(BaseModel):
    """Respuesta de la evaluación crediticia"""
    score: int = Field(..., description="Score crediticio (300-850)")
    probabilidad_default: float = Field(..., description="Probabilidad de no pagar")
    decision: str = Field(..., description="APROBAR, RECHAZAR, o REVISAR MANUAL")
    tasa_sugerida: float = Field(..., description="Tasa de interés sugerida (%)")
    monto_maximo_recomendado: Optional[float] = Field(None, description="Monto máximo recomendado")
    confianza: float = Field(..., description="Nivel de confianza (0-1)")
    explicacion: List[str] = Field(..., description="Factores que influyen")


@app.on_event("startup")
async def startup_event():
    """Carga el modelo al iniciar la API"""
    global modelo, procesador
    try:
        modelo = CreditScoringModel(model_type='xgboost')
        procesador = CreditDataProcessor()

        # Intentar cargar modelo pre-entrenado
        try:
            modelo.load("models/credit_model.pkl")
            procesador.load("models/data_processor.pkl")
            print("✅ Modelo y procesador cargados exitosamente")
        except FileNotFoundError:
            print("⚠️ Advertencia: Modelo no encontrado. Ejecutar entrenamiento primero.")

    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")


@app.get("/")
def read_root():
    """Endpoint raíz"""
    return {
        "nombre": "Credisonar Credit Scoring API",
        "version": "1.0.0",
        "endpoints": {
            "POST /evaluar": "Evaluar solicitud de crédito",
            "GET /health": "Estado de la API",
            "GET /docs": "Documentación"
        }
    }


@app.get("/health")
def health_check():
    """Estado de la API"""
    modelo_ok = modelo is not None and hasattr(modelo, 'model') and modelo.model is not None
    procesador_ok = procesador is not None

    return {
        "status": "healthy" if (modelo_ok and procesador_ok) else "unhealthy",
        "modelo_cargado": modelo_ok,
        "procesador_cargado": procesador_ok
    }


@app.post("/evaluar", response_model=EvaluacionResponse)
def evaluar_credito(cliente: ClienteInput):
    """Evalúa una solicitud de crédito"""
    if modelo is None or modelo.model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")

    try:
        # Convertir a DataFrame
        df = pd.DataFrame([cliente.dict()])

        # Preprocesar
        df_processed = procesador.preprocess(df, fit=False)
        X = procesador.scale_features(df_processed, fit=False)

        # Predecir
        resultado = modelo.predict_complete(X)[0]

        # Monto máximo
        if resultado['decision'] == 'APROBAR':
            monto_max = cliente.monto_solicitado
        elif resultado['decision'] == 'REVISAR MANUAL':
            monto_max = cliente.monto_solicitado * 0.7
        else:
            monto_max = 0.0

        # Explicación
        explicacion = []
        if cliente.pagos_puntuales_pct > 0.8:
            explicacion.append(f"✓ Buen historial ({cliente.pagos_puntuales_pct:.0%} puntualidad)")
        elif cliente.pagos_puntuales_pct < 0.6:
            explicacion.append(f"✗ Bajo historial ({cliente.pagos_puntuales_pct:.0%})")

        if cliente.ingreso_mensual > 20000:
            explicacion.append("✓ Ingreso estable")
        elif cliente.ingreso_mensual < 10000:
            explicacion.append("⚠ Ingreso bajo")

        if cliente.ratio_deuda_ingreso > 0.5:
            explicacion.append("⚠ Alto endeudamiento")

        if cliente.dias_atraso_promedio > 15:
            explicacion.append(f"✗ Atrasos ({cliente.dias_atraso_promedio} días)")

        return EvaluacionResponse(
            score=resultado['score'],
            probabilidad_default=resultado['probabilidad_default'],
            decision=resultado['decision'],
            tasa_sugerida=resultado['tasa_sugerida'],
            monto_maximo_recomendado=monto_max,
            confianza=resultado['confianza'],
            explicacion=explicacion if explicacion else ["Análisis estándar"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
