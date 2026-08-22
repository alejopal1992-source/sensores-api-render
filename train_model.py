# train_model.py
# -*- coding: utf-8 -*-
"""
Semana 3 — Entrenamiento y serialización del modelo.

Genera datos sintéticos de sensores industriales (temperatura, vibración),
entrena un RandomForestClassifier que predice retrasos por falla, y guarda:
  - data/datos_sensor.csv
  - models/modelo_sensores.pkl

Este script lo ejecuta el Dockerfile durante el build (RUN python train_model.py),
por eso las rutas son relativas a la raíz del proyecto (WORKDIR /app).
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# 1) Generar datos simulados (temperatura, vibración, retraso)
np.random.seed(42)

normal = pd.DataFrame({
    'temperatura': np.random.normal(loc=70, scale=5, size=1000),
    'vibracion':   np.random.normal(loc=0.5, scale=0.1, size=1000),
    'retraso': 0
})
falla = pd.DataFrame({
    'temperatura': np.random.normal(loc=85, scale=5, size=200),
    'vibracion':   np.random.normal(loc=0.9, scale=0.1, size=200),
    'retraso': 1
})
df = pd.concat([normal, falla], ignore_index=True).sample(frac=1, random_state=42)

# Guardar CSV en data/
data_path = Path("data")
data_path.mkdir(parents=True, exist_ok=True)
csv_path = data_path / "datos_sensor.csv"
df.to_csv(csv_path, index=False)
print(f"OK -> {csv_path}")

# 2) Entrenar modelo
X = df[['temperatura', 'vibracion']]
y = df['retraso']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

modelo = RandomForestClassifier(random_state=42)
modelo.fit(X_train, y_train)

# 3) Precisión
acc = accuracy_score(y_test, modelo.predict(X_test))
print(f"Precisión holdout: {acc:.3f}")

# 4) Guardar modelo
models_path = Path("models")
models_path.mkdir(parents=True, exist_ok=True)
joblib.dump(modelo, models_path / "modelo_sensores.pkl")
print("Modelo guardado -> models/modelo_sensores.pkl")
