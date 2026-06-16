# Guion de Diapositivas — Demo DS5.17 COBIT: Defensa en Profundidad
# USFX — Universidad San Francisco Xavier de Chuquisaca

> 15 minutos. Una idea por diapositiva. Texto grande, pocas palabras.
> Paleta: fondo `#0d1117`, azul `#58a6ff`, verde `#3fb950`, rojo `#f85149`, amarillo `#d29922`.

---

## DIAPOSITIVA 1 — Portada

**Título:** Defensa en Profundidad
**Subtítulo:** DS5.17 COBIT · Protección de las Funciones de Seguridad

**Visual:** Logo USFX + escudo digital (fondo oscuro, azul eléctrico)
**Pie:** Nombre · USFX · Fecha

**Orador:**
> "Hoy vamos a atacar un sistema universitario en vivo.
> Sin trucos, sin grabaciones. Y vamos a ver exactamente qué lo detiene."

---

## DIAPOSITIVA 2 — ¿Qué dice DS5.17?

**Título grande:**
> "Los mecanismos de seguridad deben protegerse a sí mismos."

**3 bullets:**
- No alcanza con tener antivirus — hay que proteger el antivirus
- No alcanza con tener logs — hay que garantizar que no se falsifiquen
- No alcanza con tener base de datos — hay que proteger cómo se consulta

**Orador:**
> "DS5.17 no habla de proteger datos. Habla de proteger las herramientas
> que protegen los datos. Es un nivel más adentro."

---

## DIAPOSITIVA 3 — El sistema objetivo

**Título:** ¿Qué estamos protegiendo?

**Imagen:** captura del portal SUNIVER (login naranja)

**3 bullets:**
- Portal estudiantil USFX — expedientes, calificaciones, matrículas
- Administrado por el DTIC — contiene credenciales de acceso interno
- Un atacante dentro de la red puede comprometer todo sin contraseña

**Orador:**
> "Este es el sistema SUNIVER, replicado para la demo.
> El objetivo del atacante: los expedientes de los estudiantes
> y el token secreto del DTIC."

---

## DIAPOSITIVA 4 — La metáfora central

**Título:** El castillo y sus capas

**Visual: diagrama de capas (de afuera hacia adentro)**
```
Firewall → MFA → Antivirus/EDR → Integridad de logs → Base de datos
```

**Frase central grande:**
> "Cada capa asume que la anterior ya fue comprometida."

**Orador:**
> "Un castillo medieval no tenía solo murallas. Tenía foso, muralla,
> torre de guardia y cámara del tesoro. Si el atacante cruza el foso,
> todavía enfrenta la muralla. Si la rompe, todavía hay guardias adentro.
> Eso es defensa en profundidad."

---

## DIAPOSITIVA 5 — Mapa de las 4 capas

**Título:** 4 ataques · 4 controles · 1 marco DS5.17

| # | El ataque | El control | Qué protege |
|---|-----------|-----------|-------------|
| 1 | Robé tu contraseña | MFA — código cada 30 s | Acceso al panel |
| 2 | Voy a apagar el antivirus | Tamper Protection | El propio EDR |
| 3 | Voy a borrar las huellas | Hash chain SHA-256 | La evidencia forense |
| 4 | Voy a robar la base de datos | Consultas parametrizadas | Los expedientes |

**Orador:**
> "Esta tabla es el mapa de todo lo que vamos a ver.
> Cada fila es un intento del atacante — y lo que lo detiene."

---

## DIAPOSITIVA 6 — FASE 1: MFA

**Título:** "Tengo tu contraseña. ¿Y ahora?"

### La analogía
> Como un cajero automático: tener la tarjeta robada no alcanza.
> También necesitás el PIN. El atacante robó la tarjeta — no sabe el PIN.

**Visual:** tarjeta bancaria ✓ + PIN ✗ = acceso denegado

### El mecanismo
- Secreto compartido entre el servidor y tu celular
- Ese secreto + la hora actual → código de 6 dígitos
- Cambia cada 30 segundos
- Sin el secreto físico, imposible calcularlo

### En la industria
Bancos, Gmail, GitHub, hospitales. Estándar mínimo para acceso administrativo.

### Demo
```powershell
docker exec attacker bash /scripts/attack_phase1.sh
```
**Resultado:** `"status": "DENEGADO"` — credenciales correctas, sin código TOTP = bloqueado

**Orador:**
> "El atacante hizo todo bien. Consiguió usuario y contraseña.
> Pero hay un segundo cerrojo que no puede romper en tiempo real."

---

## DIAPOSITIVA 7 — FASE 2: Tamper Protection

**Título:** "Lo primero: apagar el antivirus"

### La analogía
> Como un sereno con instrucciones escritas del dueño:
> *"Solo obedecé órdenes de apagado si el director viene en persona con su CI."*
> Cualquier llamada por teléfono diciendo "soy el jefe, andate" — ignorada.

**Visual:** teléfono tachado → guardia firme en su puesto

### El mecanismo
- El EDR tiene una variable: `PROTECTED = True`
- Recibe señal de apagado → consulta: ¿estoy protegido?
- Si sí → rechaza, avisa al SIEM con alerta CRITICAL
- Si no → se apaga (esto se demuestra en vivo)

