#!/bin/bash
# ================================================================
# FASE 1 — Ataque de Autenticación: Bypass de MFA (TOTP)
# DS5.17 COBIT — Defensa en Profundidad
# Ejecutar desde el contenedor attacker: bash /scripts/attack_phase1.sh
# ================================================================

ADMIN_URL="http://172.29.0.40:8080"
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${CYAN}  FASE 1 — Ataque al Panel de Administración (MFA)${RESET}"
echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Objetivo  : Panel Admin  → ${ADMIN_URL}"
echo -e "  Atacante  : 172.29.0.10 (Kali Linux)"
echo -e "  Credenciales conocidas: admin / Segur1dad!"
echo ""

# ── Intento 1: sin código MFA ──────────────────────────────────
echo -e "${BOLD}[INTENTO 1/3]${RESET} Login SIN código MFA (solo usuario + contraseña)"
echo -e "${YELLOW}  → El atacante conoce la contraseña pero no tiene el segundo factor...${RESET}"
echo ""
curl -s -X POST "${ADMIN_URL}/login-api" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"Segur1dad!","totp":""}' \
     | python3 -m json.tool 2>/dev/null || \
  curl -s -X POST "${ADMIN_URL}/login-api" \
       -H "Content-Type: application/json" \
       -d '{"username":"admin","password":"Segur1dad!","totp":""}'
echo ""

# ── Intento 2: código MFA adivinado ───────────────────────────
echo -e "${BOLD}[INTENTO 2/3]${RESET} Login con código MFA INCORRECTO (ataque de fuerza bruta: 123456)"
echo -e "${YELLOW}  → Intentando adivinar el código TOTP...${RESET}"
echo ""
curl -s -X POST "${ADMIN_URL}/login-api" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"Segur1dad!","totp":"123456"}' \
     | python3 -m json.tool 2>/dev/null || \
  curl -s -X POST "${ADMIN_URL}/login-api" \
       -H "Content-Type: application/json" \
       -d '{"username":"admin","password":"Segur1dad!","totp":"123456"}'
echo ""

# ── Intento 3: otro código incorrecto ─────────────────────────
echo -e "${BOLD}[INTENTO 3/3]${RESET} Login con código MFA INCORRECTO (000000)"
echo -e "${YELLOW}  → El código TOTP cambia cada 30 segundos — imposible adivinar en tiempo real...${RESET}"
echo ""
curl -s -X POST "${ADMIN_URL}/login-api" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"Segur1dad!","totp":"000000"}' \
     | python3 -m json.tool 2>/dev/null || \
  curl -s -X POST "${ADMIN_URL}/login-api" \
       -H "Content-Type: application/json" \
       -d '{"username":"admin","password":"Segur1dad!","totp":"000000"}'
echo ""

# ── Resultado ────────────────────────────────────────────────
echo -e "${BOLD}${RED}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${RED}║  RESULTADO: ACCESO DENEGADO — MFA BLOQUEA EL ATAQUE ║${RESET}"
echo -e "${BOLD}${RED}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${GREEN}  DEFENSA ACTIVA:${RESET} Aunque el atacante conoce la contraseña,"
echo -e "  el segundo factor TOTP (que cambia cada 30 s) hace"
echo -e "  el acceso imposible sin el dispositivo del administrador."
echo ""
echo -e "  ${CYAN}→ Abrir http://localhost:8080 para ver el panel admin${RESET}"
echo -e "  ${CYAN}→ Usar el código TOTP correcto para demostrar acceso legítimo${RESET}"
echo ""
