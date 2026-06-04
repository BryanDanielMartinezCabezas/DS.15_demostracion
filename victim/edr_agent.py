import os
import time
import threading
import requests
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

SIEM_URL = "http://siem:5601"
PROTECTED = True  # Tamper Protection activa por defecto


def log_to_siem(event_type, message, severity="INFO"):
    try:
        requests.post(
            f"{SIEM_URL}/log",
            json={
                "source": "EDR-Agent@victim(172.29.0.20)",
                "type": event_type,
                "message": message,
                "severity": severity,
            },
            timeout=3,
        )
    except Exception:
        pass


def wait_for_siem():
    print("[EDR] Esperando que SIEM esté disponible...", flush=True)
    for _ in range(30):
        try:
            requests.get(f"{SIEM_URL}/health", timeout=2)
            print("[EDR] SIEM conectado.", flush=True)
            return
        except Exception:
            time.sleep(3)
    print("[EDR] SIEM no disponible, continuando de todos modos.", flush=True)


def heartbeat():
    while True:
        state = "PROTEGIDO" if PROTECTED else "SIN PROTECCIÓN"
        log_to_siem("HEARTBEAT", f"EDR Agent activo | Estado: {state}", "INFO")
        time.sleep(15)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/status")
def status():
    return jsonify(
        {
            "agent": "EDR-Agent v1.0",
            "status": "running",
            "protection": PROTECTED,
            "host": "victim (172.29.0.20)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
        "PROTECTION_CHANGE",
        f"Tamper Protection {state} por administrador",
        severity,
    )
    print(f"[EDR] Protección {state}", flush=True)
    return jsonify({"protection": PROTECTED, "state": state})


@app.route("/stop", methods=["POST"])
def stop_agent():
    global PROTECTED
    attacker_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if PROTECTED:
        msg = (
            f"INTENTO DE DETENER EL EDR BLOQUEADO | "
            f"Origen: {attacker_ip} | "
            f"Tamper Protection activa — acción rechazada y registrada"
        )
        log_to_siem("TAMPER_ATTEMPT", msg, "CRITICAL")
        print(f"[EDR] ⚠️  ATAQUE BLOQUEADO desde {attacker_ip}", flush=True)
        return (
            jsonify(
                {
                    "status": "BLOCKED",
                    "reason": "Tamper Protection activa",
                    "alert": "Intento registrado en SIEM como evento CRITICAL",
                }
            ),
            403,
        )
    else:
        log_to_siem(
            "AGENT_STOPPED",
            f"EDR detenido por solicitud de {attacker_ip} | Sistema SIN protección",
            "CRITICAL",
        )
        print("[EDR] ⛔ EDR DETENIDO — sistema sin protección", flush=True)

        def shutdown():
            time.sleep(1)
            os._exit(0)

        threading.Thread(target=shutdown, daemon=True).start()
        return jsonify(
            {
                "status": "STOPPED",
                "message": "EDR Agent detenido. El sistema queda sin protección.",
            }
        )


if __name__ == "__main__":
    wait_for_siem()
    log_to_siem(
        "STARTUP",
        "EDR Agent iniciado | Tamper Protection ACTIVA | Monitoreando 172.29.0.0/24",
        "INFO",
    )
    print("[EDR] Iniciando EDR Agent en puerto 8000...", flush=True)
    threading.Thread(target=heartbeat, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