### En la industria
Windows Defender, CrowdStrike, SentinelOne — todos tienen tamper protection.
Obligatorio en cualquier EDR moderno. El 90% del ransomware intenta
desactivar el antivirus antes de ejecutarse.

### Demo — dos pasos
**Con protección activa:**
```powershell
docker exec attacker bash /scripts/attack_phase2.sh
```
Resultado: `"status": "BLOCKED"` + alerta CRITICAL en SIEM

**Sin protección (mostrar consecuencia):**
1. Panel admin → Desactivar Tamper Protection
2. Repetir el script → el EDR cae

**Orador:**
> "Primero lo vemos bloqueado. Luego desactivo la protección
> para que vean qué pasa en un sistema sin DS5.17.
> El guardián simplemente desaparece."

---

## DIAPOSITIVA 8 — FASE 3: Hash Chain

**Título:** "Ya entré. Ahora borro las huellas."

### La analogía
> Como el libro de actas de la universidad: cada página tiene
> un número correlativo y un sello que referencia la página anterior.
> Si arrancás una hoja, los números no cuadran.
> Si cambiás algo en una página, el sello de la siguiente ya no coincide.

**Visual:** libro de actas con una hoja marcada en rojo ❌

### El mecanismo
```
Log 1: "SIEM iniciado"   → hash_1 = A7F3...
Log 2: "Ataque recibido" → hash_2 = B9C1... (usa hash_1)
Log 3: "Heartbeat"       → hash_3 = D4E2... (usa hash_2)
```
El atacante modifica Log 2 → su hash sigue siendo `B9C1...`
El sistema recalcula → da `X5Q8...` → **no coincide → ROTO**

### En la industria
Splunk, IBM QRadar, registros forenses bancarios, blockchain.
Cualquier evidencia que deba ser admisible en juicio debe ser incorruptible.

### Demo
```powershell
docker exec attacker bash /scripts/attack_phase3.sh
```
Ir a localhost:5601 — el registro modificado muestra **❌ ROTO**
La barra superior cambia a rojo: **INTEGRIDAD COMPROMETIDA**

**Orador:**
> "El atacante cambió el texto del log. Pero no puede cambiar el hash
> sin que se note. Y no puede recalcular toda la cadena
> porque necesitaría reescribir cada registro desde el principio."

---

## DIAPOSITIVA 9 — FASE 4: Inyección SQL

**Título:** "No necesito contraseña. Solo sé hablar SQL."

### La analogía
> En la ventanilla de matrículas te dicen: *"escribí tu CI"*.
> Vos escribís: `7559063' O devolveme todos los registros --`
>
> Una ventanilla inteligente solo acepta números de CI.
> Una ventanilla descuidada ejecuta lo que escribiste como instrucción.

**Visual:** formulario con campo CI → con payload vs. sin payload

### El ataque (solo robar — sin contraseña, sin hackeo previo)
```
Consulta normal:   ci = 1234567         → 1 resultado
Consulta maliciosa: ci = ' OR '1'='1   → TODOS los registros
```

### El mecanismo
**Vulnerable — concatenación:**
```sql
WHERE ci = '' OR '1'='1'   ← siempre verdadero → devuelve todo
```
**Protegido — consulta parametrizada:**
```sql
WHERE ci = ?   ← el payload se trata como texto, nunca como código
```

### En la industria
Top 3 OWASP todos los años. Filtraciones en Yahoo, LinkedIn, Adobe.
Una línea de código insegura puede exponer millones de registros.

### Demo — dos pasos
**Con protección activa:**
```powershell
docker exec attacker bash /scripts/attack_phase4.sh
```
Resultado: 0 registros. SIEM muestra SQLI_BLOCKED.

**Sin protección:**
1. Panel admin → Base de Datos → Desactivar
2. Repetir → se exponen los 3 registros, incluyendo:
   `Token API DTIC-SUNIVER: SK-2024-9f8e7d. SOLO USO INTERNO.`

**Orador:**
> "Con 14 caracteres, sin usuario ni contraseña,
> el atacante obtuvo el token maestro del DTIC.
> La diferencia entre seguro y vulnerable: una sola línea de código."

---

## DIAPOSITIVA 10 — Conclusiones

**Título:** Lo que esta demo demuestra

**4 bullets grandes:**
- Cada capa bloquea un vector distinto — ninguna sobra
- El atacante que pasa el firewall todavía enfrenta 4 controles
- DS5.17 no es burocracia: es código que se escribe y se verifica
- Una línea insegura puede comprometer todo el sistema

**Pregunta de cierre (grande, centrada, en azul):**
> "¿Cuál de estas 4 capas falta en tu sistema?"

**Orador:**
> "Todo lo que vieron corre en una laptop. No requiere infraestructura costosa.
> Lo que requiere es la decisión de implementarlo.
> DS5.17 da el marco. Nosotros demostramos que funciona."

---

## Notas de diseño

- **Capturas reales** del lab en cada slide de demo — el JSON con BLOCKED y el SIEM con ❌ ROTO
- **Tipografía:** títulos ≥ 36pt, bullets ≥ 24pt, analogías en itálica o caja destacada
- **Una idea por slide** — si necesita scroll mental, dividirla
- **Cada slide de demo tiene captura de respaldo** por si algo falla en vivo
- **Transiciones:** fade simple — sin animaciones
