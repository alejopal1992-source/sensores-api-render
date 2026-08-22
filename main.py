# main.py
# -*- coding: utf-8 -*-
"""
Semana 3 — API de Predicción de Fallas Industriales + Dashboard Gradio.

Endpoints:
  GET  /health   -> estado del servicio
  POST /predict  -> predicción individual (temperatura, vibración)
  POST /monitor  -> detección de drift simple (regla ±k·sigma)
  GET  /ui       -> dashboard interactivo (Gradio)
  GET  /docs     -> documentación Swagger automática
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os, joblib, numpy as np, pandas as pd

# ---- Rutas base y archivos ----
BASE_DIR    = Path(__file__).resolve().parent
MODELS_DIR  = BASE_DIR / "models"
DATA_DIR    = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
for d in (MODELS_DIR, DATA_DIR, REPORTS_DIR):
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

CSV_PATH   = DATA_DIR / "datos_sensor.csv"
MODEL_PATH = MODELS_DIR / "modelo_sensores.pkl"

# Si no hay CSV, genera uno de respaldo
if not CSV_PATH.exists():
    rng = np.random.default_rng(42)
    normal = pd.DataFrame({
        "temperatura": rng.normal(70, 5, 300),
        "vibracion":   rng.normal(0.5, 0.1, 300),
        "retraso": 0,
    })
    falla = pd.DataFrame({
        "temperatura": rng.normal(85, 5, 60),
        "vibracion":   rng.normal(0.9, 0.1, 60),
        "retraso": 1,
    })
    df0 = pd.concat([normal, falla], ignore_index=True)
    df0.to_csv(CSV_PATH, index=False)

# ---- Modelo ----
if not MODEL_PATH.exists():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    df = pd.read_csv(CSV_PATH)
    X = df[["temperatura", "vibracion"]]
    y = df["retraso"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y)
    clf = RandomForestClassifier(random_state=42).fit(Xtr, ytr)
    joblib.dump(clf, MODEL_PATH)

modelo = joblib.load(MODEL_PATH)

# ---- FastAPI ----
app = FastAPI(
    title="API Sensores + Dashboard",
    description="API REST para predicción de fallas industriales",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_PATH.name,
            "csv": CSV_PATH.exists()}


@app.get("/debug/versions")
def debug_versions():
    """Endpoint temporal de diagnóstico: versiones instaladas y rutas registradas."""
    import importlib
    info = {}
    for pkg in ["fastapi", "starlette", "gradio", "gradio_client", "pydantic", "uvicorn"]:
        try:
            mod = importlib.import_module(pkg)
            info[pkg] = getattr(mod, "__version__", "unknown")
        except Exception as e:
            info[pkg] = f"ERROR: {e}"
    try:
        import evidently
        info["evidently"] = getattr(evidently, "__version__", "present (sin __version__)")
    except Exception as e:
        info["evidently"] = f"no instalado ({type(e).__name__}: {e})"
    try:
        import multipart
        info["multipart_file"] = getattr(multipart, "__file__", "?")
        info["multipart_has_submodule"] = hasattr(multipart, "multipart")
    except Exception as e:
        info["multipart_file"] = f"ERROR: {type(e).__name__}: {e}"
    routes = []
    for r in app.routes:
        routes.append({
            "path": getattr(r, "path", str(r)),
            "name": getattr(r, "name", None),
            "type": type(r).__name__,
        })
    info["routes"] = routes
    return info


@app.get("/debug/selftest")
def debug_selftest():
    """Llama a /ui/ dentro del propio proceso (sin red/proxy de por medio)."""
    from starlette.testclient import TestClient
    import os as _os
    result = {}
    try:
        with TestClient(app) as client:
            r = client.get("/ui/")
            result["internal_ui_status"] = r.status_code
            result["internal_ui_body_head"] = r.text[:200]
    except Exception as e:
        result["internal_ui_error"] = f"{type(e).__name__}: {e}"
    result["env_HOME"] = _os.environ.get("HOME")
    result["env_PORT"] = _os.environ.get("PORT")
    result["env_GRADIO_ROOT_PATH"] = _os.environ.get("GRADIO_ROOT_PATH")
    result["env_WEB_CONCURRENCY"] = _os.environ.get("WEB_CONCURRENCY")
    result["cwd"] = _os.getcwd()
    result["whoami_uid"] = _os.getuid()
    return result


@app.post("/predict")
def predict(temperatura: float, vibracion: float):
    X = pd.DataFrame([[temperatura, vibracion]],
                      columns=["temperatura", "vibracion"])
    proba = float(modelo.predict_proba(X)[0][1])
    pred = int(proba >= 0.5)
    return {"prediccion": pred, "prob_retraso": round(proba, 4)}


@app.post("/monitor")
def monitor(size: int, t_mean: float, t_std: float,
            v_mean: float, v_std: float):
    rng = np.random.default_rng(7)
    curr = pd.DataFrame({
        "temperatura": rng.normal(t_mean, t_std, size),
        "vibracion":   rng.normal(v_mean, v_std, size),
    })
    ref = pd.read_csv(CSV_PATH)[["temperatura", "vibracion"]]
    t_upper = ref["temperatura"].mean() + 2 * ref["temperatura"].std()
    v_upper = ref["vibracion"].mean() + 2 * ref["vibracion"].std()
    return {
        "limits": {"temp_upper": round(float(t_upper), 3),
                    "vib_upper":  round(float(v_upper), 3)},
        "current_means": {
            "temp": round(float(curr["temperatura"].mean()), 3),
            "vib":  round(float(curr["vibracion"].mean()), 3)},
        "alerts": {
            "temp": bool(curr["temperatura"].mean() > t_upper),
            "vib":  bool(curr["vibracion"].mean() > v_upper)},
    }


# ---------------------------------------------------------------
# Dashboard Gradio, montado en /ui
# ---------------------------------------------------------------
import gradio as gr
import plotly.graph_objects as go


def _gauge(proba: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(proba * 100, 1),
        number={"suffix": "%"},
        title={"text": "Probabilidad de falla"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#d62728" if proba >= 0.5 else "#2ca02c"},
            "steps": [
                {"range": [0, 50], "color": "#e8f5e9"},
                {"range": [50, 100], "color": "#fdecea"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 3},
                "thickness": 0.8,
                "value": 50,
            },
        },
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def predecir_ui(temperatura: float, vibracion: float):
    X = pd.DataFrame([[temperatura, vibracion]],
                      columns=["temperatura", "vibracion"])
    proba = float(modelo.predict_proba(X)[0][1])
    pred = "⚠️ FALLA PROBABLE" if proba >= 0.5 else "✅ Operación normal"
    return pred, _gauge(proba)


with gr.Blocks(title="Predicción de Fallas Industriales") as dashboard:
    gr.Markdown("## 🏭 Predicción de Fallas Industriales — Sensores")
    gr.Markdown(
        "Ingresa la lectura de un sensor para estimar la probabilidad de falla. "
        "Modelo: RandomForestClassifier entrenado con datos sintéticos "
        "(temperatura, vibración)."
    )
    with gr.Row():
        with gr.Column():
            temperatura_in = gr.Slider(40, 110, value=70, label="Temperatura (°C)")
            vibracion_in = gr.Slider(0.0, 1.5, value=0.5, step=0.01, label="Vibración")
            btn = gr.Button("Predecir", variant="primary")
        with gr.Column():
            resultado = gr.Textbox(label="Resultado")
            grafico = gr.Plot(label="Probabilidad de falla")

    # queue=False: evita el sistema de colas de Gradio (usa WebSocket) que
    # falla detrás del proxy de Render ("This application is currently busy").
    # Con queue=False cada clic es una petición HTTP normal, sin WebSocket.
    btn.click(predecir_ui, inputs=[temperatura_in, vibracion_in],
              outputs=[resultado, grafico], queue=False)

# IMPORTANTE: no configures la variable de entorno GRADIO_ROOT_PATH en Render
# con la URL completa (https://...) — rompe el enrutado de Gradio. Déjala sin
# definir; root_path="" (el valor por defecto aquí) funciona correctamente.
gr.mount_gradio_app(app, dashboard, path="/ui",
                     root_path=os.environ.get("GRADIO_ROOT_PATH", ""))
