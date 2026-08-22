# src/generar_datos.py
# -*- coding: utf-8 -*-
"""Paso 1: Simulación de datos de sensores industriales (temperatura, vibración, falla)."""
from pathlib import Path
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]

np.random.seed(42)

# Generar datos normales de funcionamiento
normal = pd.DataFrame({
    'temperatura': np.random.normal(loc=70, scale=5, size=1000),
    'vibracion': np.random.normal(loc=0.5, scale=0.1, size=1000),
    'retraso': 0  # sin falla
})

# Generar datos con falla (deriva simulada)
falla = pd.DataFrame({
    'temperatura': np.random.normal(loc=85, scale=5, size=200),
    'vibracion': np.random.normal(loc=0.9, scale=0.1, size=200),
    'retraso': 1  # falla detectada
})

# Dataset completo
df = pd.concat([normal, falla]).sample(frac=1).reset_index(drop=True)

(root / "data").mkdir(parents=True, exist_ok=True)
out_csv = root / "data" / "datos_sensor.csv"
df.to_csv(out_csv, index=False)
print(f"OK -> {out_csv}")
