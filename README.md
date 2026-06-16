# Demo DS5.17 COBIT — Defensa en Profundidad

Demo de 15 minutos para conferencia universitaria. Simula 4 capas de defensa en una red Docker local.

---

## Arquitectura

```
172.29.0.0/24
├── 172.29.0.10  attacker  (Kali Linux)
├── 172.29.0.20  victim    (Ubuntu · EDR Agent :8000)
├── 172.29.0.30  siem      (Flask · Dashboard :5601)
├── 172.29.0.40  admin     (Flask · Panel Admin :8080)
└── 172.29.0.60  database  (Flask + SQLite · API :5050)
```

| Servicio | URL local              | Descripción                        |
|----------|------------------------|------------------------------------|
| SIEM     | http://localhost:5601  | Dashboard de logs + hash chain     |
| Admin    | http://localhost:8080  | Panel admin protegido con MFA      |
| Database | http://localhost:5050  | API REST sobre SQLite (capa de datos) |

---

## Inicio rápido

### 1. Construir e iniciar todo

```powershell
cd C:\demo-ds517
docker compose up --build -d
```

Espera ~30 segundos para que todos los servicios arranquen.

### 2. Verificar que todo está en pie

```powershell
docker compose ps
```

Todos los contenedores deben aparecer como `running`.

### 3. Abrir los dashboards (antes de empezar la demo)

- **SIEM:** http://localhost:5601
- **Admin:** http://localhost:8080

---

## Configuración del TOTP (MFA)

El panel admin usa TOTP con este secreto:

```
JBSWY3DPEHPK3PXP
```

**Opción A — Google Authenticator / Aegis / Authy:**
Añadir manualmente con la clave `JBSWY3DPEHPK3PXP` o escanear el QR generado con:

```
otpauth://totp/Demo-DS517:admin?secret=JBSWY3DPEHPK3PXP&issuer=Demo-DS517
```

**Opción B — Generar código desde la terminal (más rápido para la demo):**

```powershell
# En PowerShell del host
docker exec admin python3 -c "import pyotp; print(pyotp.TOTP('JBSWY3DPEHPK3PXP').now())"
```

El código de 6 dígitos es válido ~30 segundos.

---

## FASE 1 — MFA: Autenticación Multi-Factor

**Objetivo:** Mostrar que conocer la contraseña no es suficiente.

Credenciales conocidas por el atacante: `admin` / `Segur1dad!`

### Ejecutar el ataque

```powershell
docker exec attacker bash /scripts/attack_phase1.sh
```

**Qué verá la audiencia:**
- 3 intentos de login con contraseña correcta pero sin/con código TOTP incorrecto
- Los 3 fallan con `"status": "DENEGADO"`
- El panel en http://localhost:8080 muestra el formulario de login bloqueado

### Demostrar acceso legítimo (presentador)

1. Obtener el código TOTP actual:
   ```powershell
   docker exec admin python3 -c "import pyotp; print(pyotp.TOTP('JBSWY3DPEHPK3PXP').now())"
   ```
2. Ir a http://localhost:8080
3. Ingresar `admin` / `Segur1dad!` + código de 6 dígitos
4. Acceso concedido al panel de administración

**Mensaje clave:** *"El atacante tiene la contraseña pero no el segundo factor físico. MFA añade una capa que el robo de credenciales no puede saltarse."*

---

## FASE 2 — Tamper Protection: Protección del EDR

**Objetivo:** Mostrar que un atacante no puede detener el agente de protección del endpoint.

### Parte A — Con protección activa (defensa)

```powershell
docker exec attacker bash /scripts/attack_phase2.sh
```

