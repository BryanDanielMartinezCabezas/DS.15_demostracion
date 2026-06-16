import pyotp
import requests
from datetime import datetime
from flask import (
    Flask, render_template_string, request,
    redirect, url_for, session, jsonify,
)

app = Flask(__name__)
app.secret_key = "demo-ds517-fixed-key"

USERNAME = "admin"
PASSWORD = "Segur1dad!"
TOTP_SECRET = "JBSWY3DPEHPK3PXP"

VICTIM_URL = "http://victim:8000"
SIEM_URL = "http://siem:5601"
DATABASE_URL = "http://database:5050"


def log_to_siem(event_type, message, severity="INFO"):
    try:
        requests.post(
            f"{SIEM_URL}/log",
            json={
                "source": "Admin-Console@admin(172.29.0.40)",
                "type": event_type,
                "message": message,
                "severity": severity,
            },
            timeout=3,
        )
    except Exception:
        pass


# ──────────────────────────────── HTML ────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Consola de Seguridad SUNIVER — DS5.17</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family:'Segoe UI',sans-serif;
    background:linear-gradient(135deg,#0d1117,#0d2137);
    min-height:100vh; display:flex; align-items:center; justify-content:center;
  }
  .card {
    background:#161b22; border:1px solid #30363d; border-radius:12px;
    padding:40px 36px; width:380px; box-shadow:0 8px 32px rgba(0,0,0,.6);
  }
  .logo { text-align:center; margin-bottom:28px; }
  .logo h1 { color:#58a6ff; font-size:1.5rem; }
  .logo p  { color:#8b949e; font-size:0.82rem; margin-top:6px; }
  label { display:block; font-size:0.82rem; color:#8b949e; margin-bottom:5px; }
  input {
    width:100%; padding:10px 12px; background:#0d1117; border:1px solid #30363d;
    border-radius:6px; color:#e6edf3; font-size:0.92rem; margin-bottom:16px;
    outline:none; transition:border .2s;
  }
  input:focus { border-color:#58a6ff; }
  .totp-note {
    background:rgba(88,166,255,.08); border:1px solid #1f6feb;
    border-radius:6px; padding:10px 12px; margin-bottom:16px;
    font-size:0.8rem; color:#8b949e; line-height:1.5;
  }
  .totp-note strong { color:#58a6ff; }
  .btn {
    width:100%; padding:11px; background:#1f6feb; color:#fff;
    border:none; border-radius:6px; cursor:pointer;
    font-size:0.95rem; font-weight:600; transition:background .2s;
  }
  .btn:hover { background:#388bfd; }
  .error {
    background:rgba(248,81,73,.12); border:1px solid #f85149;
    border-radius:6px; padding:10px 14px; color:#f85149;
    font-size:0.85rem; margin-bottom:16px; font-weight:600;
  }
  .mfa-badge {
    display:inline-block; background:rgba(63,185,80,.15); border:1px solid #3fb950;
    color:#3fb950; border-radius:12px; padding:2px 10px; font-size:0.75rem;
    font-weight:700; margin-left:8px;
  }
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <h1>&#x1F512; Consola de Seguridad</h1>
    <p>Acceso restringido &middot; Solo personal DTIC</p>
  </div>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST" action="/login">
    <label>Usuario</label>
    <input type="text" name="username" placeholder="admin" autocomplete="off">
    <label>Contraseña</label>
    <input type="password" name="password" placeholder="••••••••">
    <label>
      Código MFA (TOTP) <span class="mfa-badge">2do Factor</span>
    </label>
    <div class="totp-note">
      Usa Google Authenticator o ejecuta:<br>
      <strong>python3 -c "import pyotp; print(pyotp.TOTP('JBSWY3DPEHPK3PXP').now())"</strong>
    </div>
    <input type="text" name="totp" placeholder="123456" maxlength="6" autocomplete="off">
    <button type="submit" class="btn">Iniciar Sesión</button>
  </form>
</div>
</body>
</html>"""


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Consola de Seguridad — SUNIVER</title>
<meta http-equiv="refresh" content="10">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0d1117; color:#e6edf3; }
  .header {
    background:linear-gradient(135deg,#0d2137,#1a3a5c);
    padding:18px 32px; display:flex; align-items:center; justify-content:space-between;
    border-bottom:2px solid #30363d;
  }
  .header h1 { font-size:1.4rem; color:#58a6ff; }
  .header .meta { color:#8b949e; font-size:0.82rem; margin-top:3px; }
  .header-right { display:flex; align-items:center; gap:16px; }
  .user-badge {
    background:rgba(88,166,255,.12); border:1px solid #1f6feb;
    color:#58a6ff; padding:5px 14px; border-radius:20px; font-size:0.82rem;
  }
  .logout { color:#8b949e; font-size:0.82rem; text-decoration:none; }
  .logout:hover { color:#f85149; }

  .main { padding:28px 32px; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; }

  .card {
    background:#161b22; border:1px solid #30363d; border-radius:10px;
    padding:22px; transition:border-color .2s;
  }
  .card:hover { border-color:#58a6ff30; }
  .card-title {
    font-size:0.85rem; color:#8b949e; text-transform:uppercase;
    letter-spacing:.07em; margin-bottom:16px; padding-bottom:10px;
    border-bottom:1px solid #21262d;
  }

  .edr-status { text-align:center; padding:10px 0; }
  .edr-status .big-icon { font-size:3rem; display:block; margin-bottom:8px; }
  .edr-status .status-text { font-size:1.3rem; font-weight:700; }
  .edr-status .status-text.up   { color:#3fb950; }
  .edr-status .status-text.down { color:#f85149; }
  .edr-status .host { color:#8b949e; font-size:0.82rem; margin-top:6px; }

  .protection-section { margin-top:16px; }
  .protection-badge {
    display:inline-flex; align-items:center; gap:8px;
    padding:8px 16px; border-radius:8px; font-weight:700; font-size:0.95rem;
    margin-bottom:14px;
  }
  .protection-badge.on  { background:rgba(63,185,80,.12);  color:#3fb950; border:1px solid #3fb950; }
  .protection-badge.off { background:rgba(248,81,73,.12);  color:#f85149; border:1px solid #f85149; }
  .dot { width:10px; height:10px; border-radius:50%; }
  .dot.green { background:#3fb950; box-shadow:0 0 6px #3fb950; }
  .dot.red   { background:#f85149; box-shadow:0 0 6px #f85149; }

  .btn-toggle {
    padding:10px 22px; border:none; border-radius:7px; cursor:pointer;
    font-size:0.9rem; font-weight:600; transition:all .2s; margin-right:8px;
  }
  .btn-enable  { background:#196c2e; color:#3fb950; border:1px solid #3fb950; }
  .btn-enable:hover  { background:#238636; }
  .btn-disable { background:#5a1d1d; color:#f85149; border:1px solid #f85149; }
  .btn-disable:hover { background:#7d2626; }

  .info-row { display:flex; justify-content:space-between; align-items:center;
              padding:8px 0; border-bottom:1px solid #21262d; font-size:0.88rem; }
  .info-row:last-child { border-bottom:none; }
  .info-row .key { color:#8b949e; }
  .info-row .val { color:#e6edf3; font-weight:500; }
  .info-row .val.ok   { color:#3fb950; }
  .info-row .val.fail { color:#f85149; }

  .siem-link {
    display:block; text-align:center; padding:14px;
    background:rgba(31,111,235,.12); border:1px solid #1f6feb;
    border-radius:8px; color:#58a6ff; text-decoration:none;
    font-weight:600; font-size:0.92rem; transition:background .2s;
  }
  .siem-link:hover { background:rgba(31,111,235,.25); }

  .suniver-link {
    display:block; text-align:center; padding:14px;
    background:rgba(41,128,185,.12); border:1px solid #2980b9;
    border-radius:8px; color:#85c1e9; text-decoration:none;
    font-weight:600; font-size:0.92rem; transition:background .2s; margin-top:10px;
  }
  .suniver-link:hover { background:rgba(41,128,185,.25); }

  .toast {
    display:none; position:fixed; bottom:24px; right:24px;
    background:#161b22; border:1px solid #30363d;
    border-radius:8px; padding:14px 20px; color:#e6edf3;
    font-size:0.9rem; box-shadow:0 4px 16px rgba(0,0,0,.5); z-index:999;
  }
  footer { text-align:center; padding:16px; color:#4a5568; font-size:0.78rem; margin-top:20px; }
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>&#x1F6E1;&#xFE0F; Consola de Seguridad — SUNIVER</h1>
    <div class="meta">DS5.17 COBIT &middot; Defensa en Profundidad &middot; Actualizado: {{ now }}</div>
  </div>
  <div class="header-right">
    <span class="user-badge">&#x1F464; admin DTIC (MFA verificado)</span>
    <a href="/logout" class="logout">Cerrar sesión</a>
  </div>
</div>

<div class="main">
  <div class="grid">

    <!-- Servidor SUNIVER (EDR) -->
    <div class="card">
      <div class="card-title">&#x1F4BB; Servidor SUNIVER (EDR Agent)</div>
      <div class="edr-status">
        {% if edr.status == 'running' %}
          <span class="big-icon">&#x2705;</span>
          <div class="status-text up">ACTIVO</div>
        {% else %}
          <span class="big-icon">&#x1F6AB;</span>
          <div class="status-text down">{{ edr.status|upper }}</div>
        {% endif %}
        <div class="host">servidor-suniver &mdash; 172.29.0.20:8000</div>
      </div>

      <div class="protection-section">
        {% if edr.status == 'running' %}
          {% if edr.protection %}
            <div class="protection-badge on">
              <span class="dot green"></span> Tamper Protection: ACTIVA
            </div>
          {% else %}
            <div class="protection-badge off">
              <span class="dot red"></span> Tamper Protection: DESACTIVADA
            </div>
          {% endif %}
          <br>
          <button class="btn-toggle btn-enable"  onclick="setProtection(true)">&#x1F512; Activar Protección</button>
          <button class="btn-toggle btn-disable" onclick="setProtection(false)">&#x1F513; Desactivar</button>
        {% else %}
          <div class="protection-badge off">
            <span class="dot red"></span> Servidor no disponible
          </div>
        {% endif %}
      </div>
    </div>

    <!-- Sistema SUNIVER -->
    <div class="card">
      <div class="card-title">&#x2139;&#xFE0F; Sistema SUNIVER</div>
      <div class="info-row">
        <span class="key">Servidor (EDR Agent)</span>
        <span class="val {{ 'ok' if edr.status == 'running' else 'fail' }}">
          {{ edr.status|upper }}
        </span>
      </div>
      <div class="info-row">
        <span class="key">Tamper Protection</span>
        <span class="val {{ 'ok' if edr.protection else 'fail' }}">
          {{ 'ACTIVA' if edr.protection else 'DESACTIVADA' }}
        </span>
      </div>
      <div class="info-row">
        <span class="key">Agente de seguridad</span>
        <span class="val">{{ edr.get('agent', 'EDR-Agent v1.0') }}</span>
      </div>
      <div class="info-row">
        <span class="key">Red SUNIVER</span>
        <span class="val">172.29.0.0/24</span>
      </div>
      <div class="info-row">
        <span class="key">Autenticación consola</span>
        <span class="val ok">MFA-TOTP &#x2714;</span>
      </div>
      <div class="info-row">
        <span class="key">Último chequeo</span>
        <span class="val">{{ now }}</span>
      </div>
    </div>

    <!-- Base de Datos SUNIVER -->
    <div class="card" style="grid-column:1/-1">
      <div class="card-title">&#x1F5C4;&#xFE0F; Base de Datos SUNIVER (SQLite)</div>
      <div style="display:flex; gap:24px; flex-wrap:wrap; align-items:flex-start;">
        <div style="flex:1; min-width:220px;">
          {% if db.protected %}
            <div class="protection-badge on">
              <span class="dot green"></span> Anti-Inyección SQL: ACTIVA
            </div>
          {% else %}
            <div class="protection-badge off">
              <span class="dot red"></span> Anti-Inyección SQL: DESACTIVADA
            </div>
          {% endif %}
          <br>
          <button class="btn-toggle btn-enable"  onclick="setDbProtection(true)">&#x1F512; Activar Protección</button>
          <button class="btn-toggle btn-disable" onclick="setDbProtection(false)">&#x1F513; Desactivar</button>
        </div>
        <div style="flex:1; min-width:220px;">
          <div class="info-row">
            <span class="key">Modo de consulta</span>
            <span class="val {{ 'ok' if db.protected else 'fail' }}">
              {{ 'Parametrizada' if db.protected else 'Concatenación directa' }}
            </span>
          </div>
          <div class="info-row">
            <span class="key">Registros de estudiantes</span>
            <span class="val">{{ db.get('total_records', 'N/A') }}</span>
          </div>
          <div class="info-row">
            <span class="key">Intentos de inyección</span>
            <span class="val">{{ db.get('injection_attempts', 0) }}</span>
          </div>
          <div class="info-row">
            <span class="key">Inyecciones exitosas</span>
            <span class="val {{ 'fail' if db.get('injection_successes', 0) > 0 else 'ok' }}">
              {{ db.get('injection_successes', 0) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- SIEM + Portal -->
    <div class="card" style="grid-column:1/-1">
      <div class="card-title">&#x1F4CA; SIEM &mdash; Monitoreo de Seguridad SUNIVER</div>
      <a href="http://localhost:5601" target="_blank" class="siem-link">
        &#x1F517; Abrir Dashboard SIEM &rarr; localhost:5601
      </a>
      <a href="http://localhost:7000" target="_blank" class="suniver-link">
        &#x1F393; Abrir Portal Estudiantil SUNIVER &rarr; localhost:7000
      </a>
    </div>

  </div>
</div>

<div class="toast" id="toast"></div>
<footer>Demo Académica &middot; COBIT DS5.17 &middot; USFX &middot; Defensa en Profundidad</footer>

<script>
function setProtection(enabled) {
  fetch('/set-protection', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({enabled})
  })
  .then(r => r.json())
  .then(data => {
    showToast(enabled ? '&#x1F512; Tamper Protection ACTIVADA' : '&#x1F513; Tamper Protection DESACTIVADA');
    setTimeout(() => location.reload(), 1500);
  })
  .catch(() => showToast('Error al conectar con el servidor SUNIVER'));
}

function setDbProtection(enabled) {
  fetch('/set-db-protection', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({enabled})
  })
  .then(r => r.json())
  .then(data => {
    showToast(enabled ? '&#x1F512; Protección SQL ACTIVADA' : '&#x1F513; Protección SQL DESACTIVADA');
    setTimeout(() => location.reload(), 1500);
  })
  .catch(() => showToast('Error al conectar con la Base de Datos SUNIVER'));
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.innerHTML = msg;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 3000);
}
</script>
</body>
</html>"""


# ──────────────────────────────── Rutas ────────────────────────────────

@app.route("/")
def index():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        totp_code = request.form.get("totp", "").strip()

        totp = pyotp.TOTP(TOTP_SECRET)

        attacker_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if username != USERNAME or password != PASSWORD:
            error = "❌ Credenciales incorrectas"
            log_to_siem(
                "LOGIN_FAILED_CREDENTIALS",
                f"Intento de acceso con credenciales incorrectas | Usuario: '{username}' | Origen: {attacker_ip}",
                "WARNING",
            )
        elif not totp_code:
            error = "❌ Falta el código MFA (TOTP). Segundo factor requerido."
            log_to_siem(
                "LOGIN_FAILED_MFA",
                f"Credenciales correctas pero sin código MFA | Usuario: '{username}' | Origen: {attacker_ip}",
                "CRITICAL",
            )
        elif not totp.verify(totp_code, valid_window=1):
            error = f"❌ Código MFA inválido: '{totp_code}'. Los códigos TOTP expiran cada 30 s."
            log_to_siem(
                "LOGIN_FAILED_MFA",
                f"Credenciales correctas pero código TOTP inválido: '{totp_code}' | Origen: {attacker_ip}",
                "CRITICAL",
            )
        else:
            session["logged_in"] = True
            session["user"] = username
            log_to_siem(
                "LOGIN_SUCCESS",
                f"Acceso concedido a la Consola de Seguridad | Usuario: '{username}' | MFA verificado | Origen: {attacker_ip}",
                "INFO",
            )
            return redirect(url_for("dashboard"))

    return render_template_string(LOGIN_HTML, error=error)


@app.route("/login-api", methods=["POST"])
def login_api():
    data = request.json or {}
    username = data.get("username", "")
    password = data.get("password", "")
    totp_code = str(data.get("totp", "")).strip()

    totp = pyotp.TOTP(TOTP_SECRET)

    attacker_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if username != USERNAME or password != PASSWORD:
        log_to_siem(
            "LOGIN_FAILED_CREDENTIALS",
            f"Intento de acceso con credenciales incorrectas | Usuario: '{username}' | Origen: {attacker_ip}",
            "WARNING",
        )
        return jsonify({"status": "DENEGADO", "motivo": "Credenciales incorrectas"}), 401

    if not totp_code:
        log_to_siem(
            "LOGIN_FAILED_MFA",
            f"Credenciales correctas pero sin código MFA | Usuario: '{username}' | Origen: {attacker_ip} | Defensa MFA activa",
            "CRITICAL",
        )
        return (
            jsonify(
                {
                    "status": "DENEGADO",
                    "motivo": "Segundo factor MFA requerido. El atacante no tiene el código TOTP.",
                    "defensa": "MFA (TOTP) bloquea el acceso aunque la contraseña sea correcta.",
                }
            ),
            401,
        )

    if not totp.verify(totp_code, valid_window=1):
        log_to_siem(
            "LOGIN_FAILED_MFA",
            f"Código TOTP inválido: '{totp_code}' | Usuario: '{username}' | Origen: {attacker_ip}",
            "CRITICAL",
        )
        return (
            jsonify(
                {
                    "status": "DENEGADO",
                    "motivo": f"Código MFA '{totp_code}' inválido o expirado.",
                    "defensa": "TOTP cambia cada 30 s — imposible adivinarlo por fuerza bruta en tiempo real.",
                }
            ),
            401,
        )

    log_to_siem(
        "LOGIN_SUCCESS",
        f"Acceso concedido a la Consola de Seguridad | Usuario: '{username}' | MFA verificado | Origen: {attacker_ip}",
        "INFO",
    )
    return jsonify(
        {
            "status": "CONCEDIDO",
            "mensaje": "Autenticación MFA exitosa. Acceso a la Consola de Seguridad SUNIVER.",
            "usuario": username,
        }
    )


@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    try:
        r = requests.get(f"{VICTIM_URL}/status", timeout=2)
        edr = r.json()
    except Exception:
        edr = {"status": "unreachable", "protection": False, "agent": "N/A"}

    try:
        r2 = requests.get(f"{DATABASE_URL}/status", timeout=2)
        db = r2.json()
    except Exception:
        db = {"protected": False, "total_records": "N/A", "injection_attempts": 0, "injection_successes": 0}

    return render_template_string(
        DASHBOARD_HTML,
        edr=edr,
        db=db,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.route("/set-protection", methods=["POST"])
def set_protection():
    if "logged_in" not in session:
        return jsonify({"error": "No autorizado"}), 401
    enabled = (request.json or {}).get("enabled", True)
    try:
        r = requests.post(f"{VICTIM_URL}/protection", json={"enabled": enabled}, timeout=3)
        return r.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set-db-protection", methods=["POST"])
def set_db_protection():
    if "logged_in" not in session:
        return jsonify({"error": "No autorizado"}), 401
    enabled = (request.json or {}).get("enabled", True)
    try:
        r = requests.post(f"{DATABASE_URL}/protection", json={"enabled": enabled}, timeout=3)
        return r.json()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logout")
def logout():
    user = session.get("user", "desconocido")
    log_to_siem("LOGOUT", f"Sesión cerrada | Usuario: '{user}'", "INFO")
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    print("[Admin] Consola de Seguridad SUNIVER iniciada en puerto 8080", flush=True)
    print(f"[Admin] TOTP secret: {TOTP_SECRET}", flush=True)
    print(
        f"[Admin] Código actual: "
        f"{pyotp.TOTP(TOTP_SECRET).now()} (válido ~30 s)",
        flush=True,
    )
    app.run(host="0.0.0.0", port=8080)
