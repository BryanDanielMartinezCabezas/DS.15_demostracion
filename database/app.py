import json
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

SEED_STUDENTS = [
    (
        "admin_dtic",
        "Administrador DTIC-USFX",
        "DTIC",
        "Token API DTIC-SUNIVER: SK-2024-9f8e7d. SOLO USO INTERNO. NO COMPARTIR.",
        "[]",
    ),
    (
        "1234567",
        "Carlos Mamani López",
        "Medicina",
        "Carrera: Medicina | Semestre: 1/2026 | Promedio: 74.8 | Estado: Regular",
        json.dumps([
            {"cod": "ANT301", "mat": "ANATOMÍA HUMANA I",       "curso": 3, "grupo": 1, "sea": "D", "p1": 18, "p2": 20, "np": 19.0, "prac": 12, "lab": 0,  "ns": 51.0, "ef": 32, "nf": 70},
            {"cod": "FIS201", "mat": "FISIOLOGÍA I",             "curso": 3, "grupo": 1, "sea": "A", "p1": 22, "p2": 25, "np": 23.5, "prac":  8, "lab": 18, "ns": 49.5, "ef": 30, "nf": 77},
            {"cod": "BIO150", "mat": "BIOQUÍMICA",               "curso": 3, "grupo": 1, "sea": "G", "p1": 15, "p2": 18, "np": 16.5, "prac": 10, "lab": 0,  "ns": 46.5, "ef": 28, "nf": 61},
            {"cod": "PAT402", "mat": "PATOLOGÍA GENERAL",        "curso": 4, "grupo": 1, "sea": "D", "p1": 24, "p2": 28, "np": 26.0, "prac": 16, "lab": 0,  "ns": 62.0, "ef": 38, "nf": 90},
            {"cod": "FAR201", "mat": "FARMACOLOGÍA I",           "curso": 3, "grupo": 2, "sea": "G", "p1": 20, "p2": 22, "np": 21.0, "prac": 14, "lab": 0,  "ns": 55.0, "ef": 35, "nf": 77},
        ]),
    ),
    (
        "7654321",
        "María Condori Vargas",
        "Derecho",
        "Carrera: Derecho | Semestre: 1/2026 | Promedio: 84.6 | Estado: Regular",
        json.dumps([
            {"cod": "DER101", "mat": "DERECHO CIVIL I",             "curso": 2, "grupo": 1, "sea": "D", "p1": 28, "p2": 30, "np": 29.0, "prac": 18, "lab": 0, "ns": 77.0, "ef": 38, "nf": 96},
            {"cod": "DER202", "mat": "DERECHO CONSTITUCIONAL",      "curso": 2, "grupo": 1, "sea": "D", "p1": 25, "p2": 27, "np": 26.0, "prac": 16, "lab": 0, "ns": 68.0, "ef": 35, "nf": 87},
            {"cod": "DER303", "mat": "DERECHO PENAL GENERAL",       "curso": 3, "grupo": 1, "sea": "G", "p1": 22, "p2": 24, "np": 23.0, "prac": 14, "lab": 0, "ns": 55.0, "ef": 32, "nf": 78},
            {"cod": "DER404", "mat": "DERECHO COMERCIAL",           "curso": 3, "grupo": 2, "sea": "D", "p1": 20, "p2": 22, "np": 21.0, "prac": 14, "lab": 0, "ns": 55.0, "ef": 30, "nf": 72},
            {"cod": "PRO101", "mat": "PROC. CIVIL INTRODUCTORIO",   "curso": 2, "grupo": 1, "sea": "D", "p1": 26, "p2": 28, "np": 27.0, "prac": 18, "lab": 0, "ns": 72.0, "ef": 36, "nf": 90},
        ]),
    ),
    (
        "5678901",
        "Ana Quispe Flores",
        "Ing. en Ciencias de la Computación",
        "Carrera: Ing. Computación | Semestre: 1/2026 | Promedio: 81.0 | Estado: Regular",
        json.dumps([
            {"cod": "SIS330", "mat": "DESARROLLO DE APLICACIONES INTELIGENTES", "curso": 7, "grupo": 1, "sea": "A", "p1": 18, "p2": 20, "np": 19.0, "prac": 8,  "lab": 22, "ns": 49.0, "ef": 35, "nf": 84},
            {"cod": "COM600", "mat": "MICRO SERVICIOS",                          "curso": 7, "grupo": 1, "sea": "D", "p1": 40, "p2": 42, "np": 41.0, "prac": 18, "lab": 0,  "ns": 59.0, "ef": 28, "nf": 87},
            {"cod": "SIS254", "mat": "SEGURIDAD DE LA INFORMACIÓN",              "curso": 7, "grupo": 1, "sea": "I", "p1": 22, "p2": 24, "np": 23.0, "prac": 9,  "lab": 20, "ns": 52.0, "ef": 30, "nf": 82},
            {"cod": "COM480", "mat": "ROBÓTICA I",                               "curso": 7, "grupo": 1, "sea": "G", "p1": 25, "p2": 30, "np": 27.5, "prac": 15, "lab": 0,  "ns": 42.5, "ef": 32, "nf": 75},
            {"cod": "SIS325", "mat": "ADM. DE PROYECTOS DE SOFTWARE",            "curso": 8, "grupo": 1, "sea": "G", "p1": 30, "p2": 28, "np": 29.0, "prac": 14, "lab": 0,  "ns": 43.0, "ef": 34, "nf": 77},
        ]),
    ),
]


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
    cur.execute("""CREATE TABLE IF NOT EXISTS estudiantes (
        id INTEGER PRIMARY KEY,
        ci TEXT NOT NULL,
        nombre TEXT NOT NULL,
        carrera TEXT NOT NULL DEFAULT '',
        datos_acceso TEXT NOT NULL,
        notas TEXT NOT NULL DEFAULT '[]'
    )""")
    if fresh:
        cur.executemany(
            "INSERT INTO estudiantes (ci, nombre, carrera, datos_acceso, notas) VALUES (?, ?, ?, ?, ?)",
            SEED_STUDENTS,
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
    return jsonify({
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
    })


@app.route("/student")
def get_student():
    """Endpoint interno para SUNIVER — siempre parametrizado."""
    ci = request.args.get("ci", "")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT ci, nombre, carrera, datos_acceso, notas FROM estudiantes WHERE ci = ? AND notas != '[]'",
        (ci,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify({
            "found": True,
            "ci": row[0],
            "nombre": row[1],
            "carrera": row[2],
            "datos_acceso": row[3],
            "notas": json.loads(row[4]),
        })
    return jsonify({"found": False})


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
            "SELECT id, ci, nombre, carrera, datos_acceso FROM estudiantes WHERE ci = ?",
            (ci,),
        )
        query_shown = "SELECT ... FROM estudiantes WHERE ci = ?  -- valor enlazado, no concatenado"
    else:
        query = f"SELECT id, ci, nombre, carrera, datos_acceso FROM estudiantes WHERE ci = '{ci}'"
        query_shown = query
        try:
            cur.execute(query)
        except sqlite3.Error as e:
            conn.close()
            log_to_siem(
                "SQLI_ERROR",
                f"Consulta SQL inválida provocada por payload | Origen: {attacker_ip} | Payload: {ci}",
                "WARNING",
            )
            return jsonify({"error": str(e), "protected": PROTECTED}), 400

    rows = cur.fetchall()
    conn.close()
    results = [
        {"id": r[0], "ci": r[1], "nombre": r[2], "carrera": r[3], "datos_acceso": r[4]}
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
                f"Intento de inyección SQL neutralizado | Origen: {attacker_ip} | Payload: {ci}",
                "WARNING",
            )

    return jsonify({
        "protected": PROTECTED,
        "query": query_shown,
        "results": results,
        "count": len(results),
    })


if __name__ == "__main__":
    wait_for_siem()
    init_db()
    log_to_siem(
        "STARTUP",
        "Base de Datos SUNIVER iniciada | Protección anti-SQLi ACTIVA | 4 registros cargados (3 estudiantes + admin DTIC)",
        "INFO",
    )
    print("[DB] Iniciando Base de Datos SUNIVER en puerto 5050...", flush=True)
    app.run(host="0.0.0.0", port=5050)
