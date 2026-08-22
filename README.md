# Monitoreo y Despliegue de Sensores Industriales — IA en la Nube

Proyecto que simula un entorno de mantenimiento predictivo: genera datos sintéticos de
sensores industriales (temperatura, vibración), entrena un modelo de clasificación binaria
para detectar fallas, lo expone como API REST con FastAPI y lo despliega en la nube con
Docker + Render.

El repositorio contiene el trabajo de dos entregas del curso:

- **Semana 2** (`src/`) — monitoreo de deriva (drift) con `evidently`, API local con
  `/predecir_sensores`, `/monitor`, `/report`.
- **Semana 3** (raíz del proyecto) — API contenerizada con Docker, dashboard Gradio y
  despliegue continuo en Render: `/health`, `/predict`, `/monitor`, `/ui`, `/docs`.

## Estructura

```
.
├── data/                    # datos_sensor.csv (generado)
├── models/                  # modelo_sensores.pkl (generado)
├── reports/                 # reporte_drift.html (generado, Semana 2)
├── src/                     # Entrega Semana 2 (drift con evidently)
│   ├── generar_datos.py
│   ├── entrenar_modelo.py
│   ├── monitoreo_drift.py
│   └── app.py
├── main.py                  # API FastAPI + dashboard Gradio (Semana 3)
├── train_model.py           # Genera datos y entrena el modelo (Semana 3)
├── test_api.py              # Prueba local/remota de los endpoints
├── requirements.txt
├── Dockerfile                # Empaquetado para despliegue en Render
├── .dockerignore
├── .gitignore
└── README.md
```

## Semana 3 — Puesta en marcha local

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Entrenar el modelo (genera data/ y models/)

```bash
python train_model.py
```

### 3. Levantar la API

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger: http://localhost:8000/docs
- Dashboard Gradio: http://localhost:8000/ui

### 4. Probar los endpoints

```bash
python test_api.py
```

## Semana 3 — Docker

```bash
docker build -t sensores-api .
docker run -p 8000:10000 sensores-api
```

```bash
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/predict?temperatura=70&vibracion=0.5"
curl -X POST "http://localhost:8000/predict?temperatura=90&vibracion=1.0"
```

## Semana 3 — Despliegue en Render

Ver la guía detallada `guia_render_sensores.md` (o la sección "Desplegar en Render" del
documento del ejercicio): crear repo en GitHub, conectar en Render como Web Service tipo
Docker, plan Free, y verificar en `https://sensores-api-XXXX.onrender.com`.

## Semana 2 — Monitoreo de drift (src/)

```bash
python src/generar_datos.py
python src/entrenar_modelo.py
python src/monitoreo_drift.py                 # reporte HTML standalone
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

- `GET /health`
- `POST /predecir_sensores` — `{ "temperatura": 88, "vibracion": 0.95 }`
- `POST /monitor` — recalcula el drift con `evidently` y devuelve límites/alertas.
- `GET /report` — sirve el último HTML de Evidently generado por `/monitor`.

Reglas de alerta (`src/app.py`): drift de dataset si
`share_of_drifted_features >= 0.5`; alerta por variable si la media del batch actual
supera `ref_mean + k_sigma * ref_std`.
