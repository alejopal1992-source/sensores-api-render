# src/entrenar_modelo.py
# -*- coding: utf-8 -*-
"""Paso 2: Entrenamiento de modelo base (clasificación binaria de fallas)."""
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

root = Path(__file__).resolve().parents[1]
df = pd.read_csv(root / "data" / "datos_sensor.csv")

X = df[['temperatura', 'vibracion']]
y = df['retraso']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

modelo = RandomForestClassifier(random_state=42)
modelo.fit(X_train, y_train)

acc = accuracy_score(y_test, modelo.predict(X_test))
print(f"Precisión holdout: {acc:.3f}")

(root / "models").mkdir(parents=True, exist_ok=True)
joblib.dump(modelo, root / "models" / "modelo_sensores.pkl")
print("OK -> models/modelo_sensores.pkl")
