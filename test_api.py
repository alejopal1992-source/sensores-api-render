# test_api.py
# -*- coding: utf-8 -*-
"""
Script de prueba end-to-end para la API de sensores.

Uso:
    python test_api.py                              # prueba http://localhost:8000
    python test_api.py https://sensores-api-XXXX.onrender.com
"""
import sys
import requests

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"

SEP = "─" * 50
ok_count = 0
fail_count = 0


def check(n, titulo, method, path, **kwargs):
    global ok_count, fail_count
    print(SEP)
    print(f"{n}. {titulo}")
    try:
        resp = requests.request(method, f"{BASE_URL}{path}", timeout=30, **kwargs)
        print(f"   Status: {resp.status_code}")
        try:
            print(f"   Body:   {resp.json()}")
        except ValueError:
            print(f"   Body:   {resp.text[:200]}")
        if resp.status_code == 200:
            ok_count += 1
        else:
            fail_count += 1
        return resp
    except requests.RequestException as e:
        print(f"   ERROR: {e}")
        fail_count += 1
        return None


def main():
    print(f"🔗 Base URL: {BASE_URL}\n")

    check(1, "GET /health", "GET", "/health")

    check(2, "POST /predict  (caso normal: temp=70, vib=0.5)", "POST",
          "/predict", params={"temperatura": 70, "vibracion": 0.5})

    check(3, "POST /predict  (caso con falla: temp=90, vib=1.0)", "POST",
          "/predict", params={"temperatura": 90, "vibracion": 1.0})

    check(4, "POST /monitor  (batch simulado)", "POST", "/monitor",
          params={"size": 200, "t_mean": 72, "t_std": 5,
                  "v_mean": 0.52, "v_std": 0.1})

    check(5, "GET /docs", "GET", "/docs")

    print(SEP)
    if fail_count == 0:
        print("✅ Todos los tests pasaron correctamente.")
    else:
        print(f"❌ {fail_count} test(s) fallaron, {ok_count} OK.")
        sys.exit(1)


if __name__ == "__main__":
    main()
