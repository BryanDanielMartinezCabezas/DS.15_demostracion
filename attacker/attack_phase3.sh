#!/bin/bash
# ================================================================
# FASE 3 — Integridad de Logs: Manipulación de Registros SIEM
# DS5.17 COBIT — Defensa en Profundidad
# Ejecutar desde el contenedor attacker: bash /scripts/attack_phase3.sh
# ================================================================

SIEM_URL="http://172.29.0.30:5601"
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${CYAN}  FASE 3 — Manipulación de Logs (Hash Chain Integrity)${RESET}"
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Objetivo  : SIEM → ${SIEM_URL}"
echo -e "  Atacante  : 172.29.0.10 (Kali Linux)"
echo -e "  Objetivo  : Modificar un registro para ocultar actividad maliciosa"
echo ""

# ── Estado de integridad antes ────────────────────────────────
echo -e "${BOLD}[PASO 1]${RESET} Verificando integridad de la cadena de logs ANTES del ataque..."
echo ""
curl -s "${SIEM_URL}/verify" \
     | python3 -m json.tool 2>/dev/null || \
  curl -s "${SIEM_URL}/verify"
echo ""

# ── Ver logs actuales ─────────────────────────────────────────
echo -e "${BOLD}[PASO 2]${RESET} Consultando registros existentes..."
echo ""
curl -s "${SIEM_URL}/logs" \
     | python3 -c "
import json,sys
logs = json.load(sys.stdin)
print(f'  Total de registros: {len(logs)}')
for l in logs[:5]:
    print(f\"  #{l['id']} [{l['severity']}] {l['message'][:70]}\")
if len(logs) > 5:
    print(f'  ... ({len(logs)-5} más)')
" 2>/dev/null || echo "  (No se pudo obtener los logs)"
echo ""

# ── Modificar un registro ─────────────────────────────────────
echo -e "${BOLD}[PASO 3]${RESET} Modificando registro #2 para encubrir actividad maliciosa..."
echo -e "${YELLOW}  → El atacante altera el mensaje pero no puede actualizar el hash...${RESET}"
echo ""
curl -s -X POST "${SIEM_URL}/tamper" \
     -H "Content-Type: application/json" \
     -d '{"id": 2, "message": "*** Sistema operando normalmente *** [MODIFICADO POR ATACANTE - ocultando intrusión]"}' \
     | python3 -m json.tool 2>/dev/null || \
  curl -s -X POST "${SIEM_URL}/tamper" \
       -H "Content-Type: application/json" \
       -d '{"id": 2, "message": "*** Sistema operando normalmente *** [MODIFICADO POR ATACANTE]"}'
echo ""

# ── Verificar integridad después ──────────────────────────────
echo -e "${BOLD}[PASO 4]${RESET} Verificando integridad DESPUÉS de la manipulación..."
echo -e "${YELLOW}  → ¿Detecta el SIEM que la cadena fue rota?${RESET}"
echo ""
curl -s "${SIEM_URL}/verify" \
     | python3 -m json.tool 2>/dev/null || \
  curl -s "${SIEM_URL}/verify"
echo ""

# ── Resultado ────────────────────────────────────────────────
echo -e "${BOLD}${RED}╔════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${RED}║  RESULTADO: MANIPULACIÓN DETECTADA — CADENA SHA-256 COMPROMETIDA ║${RESET}"
echo -e "${BOLD}${RED}╚════════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${GREEN}  DEFENSA ACTIVA:${RESET} Cada registro lleva un hash SHA-256 encadenado."
echo -e "  Al modificar el mensaje, el hash ya no coincide con el contenido"
echo -e "  y la cadena se rompe — la manipulación es detectable forense-"
echo -e "  mente aunque el atacante tenga acceso a la base de datos."
echo ""
echo -e "  ${CYAN}→ Ver alerta ROJA en http://localhost:5601${RESET}"
echo -e "     La entrada manipulada aparece destacada con ❌ ROTO"
echo ""
