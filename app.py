# src/app.py
# -*- coding: utf-8 -*-
"""Paso 4: API de predicción y monitoreo (mantenimiento predictivo, Semana 2)."""
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Evidently
from evidently import Report
from evidently.presets import DataDriftPreset

# ---------------------------
# Rutas base y artefactos
# ---------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "datos_sensor.csv"
MODEL_PATH = BASE_DIR / "models" / "modelo_sensores.pkl"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_HTML = REPORTS_DIR / "reporte_drift.html"

# ---------------------------
# Crear app
# ---------------------------
app = FastAPI(title="API Predicción y Monitoreo (Semana 2)", version="2.0.0")

# ---------------------------
# Carga de modelo
# ---------------------------
if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el modelo en {MODEL_PATH}. "
        f"Ejecuta primero el entrenamiento (src/entrenar_modelo.py)."
    )
modelo = joblib.load(MODEL_PATH)


# ---------------------------
# Schemas (Pydantic)
# ---------------------------
class EntradaSensor(BaseModel):
    """Entrada para predicción con el modelo de sensores (Semana 2)."""
    temperatura: float = Field(..., description="Temperatura medida")
    vibracion: float = Field(..., description="Vibración medida")


class MonitorParams(BaseModel):
    """Parámetros para simular el batch actual en /monitor."""
    size: int = Field(200, ge=50, le=5000, description="Tamaño del batch actual")
    temp_mean: float = Field(90, description="Media simulada de temperatura del batch actual")
    temp_std: float = Field(5, ge=0.1, description="Desviación simulada de temperatura")
    vib_mean: float = Field(1.0, description="Media simulada de vibración del batch actual")
    vib_std: float = Field(0.1, ge=0.01, description="Desviación simulada de vibración")
    k_sigma: float = Field(
        2.0, ge=0.5, le=4.0,
        description="Multiplicador de sigma para límites (ref_mean + k*ref_std)"
    )


# ---------------------------
# Utils
# ---------------------------
def _build_reference_and_current(reference_frac: float = 0.7, seed: int = 42, params: MonitorParams | None = None):
    """Construye dataset de referencia y batch actual con parámetros controlables."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"No hay datos en {DATA_PATH}. Genera primero el CSV (src/generar_datos.py).")
    df = pd.read_csv(DATA_PATH)

    # referencia: igual que en entrenamiento (muestra aleatoria)
    ref = df.sample(frac=reference_frac, random_state=seed)[['temperatura', 'vibracion']]

    # batch actual parametrizable
    if params is None:
        params = MonitorParams()
    rng = np.random.default_rng(seed + 1)
    curr = pd.DataFrame({
        'temperatura': rng.normal(loc=params.temp_mean, scale=params.temp_std, size=params.size),
        'vibracion': rng.normal(loc=params.vib_mean, scale=params.vib_std, size=params.size)
    })
    return ref, curr, params


def _run_drift_report_and_summary(params: MonitorParams):
    """Corre Evidently, guarda HTML y devuelve resumen con límites k-sigma y alertas claras."""
    ref, curr, params = _build_reference_and_current(params=params)

    # 1) Evidently: se corre el reporte y se guarda el snapshot resultante
    drift_share_threshold = 0.5
    report = Report([DataDriftPreset(drift_share=drift_share_threshold)])
    snapshot = report.run(current_data=curr, reference_data=ref)
    snapshot.save_html(str(REPORT_HTML))

    # DriftedColumnsCount agrega cuántas/qué proporción de columnas presentan drift
    metrics = snapshot.dict()["metrics"]
    drift_count = next(m for m in metrics if m["metric_name"].startswith("DriftedColumnsCount"))
    n_drifted_features = drift_count["value"]["count"]
    share_of_drifted_features = drift_count["value"]["share"]
    dataset_drift = share_of_drifted_features >= drift_share_threshold

    # 2) Límites por k sigmas
    ref_temp_mean = float(ref['temperatura'].mean())
    ref_temp_std = float(ref['temperatura'].std())
    ref_vib_mean = float(ref['vibracion'].mean())
    ref_vib_std = float(ref['vibracion'].std())

    temp_upper = ref_temp_mean + params.k_sigma * ref_temp_std
    vib_upper = ref_vib_mean + params.k_sigma * ref_vib_std

    curr_temp_mean = float(curr['temperatura'].mean())
    curr_vib_mean = float(curr['vibracion'].mean())

    temp_alert = curr_temp_mean > temp_upper
    vib_alert = curr_vib_mean > vib_upper

    return {
        "dataset_drift": dataset_drift,
        "share_of_drifted_features": round(float(share_of_drifted_features), 4),
        "n_drifted_features": int(n_drifted_features),
        "limits": {
            "k_sigma": params.k_sigma,
            "temp": {
                "ref_mean": round(ref_temp_mean, 3),
                "ref_std": round(ref_temp_std, 3),
                "upper_limit": round(temp_upper, 3),
                "current_mean": round(curr_temp_mean, 3),
                "alert": temp_alert
            },
            "vibration": {
                "ref_mean": round(ref_vib_mean, 3),
                "ref_std": round(ref_vib_std, 3),
                "upper_limit": round(vib_upper, 3),
                "current_mean": round(curr_vib_mean, 3),
                "alert": vib_alert
            }
        },
        "report_path": str(REPORT_HTML)
    }


# ---------------------------
# Endpoints
# ---------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_exists": MODEL_PATH.exists(),
        "data_exists": DATA_PATH.exists(),
        "report_target": str(REPORT_HTML)
    }


@app.post("/predecir_sensores")
def predecir_sensores(entrada: EntradaSensor):
    """Predicción con el modelo de Semana 2 (features: temperatura, vibración)."""
    df = pd.DataFrame([entrada.model_dump()])[['temperatura', 'vibracion']]
    try:
        proba = float(modelo.predict_proba(df)[0][1])
        pred = int(proba >= 0.5)
        return {"probabilidad_evento": round(proba, 4), "prediccion": pred}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al predecir: {e}")


@app.post("/monitor")
def monitor(params: MonitorParams):
    """Ejecuta Evidently y devuelve un resumen con límites y alertas por variable."""
    try:
        return _run_drift_report_and_summary(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report")
def report_html():
    """Sirve el último reporte HTML generado por /monitor."""
    if not REPORT_HTML.exists():
        raise HTTPException(status_code=404, detail="No existe reporte. Ejecuta /monitor primero.")
    return FileResponse(path=str(REPORT_HTML), media_type="text/html", filename=REPORT_HTML.name)
