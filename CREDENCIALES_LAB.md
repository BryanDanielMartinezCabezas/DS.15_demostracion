# Credenciales y Guía de Laboratorio — DS5.17
# Tener esto abierto durante la presentación

---

## PASO 0 — Levantar todo (hacer ANTES de la charla)

```powershell
# Desde C:\demo-ds517 en PowerShell:
docker compose up -d
```

Verificar que todo está corriendo:
```powershell
docker compose ps
```
Deben aparecer 6 contenedores con estado "running".

---

## PASO 1 — Abrir estos 3 navegadores/pestañas

| URL | Qué es |
|-----|--------|
| http://localhost:8080 | Panel Admin (Consola de Seguridad) |
| http://localhost:5601 | SIEM (dashboard de alertas) |
| http://localhost:7000 | Portal SUNIVER |

---

## CREDENCIALES

### Panel Admin — localhost:8080
```
Usuario:    admin
Contraseña: Segur1dad!
Código MFA: [ver abajo]
```

**Cómo obtener el código MFA (TOTP):**

Opción A — Celular (recomendada para la presentación):
1. Instalar Google Authenticator o Authy
2. Agregar cuenta manualmente
3. Ingresar clave secreta: JBSWY3DPEHPK3PXP
4. Usar el código de 6 dígitos que aparece

Opción B — Terminal (si no tenés el celular):
```powershell
pip install pyotp
python -c "import pyotp; print(pyotp.TOTP('JBSWY3DPEHPK3PXP').now())"
```
⚠ El código expira en 30 segundos — ingresarlo rápido.

### Portal SUNIVER — localhost:7000
```
CI:         cualquier número (ej: 7559063)
Contraseña: cualquier texto (ej: 123456)
```
No tiene autenticación real — es la réplica visual.

---

## FASE 1 — Ataque MFA

**Qué hace:** El atacante intenta entrar al panel admin sin el código TOTP.

```powershell
docker exec attacker bash /scripts/attack_phase1.sh
```

**Resultado esperado:**
```json
{"status": "DENEGADO", "motivo": "Segundo factor MFA requerido"}
```

**Lo que ves en el SIEM (localhost:5601):** Nada nuevo — el ataque ni llega a registrarse
porque falla antes del sistema. Ese es el punto: MFA es la primera puerta.

---

## FASE 2 — Ataque Tamper Protection (EDR)

**Qué hace:** El atacante intenta apagar el antivirus.

```powershell
docker exec attacker bash /scripts/attack_phase2.sh
```

**Con protección activa:**
```json
{"status": "BLOCKED", "reason": "Tamper Protection activa"}
```
Ver en SIEM: alerta CRITICAL — TAMPER_ATTEMPT

**Para mostrar el "sin protección":**
1. Ir a localhost:8080 → "Desactivar" en la tarjeta EDR
2. Repetir el comando
3. El contenedor victim cae — el EDR muere
4. Volver a activar: `docker compose up -d victim`

---

## FASE 3 — Ataque Integridad de Logs (SIEM)

**Qué hace:** El atacante modifica un registro de log para borrar evidencia.

```powershell
docker exec attacker bash /scripts/attack_phase3.sh
```

**Resultado:** El dashboard SIEM muestra ❌ ROTO en el registro modificado.
La barra superior cambia a rojo: "INTEGRIDAD COMPROMETIDA".

Ir a localhost:5601 y refrescar para verlo.

**Para resetear el SIEM** (volver a estado limpio):
```powershell
docker compose restart siem
```

---

## FASE 4 — Ataque Inyección SQL (Base de Datos)

**Qué hace:** El atacante roba todos los expedientes sin credenciales.

```powershell
docker exec attacker bash /scripts/attack_phase4.sh
```

**Con protección activa:** 0 resultados. SIEM registra SQLI_BLOCKED (WARNING).

**Para mostrar el "sin protección":**
1. Ir a localhost:8080 → "Desactivar" en la tarjeta Base de Datos
2. Repetir el comando
3. Se exponen los 3 registros, incluyendo:
   `Token API DTIC-SUNIVER: SK-2024-9f8e7d`

**Para reactivar:**
localhost:8080 → "Activar Protección" en Base de Datos

---

## RESETEAR TODO (si algo sale mal)

```powershell
# Reiniciar todos los contenedores desde cero:
docker compose down
docker compose up -d
```

Esperar ~15 segundos y refrescar los navegadores.

---

## ORDEN RECOMENDADO EN LA PRESENTACIÓN

```
1. Mostrar portal SUNIVER (localhost:7000) — "esto es lo que protegemos"
2. Mostrar panel admin (localhost:8080) — "este es el tablero de control"
3. Mostrar SIEM vacío (localhost:5601) — "aquí se registra todo"

4. Fase 1: script → mostrar DENEGADO
5. Fase 2: script → BLOCKED → desactivar → volver a correr → EDR cae
6. Fase 3: script → mostrar SIEM con ❌ ROTO
7. Fase 4: script → 0 resultados → desactivar → token DTIC expuesto
```

---

## Si Git Bash da error de rutas con /scripts/

Usar este prefijo:
```powershell
MSYS_NO_PATHCONV=1 docker exec attacker bash /scripts/attack_phase1.sh
```
