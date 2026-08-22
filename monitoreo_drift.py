# src/monitoreo_drift.py
# -*- coding: utf-8 -*-
"""Paso 3: Monitoreo de deriva (drift) con la librería 'evidently'."""
import numpy as np
import pandas as pd
from pathlib import Path
from evidently import Report
from evidently.presets import DataDriftPreset

root = Path(__file__).resolve().parents[1]
df = pd.read_csv(root / "data" / "datos_sensor.csv")

# Referencia: el mismo split que en entrenamiento para simplificar
ref = df.sample(frac=0.7, random_state=42)[['temperatura', 'vibracion']]

# Simulación de un "nuevo batch" con valores desplazados (deriva)
curr = pd.DataFrame({
    'temperatura': np.random.normal(loc=90, scale=5, size=200),
    'vibracion': np.random.normal(loc=1.0, scale=0.1, size=200)
})

report = Report([DataDriftPreset()])
snapshot = report.run(current_data=curr, reference_data=ref)

(root / "reports").mkdir(parents=True, exist_ok=True)
out_html = root / "reports" / "reporte_drift.html"
snapshot.save_html(str(out_html))
print(f"OK -> {out_html}")
