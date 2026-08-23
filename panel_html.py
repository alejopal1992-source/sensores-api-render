PANEL_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Panel de Predicción — Sensores Industriales</title>
<style>
  :root {
    --purple: #6C63FF;
    --purple-dark: #4B44C4;
    --green: #2ca02c;
    --amber: #e6a700;
    --red: #d62728;
    --bg: #eef0fb;
    --card: #ffffff;
    --text: #2b2b40;
    --muted: #6b6b80;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(180deg, #eef0fb 0%, #e4e8fb 100%);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    color: var(--text);
    padding: 24px;
  }
  .card {
    background: var(--card);
    border-radius: 22px;
    box-shadow: 0 12px 40px rgba(76, 68, 196, 0.18);
    padding: 32px 30px;
    width: 100%;
    max-width: 420px;
  }
  h1 {
    font-size: 1.28rem;
    text-align: center;
    margin: 0 0 4px;
    color: var(--text);
  }
  .subtitle {
    text-align: center;
    color: var(--muted);
    font-size: 0.86rem;
    margin: 0 0 26px;
  }
  .field { margin-bottom: 22px; }
  .field label {
    display: flex;
    justify-content: space-between;
    font-size: 0.88rem;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .field label span.val {
    color: var(--purple-dark);
    font-weight: 700;
  }
  input[type="range"] {
    width: 100%;
    -webkit-appearance: none;
    height: 6px;
    border-radius: 4px;
    background: #e2e2f5;
    outline: none;
  }
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--purple);
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(76, 68, 196, 0.4);
  }
  input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--purple);
    cursor: pointer;
    border: none;
  }
  button {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--purple), var(--purple-dark));
    color: #fff;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.08s ease, opacity 0.2s ease;
  }
  button:active { transform: scale(0.98); }
  button:disabled { opacity: 0.6; cursor: default; }
  .result {
    margin-top: 28px;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 190px;
    justify-content: center;
  }
  .gauge-wrap { position: relative; width: 170px; height: 170px; }
  .gauge-wrap svg { transform: rotate(-90deg); }
  .gauge-pct {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .gauge-pct .num { font-size: 1.7rem; font-weight: 800; }
  .gauge-pct .lbl { font-size: 0.68rem; color: var(--muted); margin-top: 2px; }
  .status-msg {
    margin-top: 14px;
    font-size: 0.92rem;
    font-weight: 600;
    text-align: center;
    padding: 8px 16px;
    border-radius: 10px;
  }
  .status-ok { color: #1e7d1e; background: #e8f5e9; }
  .status-warn { color: #b23a00; background: #fdecea; }
  .error-box {
    margin-top: 18px;
    font-size: 0.85rem;
    color: #a4290b;
    background: #fdecea;
    border: 1px solid #f3b7ab;
    border-radius: 10px;
    padding: 10px 14px;
    text-align: center;
    display: none;
  }
  .placeholder-msg { color: var(--muted); font-size: 0.85rem; text-align: center; }
  .footer-note {
    margin-top: 22px;
    font-size: 0.72rem;
    color: var(--muted);
    text-align: center;
    line-height: 1.4;
  }
</style>
</head>
<body>
  <div class="card">
    <h1>&#128736; &iquest;Ocurrir&aacute; una falla en el sensor?</h1>
    <p class="subtitle">Ajusta la lectura del sensor y consulta la predicci&oacute;n del modelo en tiempo real.</p>

    <div class="field">
      <label>Temperatura (&deg;C) <span class="val" id="tempVal">70.0</span></label>
      <input type="range" id="temp" min="40" max="110" step="0.5" value="70">
    </div>

    <div class="field">
      <label>Vibraci&oacute;n <span class="val" id="vibVal">0.50</span></label>
      <input type="range" id="vib" min="0" max="1.5" step="0.01" value="0.5">
    </div>

    <button id="btn" onclick="predecir()">Consultar predicci&oacute;n</button>

    <div class="result" id="result">
      <p class="placeholder-msg">Presiona el bot&oacute;n para ver la probabilidad de falla.</p>
    </div>

    <div class="error-box" id="errorBox"></div>

    <p class="footer-note">Modelo RandomForestClassifier servido desde /predict.<br>Interfaz propia, adicional al dashboard Gradio (/ui).</p>
  </div>

<script>
  const tempInput = document.getElementById('temp');
  const vibInput = document.getElementById('vib');
  const tempVal = document.getElementById('tempVal');
  const vibVal = document.getElementById('vibVal');
  const btn = document.getElementById('btn');
  const resultDiv = document.getElementById('result');
  const errorBox = document.getElementById('errorBox');

  tempInput.addEventListener('input', () => tempVal.textContent = parseFloat(tempInput.value).toFixed(1));
  vibInput.addEventListener('input', () => vibVal.textContent = parseFloat(vibInput.value).toFixed(2));

  function gaugeSVG(pct, color) {
    const r = 70, c = 2 * Math.PI * r;
    const offset = c - (pct / 100) * c;
    return `
      <div class="gauge-wrap">
        <svg width="170" height="170">
          <circle cx="85" cy="85" r="${r}" stroke="#e2e2f5" stroke-width="14" fill="none"/>
          <circle cx="85" cy="85" r="${r}" stroke="${color}" stroke-width="14" fill="none"
            stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${offset}"
            style="transition: stroke-dashoffset 0.5s ease, stroke 0.3s ease;"/>
        </svg>
        <div class="gauge-pct">
          <span class="num" style="color:${color}">${pct.toFixed(0)}%</span>
          <span class="lbl">prob. de falla</span>
        </div>
      </div>`;
  }

  async function predecir() {
    errorBox.style.display = 'none';
    btn.disabled = true;
    btn.textContent = 'Consultando...';
    const temperatura = parseFloat(tempInput.value);
    const vibracion = parseFloat(vibInput.value);
    try {
      const url = `/predict?temperatura=${temperatura}&vibracion=${vibracion}`;
      const resp = await fetch(url, { method: 'POST' });
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      const pct = data.prob_retraso * 100;
      const isFalla = data.prediccion === 1;
      const color = isFalla ? '#d62728' : '#2ca02c';
      resultDiv.innerHTML = gaugeSVG(pct, color);
      const msg = document.createElement('div');
      msg.className = 'status-msg ' + (isFalla ? 'status-warn' : 'status-ok');
      msg.textContent = isFalla ? '⚠️ Riesgo de falla — revisar sensor' : '✅ Operación normal';
      resultDiv.appendChild(msg);
    } catch (err) {
      errorBox.textContent = 'No se pudo contactar la API (' + err.message + '). Verifica que el servicio esté activo e intenta de nuevo.';
      errorBox.style.display = 'block';
      resultDiv.innerHTML = '<p class="placeholder-msg">Sin datos aún.</p>';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Consultar predicción';
    }
  }
</script>
</body>
</html>
"""