**Qué verá la audiencia:**
- El EDR responde `"status": "BLOCKED"` y rechaza la solicitud de detención
- El SIEM registra instantáneamente un evento `CRITICAL` con la IP atacante
- El dashboard SIEM (http://localhost:5601) muestra la alerta en rojo

### Parte B — Sin protección (demostrar el riesgo)

1. En el panel admin (http://localhost:8080), hacer clic en **"Desactivar Protección"**
2. Volver a ejecutar el script de ataque:
   ```powershell
   docker exec attacker bash /scripts/attack_phase2.sh
   ```
3. Esta vez el EDR responde `"status": "STOPPED"` y el contenedor victim se detiene

Para restaurar el victim:
```powershell
docker compose up -d victim
```

**Mensaje clave:** *"Sin Tamper Protection, el primer paso de cualquier ataque avanzado es silenciar el antivirus. Con la capa activa, el intento es detectado y registrado antes de que cause daño."*

---

## FASE 3 — Integridad de Logs: Hash Chain SHA-256

**Objetivo:** Mostrar que alterar los registros del SIEM es detectado automáticamente.

### Ejecutar el ataque

```powershell
docker exec attacker bash /scripts/attack_phase3.sh
```

**Qué verá la audiencia:**
1. Estado inicial: `"integrity": "OK"` — cadena íntegra
2. El atacante modifica el mensaje del registro #2
3. Estado final: `"integrity": "COMPROMETIDA"` — cadena rota
4. El dashboard SIEM (http://localhost:5601) muestra:
   - Banner rojo de alerta crítica
   - La fila modificada resaltada con ❌ ROTO
   - El indicador superior cambia de verde a rojo

**Mensaje clave:** *"Un atacante con acceso a la base de datos puede borrar sus huellas... pero la cadena de hash SHA-256 encadenada delata cualquier modificación, igual que un sello de integridad en evidencia forense."*

---

## FASE 4 — Inyección SQL: Protección de la Capa de Base de Datos

**Objetivo:** Mostrar que, incluso con acceso de red al motor de datos, un atacante no puede robar información sin credenciales si la capa de datos usa consultas parametrizadas.

### Parte A — Con protección activa (defensa, por defecto)

```powershell
docker exec attacker bash /scripts/attack_phase4.sh
```

**Qué verá la audiencia:**
- Una consulta legítima (`username=soporte`) devuelve 1 registro
- El payload `' OR '1'='1` se trata como texto literal — no devuelve registros adicionales
- El SIEM registra un evento `WARNING` (`SQLI_BLOCKED`) con la IP atacante y el payload

### Parte B — Sin protección (demostrar el riesgo)

1. En el panel admin (http://localhost:8080), en la tarjeta **"Capa de Base de Datos"**, hacer clic en **"Desactivar"**
2. Volver a ejecutar el script de ataque:
   ```powershell
   docker exec attacker bash /scripts/attack_phase4.sh
   ```
3. Esta vez la consulta se construye concatenando el payload — `' OR '1'='1` vuelve siempre verdadero
   y la API devuelve **todos** los registros, incluida la nota confidencial del usuario `admin`
   (clave maestra del EDR). El SIEM registra el evento como `CRITICAL` (`SQLI_SUCCESS`)

Para restaurar la protección:
```powershell
# Panel admin → Capa de Base de Datos → Activar Protección
```

**Mensaje clave:** *"La red interna y el firewall no bastan: si la base de datos arma sus consultas concatenando texto del atacante, cualquiera con acceso de red puede volcar toda la tabla. Las consultas parametrizadas (prepared statements) son la defensa que neutraliza la inyección en el propio motor de datos."*

---

## Comandos útiles durante la demo

```powershell
# Ver logs en tiempo real de cada servicio
docker compose logs -f siem
docker compose logs -f victim
docker compose logs -f admin
docker compose logs -f database

# Reiniciar un servicio (ej. victim después de detenerlo en Fase 2)
docker compose up -d victim

# Reiniciar el SIEM para limpiar los logs (entre demos)
docker compose restart siem

# Reiniciar todo desde cero
docker compose down && docker compose up -d

# Ver estado de todos los contenedores
docker compose ps

# Abrir shell en el attacker manualmente
docker exec -it attacker bash
```

---

## Parar la demo

```powershell
docker compose down
```

---

## Resumen de capas de defensa (DS5.17 COBIT)

| Fase | Control | Mecanismo | Qué protege |
|------|---------|-----------|-------------|
| 1    | Autenticación MFA | TOTP (pyotp) | Acceso al panel de administración |
| 2    | Tamper Protection | Flag + alerta SIEM | Integridad del agente EDR |
| 3    | Integridad de logs | Hash chain SHA-256 | Evidencia forense y auditoría |
| 4    | Anti-inyección SQL | Consultas parametrizadas | Confidencialidad de la base de datos |

Cada capa es independiente: si una falla, las otras siguen activas.
