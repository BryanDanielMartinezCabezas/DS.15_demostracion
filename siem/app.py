import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

logs = []
GENESIS_HASH = "0" * 64

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SIEM — Centro de Operaciones de Seguridad</title>
<meta http-equiv="refresh" content="5">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0d1117; color:#e6edf3; min-height:100vh; }

  .header {
    background:linear-gradient(135deg,#0d2137,#1a3a5c);
    padding:20px 32px;
    display:flex; align-items:center; justify-content:space-between;
    border-bottom:2px solid #30363d;
  }
  .header-left h1 { font-size:1.6rem; color:#58a6ff; letter-spacing:0.02em; }
  .header-left .sub { color:#8b949e; font-size:0.85rem; margin-top:4px; }
  .header-right { text-align:right; color:#8b949e; font-size:0.82rem; line-height:1.6; }
  .header-right span { color:#58a6ff; }

  .integrity-bar {
    padding:14px 32px;
    display:flex; align-items:center; gap:16px;
    background:#161b22; border-bottom:1px solid #30363d;
  }
  .integrity-bar.ok   { border-left:5px solid #3fb950; }
  .integrity-bar.fail { border-left:5px solid #f85149; }

  .dot { width:13px; height:13px; border-radius:50%; flex-shrink:0; }
  .dot.green { background:#3fb950; box-shadow:0 0 8px #3fb950; animation:blink 2s infinite; }
  .dot.red   { background:#f85149; box-shadow:0 0 8px #f85149; animation:blink 1s infinite; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.4} }

  .integrity-label { font-weight:700; font-size:1.05rem; }
  .integrity-label.ok   { color:#3fb950; }
  .integrity-label.fail { color:#f85149; }

  .verify-btn {
    margin-left:auto; padding:7px 18px; background:#1f6feb; color:#fff;
    border:none; border-radius:6px; cursor:pointer; font-size:0.88rem;
    text-decoration:none; display:inline-block;
  }
  .verify-btn:hover { background:#388bfd; }

  .alert-banner {
    margin:20px 32px 0;
    background:rgba(248,81,73,.12); border:1px solid #f85149;
    border-radius:8px; padding:16px 20px;
  }
  .alert-banner h3 { color:#f85149; font-size:1rem; margin-bottom:6px; }
  .alert-banner p  { color:#e6edf3; font-size:0.88rem; line-height:1.5; }

  .main { padding:24px 32px; }

  .stats { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px; }
  .stat { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; text-align:center; }
  .stat .num { font-size:2.2rem; font-weight:700; }
  .stat .lbl { font-size:0.8rem; color:#8b949e; margin-top:4px; }
  .stat.total   .num { color:#58a6ff; }
  .stat.critic  .num { color:#f85149; }
  .stat.warn    .num { color:#d29922; }
  .stat.info    .num { color:#3fb950; }

  .section-title {
    font-size:1rem; font-weight:700; color:#58a6ff; margin-bottom:12px;
    padding-bottom:8px; border-bottom:1px solid #30363d;
  }

  table { width:100%; border-collapse:collapse; font-size:0.85rem; }
  thead th {
    background:#21262d; padding:10px 14px; text-align:left;
    color:#8b949e; text-transform:uppercase; font-size:0.75rem;
    letter-spacing:.05em; position:sticky; top:0;
  }
  tbody tr { border-bottom:1px solid #21262d; transition:background .15s; }
  tbody tr:hover { background:#1c2128; }
  tbody td { padding:9px 14px; vertical-align:top; }

  tr.sev-CRITICAL { background:rgba(248,81,73,.08); }
  tr.sev-WARNING  { background:rgba(210,153,34,.08); }
  tr.tampered     { background:rgba(248,81,73,.18) !important; outline:1px solid #f85149; }

  .badge {
    display:inline-block; padding:2px 9px; border-radius:12px;
    font-size:0.73rem; font-weight:700; white-space:nowrap;
  }
  .badge-CRITICAL { background:rgba(248,81,73,.2); color:#f85149; border:1px solid #f85149; }
  .badge-WARNING  { background:rgba(210,153,34,.2); color:#d29922;  border:1px solid #d29922; }
  .badge-INFO     { background:rgba(88,166,255,.15); color:#58a6ff; border:1px solid #58a6ff; }

  .hash-cell {
    font-family:monospace; font-size:0.75rem; color:#8b949e;
    max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  }
  .hash-cell.broken { color:#f85149; font-weight:700; }

  .integrity-icon { font-size:1rem; }

  footer {
    text-align:center; padding:18px; color:#4a5568; font-size:0.78rem;
    border-top:1px solid #30363d; margin-top:16px;
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>&#x1F6E1;&#xFE0F; SIEM — Centro de Operaciones de Seguridad</h1>
    <div class="sub">Demo DS5.17 COBIT &middot; Defensa en Profundidad &middot; Hash Chain SHA-256</div>
  </div>
  <div class="header-right">
    Actualizado: <span>{{ now }}</span><br>
    Red monitorizada: <span>172.29.0.0/24</span>
  </div>
</div>

<div class="integrity-bar {{ 'ok' if integrity_ok else 'fail' }}">
  <div class="dot {{ 'green' if integrity_ok else 'red' }}"></div>
  <span class="integrity-label {{ 'ok' if integrity_ok else 'fail' }}">
    {% if integrity_ok %}
      INTEGRIDAD DE LOGS: VERIFICADA &#x2714;
    {% else %}
      &#x26A0;&#xFE0F;&nbsp; INTEGRIDAD DE LOGS: COMPROMETIDA &#x2716;
    {% endif %}
  </span>
  <a href="/verify" class="verify-btn">Verificar cadena</a>
</div>

{% if not integrity_ok %}
<div class="alert-banner">
  <h3>&#x1F6A8; ALERTA CRÍTICA — MANIPULACIÓN DE LOGS DETECTADA</h3>
  <p>La cadena de hash SHA-256 ha sido comprometida. Uno o más registros fueron modificados
     sin respetar el protocolo de integridad. La evidencia forense <strong>no puede garantizarse</strong>.</p>
</div>
{% endif %}

<div class="main">
  <div class="stats">
    <div class="stat total">
      <div class="num">{{ total }}</div>
      <div class="lbl">Total de eventos</div>
    </div>
    <div class="stat critic">
      <div class="num">{{ critical_count }}</div>
      <div class="lbl">Alertas críticas</div>
    </div>
    <div class="stat warn">
      <div class="num">{{ warning_count }}</div>
      <div class="lbl">Advertencias</div>
    </div>
    <div class="stat info">
      <div class="num">{{ info_count }}</div>
      <div class="lbl">Eventos info</div>
    </div>
  </div>

  <div class="section-title">&#x1F4CB; Registro de Eventos (cadena SHA-256)</div>

  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Timestamp</th>
        <th>Origen</th>
        <th>Tipo</th>
        <th>Mensaje</th>
        <th>Severidad</th>
        <th>Hash SHA-256</th>
        <th>Integridad</th>
      </tr>
    </thead>
    <tbody>
      {% for log in logs %}
      <tr class="{{ 'tampered' if not log.hash_ok else 'sev-' + log.severity }}">
        <td>{{ log.id }}</td>
        <td style="white-space:nowrap">{{ log.timestamp }}</td>
        <td style="white-space:nowrap">{{ log.source }}</td>
        <td style="white-space:nowrap">{{ log.type }}</td>
        <td>{{ log.message }}</td>
        <td><span class="badge badge-{{ log.severity }}">{{ log.severity }}</span></td>
        <td class="hash-cell {{ 'broken' if not log.hash_ok else '' }}" title="{{ log.hash }}">
          {{ log.hash[:20] }}…
        </td>
        <td class="integrity-icon">
          {% if log.hash_ok %}&#x2705;{% else %}&#x274C; ROTO{% endif %}
        </td>
      </tr>
      {% endfor %}
      {% if not logs %}
      <tr><td colspan="8" style="text-align:center;color:#8b949e;padding:30px">
        Sin eventos registrados aún...
      </td></tr>
      {% endif %}
    </tbody>
  </table>
</div>

<footer>Demo Académica &middot; COBIT DS5.17 &middot; Universidad &middot; Defensa en Profundidad</footer>
</body>
</html>"""


def compute_hash(entry, prev_hash):
    data = (
        f"{entry['id']}"
        f"{entry['timestamp']}"
        f"{entry['source']}"
        f"{entry['type']}"
        f"{entry['message']}"
        f"{prev_hash}"
    )
    return hashlib.sha256(data.encode()).hexdigest()


def verify_chain():
    results = []
    prev_hash = GENESIS_HASH
    for entry in logs:
        expected = compute_hash(entry, prev_hash)
        ok = expected == entry["hash"]
        results.append(ok)
        prev_hash = entry["hash"]  # propagate stored hash so later entries show as broken too
    return results


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/log", methods=["POST"])
def add_log():
    data = request.json or {}
    prev_hash = logs[-1]["hash"] if logs else GENESIS_HASH
    entry = {
        "id": len(logs) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": data.get("source", "unknown"),
        "type": data.get("type", "EVENT"),
        "message": data.get("message", ""),
        "severity": data.get("severity", "INFO"),
    }
    entry["hash"] = compute_hash(entry, prev_hash)
    logs.append(entry)
    print(f"[SIEM] [{entry['severity']}] {entry['type']} — {entry['message'][:60]}", flush=True)
    return jsonify({"status": "logged", "id": entry["id"], "hash": entry["hash"][:16] + "..."})


@app.route("/")
def dashboard():
    chain_results = verify_chain()
    integrity_ok = all(chain_results) if chain_results else True

    display_logs = []
    for i, entry in enumerate(logs):
        e = dict(entry)
        e["hash_ok"] = chain_results[i] if i < len(chain_results) else True
        display_logs.append(e)
    display_logs.reverse()  # mostrar los más recientes primero

    return render_template_string(
        DASHBOARD_HTML,
        logs=display_logs,
        integrity_ok=integrity_ok,
        total=len(logs),
        critical_count=sum(1 for l in logs if l["severity"] == "CRITICAL"),
        warning_count=sum(1 for l in logs if l["severity"] == "WARNING"),
        info_count=sum(1 for l in logs if l["severity"] == "INFO"),
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.route("/verify")
def verify():
    chain_results = verify_chain()
    integrity_ok = all(chain_results) if chain_results else True
    broken = [logs[i]["id"] for i, ok in enumerate(chain_results) if not ok]
    return jsonify(
        {
            "integrity": "OK" if integrity_ok else "COMPROMETIDA",
            "total_logs": len(logs),
            "broken_entries": broken,
            "message": (
                "Cadena de hash íntegra." if integrity_ok
                else f"¡Manipulación detectada en entrada(s): {broken}!"
            ),
        }
    )


@app.route("/tamper", methods=["POST"])
def tamper():
    """Endpoint de demo: modifica un log sin actualizar el hash — rompe la cadena."""
    data = request.json or {}
    entry_id = data.get("id", 2)
    new_message = data.get("message", "*** REGISTRO MANIPULADO ***")

    for entry in logs:
        if entry["id"] == entry_id:
            old_msg = entry["message"]
            entry["message"] = new_message  # modificar SIN recalcular el hash
            print(f"[SIEM] ⚠️  TAMPER en entrada #{entry_id} — cadena de hash ROTA", flush=True)
            return jsonify(
                {
                    "status": "tampered",
                    "id": entry_id,
                    "old_message": old_msg,
                    "new_message": new_message,
                    "consequence": "Hash chain ROTA — manipulación visible en dashboard",
                }
            )

    return jsonify({"error": f"Entrada {entry_id} no encontrada"}), 404


@app.route("/logs")
def get_logs():
    return jsonify(logs)


if __name__ == "__main__":
    startup = {
        "id": 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "SIEM-System(172.29.0.30)",
        "type": "STARTUP",
        "message": "SIEM iniciado | Hash chain SHA-256 activa | Monitoreando 172.29.0.0/24",
        "severity": "INFO",
    }
    startup["hash"] = compute_hash(startup, GENESIS_HASH)
    logs.append(startup)
    print("[SIEM] Iniciando en puerto 5601...", flush=True)
    app.run(host="0.0.0.0", port=5601)
