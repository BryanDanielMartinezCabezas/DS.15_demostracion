import os
import time
import sqlite3
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

SIEM_URL = "http://siem:5601"
DB_PATH = "/app/suniver.db"
PROTECTED = True

EVENTS_SENT = 0
INJECTION_ATTEMPTS = 0
INJECTION_SUCCESSES = 0

SUSPICIOUS_TOKENS = ["' OR ", "OR '1'='1", "UNION SELECT", "--", "DROP TABLE", "'='"]


def log_to_siem(event_type, message, severity="INFO"):
    global EVENTS_SENT
    try:
        requests.post(
            f"{SIEM_URL}/log",
            json={
                "source": "Database-SUNIVER@db(172.29.0.60)",
                "type": event_type,
                "message": message,
                "severity": severity,
            },
            timeout=3,
        )
        EVENTS_SENT += 1
    except Exception:
        pass


def wait_for_siem():
    print("[DB] Esperando que SIEM esté disponible...", flush=True)
    for _ in range(30):
        try:
            requests.get(f"{SIEM_URL}/health", timeout=2)
            print("[DB] SIEM conectado.", flush=True)
            return
        except Exception:
            time.sleep(3)
    print("[DB] SIEM no disponible, continuando de todos modos.", flush=True)


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    fresh = not os.path.exists(DB_PATH)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY,
            ci TEXT NOT NULL,
            nombre TEXT NOT NULL,
            datos_acceso TEXT NOT NULL
        )"""
    )
    if fresh:
        cur.executemany(
            "INSERT INTO estudiantes (ci, nombre, datos_acceso) VALUES (?, ?, ?)",
            [
                (
                    "admin_dtic",
                    "Administrador DTIC-USFX",
                    "Token API DTIC-SUNIVER: SK-2024-9f8e7d. SOLO USO INTERNO. NO COMPARTIR.",
                ),
                (
                    "1234567",
                    "Carlos Mamani López",
                    "Expediente: Gestión 2024-I | Carrera: Medicina | Promedio: 72",
                ),
                (
                    "7654321",
                    "María Condori Vargas",
                    "Expediente: Gestión 2024-I | Carrera: Derecho | Promedio: 85",
                ),
            ],
        )
        conn.commit()
    conn.close()


def count_records():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM estudiantes")
    n = cur.fetchone()[0]
    conn.close()
    return n


def is_suspicious(value):
    upper = value.upper()
    return any(token.upper() in upper for token in SUSPICIOUS_TOKENS)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/status")
def status():
    return jsonify(
        {
            "service": "Base de Datos SUNIVER",
            "engine": "SQLite3",
            "protected": PROTECTED,
            "mode": (
                "Consultas parametrizadas (prepared statements)"
                if PROTECTED
                else "Concatenación directa de SQL (vulnerable)"
            ),
            "total_records": count_records(),
            "injection_attempts": INJECTION_ATTEMPTS,
            "injection_successes": INJECTION_SUCCESSES,
            "events_sent": EVENTS_SENT,
        }
    )


@app.route("/protection", methods=["POST"])
def set_protection():
    global PROTECTED
    data = request.json or {}
    PROTECTED = data.get("enabled", True)
    state = "ACTIVADA" if PROTECTED else "DESACTIVADA"
    severity = "WARNING" if not PROTECTED else "INFO"
    log_to_siem(
        "DB_PROTECTION_CHANGE",
        f"Protección anti-inyección SQL (consultas parametrizadas) {state} por administrador",
        severity,
    )
    print(f"[DB] Protección {state}", flush=True)
    return jsonify({"protection": PROTECTED, "state": state})


@app.route("/search")
def search():
    global INJECTION_ATTEMPTS, INJECTION_SUCCESSES
    ci = request.args.get("ci", "")
    attacker_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    suspicious = is_suspicious(ci)

    conn = get_connection()
    cur = conn.cursor()

    if PROTECTED:
        cur.execute(
            "SELECT id, ci, nombre, datos_acceso FROM estudiantes WHERE ci = ?",
            (ci,),
        )
        query_shown = "SELECT ... FROM estudiantes WHERE ci = ?  -- valor enlazado, no concatenado"
    else:
        query = f"SELECT id, ci, nombre, datos_acceso FROM estudiantes WHERE ci = '{ci}'"
        query_shown = query
        try:
            cur.execute(query)
        except sqlite3.Error as e:
            conn.close()
            log_to_siem(
                "SQLI_ERROR",
                f"Consulta SQL inválida provocada por payload de inyección | Origen: {attacker_ip} | Payload: {ci}",
                "WARNING",
            )
            return jsonify({"error": str(e), "protected": PROTECTED}), 400

    rows = cur.fetchall()
    conn.close()
    results = [
        {"id": r[0], "ci": r[1], "nombre": r[2], "datos_acceso": r[3]}
        for r in rows
    ]

    if suspicious:
        INJECTION_ATTEMPTS += 1
        if not PROTECTED and len(results) > 1:
            INJECTION_SUCCESSES += 1
            log_to_siem(
                "SQLI_SUCCESS",
                f"INYECCIÓN SQL EXITOSA | Origen: {attacker_ip} | Payload: {ci} | Registros expuestos: {len(results)} (incl. token DTIC)",
                "CRITICAL",
            )
        else:
            log_to_siem(
                "SQLI_BLOCKED",
                f"Intento de inyección SQL neutralizado por consultas parametrizadas | Origen: {attacker_ip} | Payload: {ci}",
                "WARNING",
            )

    return jsonify(
        {
            "protected": PROTECTED,
            "query": query_shown,
            "results": results,
            "count": len(results),
        }
    )


if __name__ == "__main__":
    wait_for_siem()
    init_db()
    log_to_siem(
        "STARTUP",
        "Base de Datos SUNIVER iniciada | Protección anti-SQLi (consultas parametrizadas) ACTIVA | 3 registros de estudiantes cargados",
        "INFO",
    )
    print("[DB] Iniciando Base de Datos SUNIVER en puerto 5050...", flush=True)
    app.run(host="0.0.0.0", port=5050)
