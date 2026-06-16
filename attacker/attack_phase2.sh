#!/bin/bash
# ================================================================
# FASE 2 — Tamper Protection: Detener el EDR Agent
# DS5.17 COBIT — Defensa en Profundidad
# Ejecutar desde el contenedor attacker: bash /scripts/attack_phase2.sh
# ================================================================

VICTIM_URL="http://172.29.0.20:8000"
SIEM_URL="http://172.29.0.30:5601"
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${CYAN}  FASE 2 — Ataque al EDR Agent (Tamper Protection)${RESET}"
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Objetivo  : EDR Agent → ${VICTIM_URL}"
echo -e "  Atacante  : 172.29.0.10 (Kali Linux)"
echo -e "  Objetivo  : Detener el proceso de protección del endpoint"
echo ""

# ── Estado actual del EDR ────────────────────────────────────
echo -e "${BOLD}[PASO 1]${RESET} Reconocimiento — verificando estado del EDR..."
echo ""
curl -s "${VICTIM_URL}/status" \
     | python3 -m json.tool 2>/dev/null || \
  curl -s "${VICTIM_URL}/status"
echo ""

# ── Intento de detener el EDR ─────────────────────────────────
echo -e "${BOLD}[PASO 2]${RESET} Enviando señal de STOP al EDR Agent..."
echo -e "${YELLOW}  → Simulando un atacante que intenta deshabilitar el antivirus/EDR...${RESET}"
echo ""
STOP_RESPONSE=$(curl -s -X POST "${VICTIM_URL}/stop")
echo "$STOP_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STOP_RESPONSE"
EDR_STATUS=$(echo "$STOP_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
echo ""

# ── Verificar SIEM ────────────────────────────────────────────
echo -e "${BOLD}[PASO 3]${RESET} Verificando alertas en el SIEM..."
echo -e "${YELLOW}  → ¿El intento quedó registrado como evento CRITICAL?${RESET}"
echo ""
curl -s "${SIEM_URL}/logs" \
     | python3 -c "
import json,sys
logs = json.load(sys.stdin)
critical = [l for l in logs if l['severity'] == 'CRITICAL']
print(f'  Total de eventos: {len(logs)}')
print(f'  Alertas CRITICAS: {len(critical)}')
for l in critical[-3:]:
    print(f\"  [{l['severity']}] {l['type']}: {l['message'][:80]}\")
" 2>/dev/null || echo "  (Ver dashboard SIEM en http://localhost:5601)"
echo ""

# ── Resultado — depende del status real de la respuesta ──────
if [ "$EDR_STATUS" = "BLOCKED" ]; then
  echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}${GREEN}║  RESULTADO: EDR PROTEGIDO — ATAQUE BLOQUEADO Y REGISTRADO ║${RESET}"
  echo -e "${BOLD}${GREEN}╚═══════════════════════════════════════════════════════════╝${RESET}"
  echo ""
  echo -e "${GREEN}  DEFENSA ACTIVA:${RESET} Tamper Protection interceptó el intento."
  echo -e "  El EDR sigue corriendo. El evento CRITICAL quedó registrado"
  echo -e "  en el SIEM con la IP atacante y la marca de tiempo."
  echo ""
  echo -e "  ${CYAN}→ Ver alerta en http://localhost:5601${RESET}"
  echo -e "  ${CYAN}→ Para demostrar sin protección: panel admin → Desactivar → volver a ejecutar${RESET}"
elif [ "$EDR_STATUS" = "STOPPED" ]; then
  echo -e "${BOLD}${RED}╔═══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}${RED}║  RESULTADO: EDR DETENIDO — SISTEMA SIN PROTECCIÓN         ║${RESET}"
  echo -e "${BOLD}${RED}╚═══════════════════════════════════════════════════════════╝${RESET}"
  echo ""
  echo -e "${RED}  SIN PROTECCIÓN:${RESET} Tamper Protection estaba desactivada."
  echo -e "  El EDR fue detenido por el atacante. El endpoint ya no"
  echo -e "  tiene protección activa. El SIEM registró AGENT_STOPPED como CRITICAL."
  echo ""
  echo -e "  ${CYAN}→ Para restaurar: docker compose up -d victim${RESET}"
  echo -e "  ${CYAN}→ Luego reactivar protección en http://localhost:8080${RESET}"
else
  echo -e "${BOLD}${YELLOW}  RESULTADO: respuesta inesperada del EDR — revisar estado manualmente${RESET}"
  echo -e "  ${CYAN}→ http://localhost:8080${RESET}"
fi
echo ""
