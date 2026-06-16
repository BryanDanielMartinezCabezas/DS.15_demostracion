# Guion de Diapositivas — Demo DS5.17 COBIT: Defensa en Profundidad
# USFX — Universidad San Francisco Xavier de Chuquisaca

> Presentación de 15 minutos. Una idea por diapositiva. Texto grande, pocas palabras.
> Paleta: fondo `#0d1117`, azul `#58a6ff`, verde `#3fb950`, rojo `#f85149`, amarillo `#d29922`.
> Sin diapositiva de agenda separada.

---

## DIAPOSITIVA 1 — Portada

**Título grande:** Defensa en Profundidad
**Subtítulo:** Control DS5.17 COBIT — Protección de las Funciones de Seguridad
**Pie:** Nombre del presentador · USFX · Fecha

**Orador:**
> "Hoy no vamos a hablar de seguridad en teoría.
> Vamos a atacar un sistema universitario real — frente a ustedes —
> y ver exactamente qué lo detiene."

---

## DIAPOSITIVA 2 — ¿Qué dice DS5.17?

**Título:** COBIT DS5.17
**Subtítulo:** Protección de las Funciones de Seguridad

**Definición (una sola frase grande):**
> "Los propios mecanismos de seguridad deben estar protegidos contra manipulación, desactivación o evasión."

**Tres bullets debajo:**
- No alcanza con tener un antivirus — hay que proteger el antivirus
- No alcanza con tener logs — hay que garantizar que no se puedan falsificar
- No alcanza con tener una base de datos — hay que proteger cómo se consulta

**Orador:**
> "DS5.17 no habla de proteger datos. Habla de proteger las herramientas
> que protegen los datos. Es un nivel más adentro."

---

## DIAPOSITIVA 3 — El sistema objetivo: SUNIVER

**Título:** ¿Qué estamos protegiendo?

**Imagen grande:** captura del portal SUNIVER (login naranja)

**Tres bullets:**
- Portal estudiantil de la USFX — expedientes, calificaciones, datos universitarios
- Sistema administrado por el DTIC — incluye credenciales de acceso interno
- Un atacante con acceso a la red interna puede comprometer todo

**Orador:**
> "Este es el sistema real de la USFX, replicado para la demo.
> Lo que el atacante quiere: los expedientes de los estudiantes
> y el token secreto del DTIC que da acceso a toda la infraestructura."

---

## DIAPOSITIVA 4 — La metáfora: el castillo medieval

**Título:** ¿Por qué una sola defensa no basta?

**Imagen o diagrama:** castillo con capas — foso, muralla, torre, cámara del tesoro

**Una grieta en la muralla no significa que el tesoro está expuesto.
Hay más capas adentro.**

**Columna izquierda — Castillo:**
- Foso
- Muralla exterior
- Torre de guardia
- Cámara del tesoro

**Columna derecha — Sistema digital:**
- Firewall
- Autenticación (MFA)
- Antivirus / EDR
- Base de datos

**Orador:**
> "Un atacante que rompe el firewall todavía enfrenta la autenticación.
> Si la rompe, todavía enfrenta el EDR. Si lo desactiva, todavía enfrenta
> la integridad de logs. Cada capa supone que la anterior ya fue comprometida."

---

## DIAPOSITIVA 5 — Las 4 capas: mapa general

**Título:** 4 controles DS5.17 en este laboratorio

**Tabla (grande, con íconos):**

| # | Control | Mecanismo | Qué protege |
|---|---------|-----------|-------------|
| 1 | Autenticación MFA | TOTP — código cada 30 s | Acceso al panel de seguridad |
| 2 | Tamper Protection | EDR rechaza señal de apagado | El propio antivirus |
| 3 | Integridad de logs | Hash chain SHA-256 | La evidencia forense |
| 4 | Anti-inyección SQL | Consultas parametrizadas | La base de datos de estudiantes |

**Orador:**
> "Esta tabla es el mapa de todo lo que vamos a ver.
> Cada fila es un ataque distinto — y una defensa distinta.
> Volvamos a ella mentalmente en cada fase."

---

## DIAPOSITIVA 6 — FASE 1: Autenticación MFA

### La amenaza
**Título:** "Tengo tu contraseña. ¿Ahora qué?"

El atacante obtiene las credenciales del administrador (phishing, filtración, fuerza bruta).
Con solo usuario + contraseña debería poder entrar al panel de control.

### El mecanismo
**TOTP — Time-based One-Time Password**

- Hay un secreto compartido entre el servidor y tu teléfono
- Ese secreto + la hora actual → algoritmo matemático → código de 6 dígitos
- Cambia cada 30 segundos
- Sin el secreto físico, es imposible calcular el código

**Analogía:** Es como una cerradura que cambia de combinación cada 30 segundos.
Tener la llave vieja no sirve.

### En la industria
Bancos, GitHub, Gmail, sistemas hospitalarios, cualquier acceso administrativo crítico.
Es el estándar mínimo de seguridad para 2024.

### Demo en vivo
```
docker exec attacker bash /scripts/attack_phase1.sh
```
**Resultado esperado:** `"status": "DENEGADO"` — el atacante tiene usuario y contraseña
correctos pero no el código TOTP. El acceso es rechazado.

**Orador:**
> "El atacante hizo todo bien. Consiguió las credenciales.
> Pero hay un segundo cerrojo que no puede romper en tiempo real."

---

## DIAPOSITIVA 7 — FASE 2: Tamper Protection (EDR)

### La amenaza
**Título:** "Lo primero que hace el malware: apagar el antivirus"

En el 90% de los ataques ransomware documentados, el malware desactiva
el antivirus antes de ejecutar su payload. Si el EDR cae, el atacante
puede hacer lo que quiera sin ser detectado.

### El mecanismo
**Tamper Protection — el guardián que se protege a sí mismo**

- El EDR tiene una variable de estado: `PROTECTED = True`
- Cuando recibe la señal de apagado, pregunta: ¿estoy protegido?
- Si sí → rechaza la señal, registra el intento como CRITICAL en el SIEM
- Si no → se apaga (esto se demuestra desactivando desde el panel admin)

**Analogía:** Un guardia de seguridad que tiene instrucciones de no obedecer
órdenes de apagado a menos que vengan firmadas por el director.

### En la industria
Windows Defender, CrowdStrike, SentinelOne — todos tienen tamper protection
activada por defecto. Es una característica obligatoria en cualquier EDR moderno.

### Demo en vivo — dos pasos
**Paso A (defensa activa):**
```
docker exec attacker bash /scripts/attack_phase2.sh
```
Resultado: `"status": "BLOCKED"` + alerta CRITICAL en SIEM

**Paso B (sin protección):**
1. Panel admin → Desactivar Tamper Protection
2. Repetir el script
3. Resultado: el contenedor `victim` cae — el EDR muere

**Orador:**
> "Primero lo vemos bloqueado. Luego desactivo la protección
> para mostrar qué pasaría sin DS5.17. El EDR simplemente desaparece."

---

## DIAPOSITIVA 8 — FASE 3: Integridad de Logs (Hash Chain)

### La amenaza
**Título:** "Entré, hice el daño, ahora borro las huellas"

El atacante ya está dentro del sistema. Si puede editar los logs del SIEM,
puede eliminar la evidencia de su intrusión. La investigación forense
posterior no encontraría nada.

### El mecanismo
**Hash Chain SHA-256 — la cadena de evidencia incorruptible**

Cada registro de log tiene un sello matemático (hash) que depende del
contenido del registro anterior. Es como una cadena de bloques.

```
Log 1: "Inicio"    → hash_1 = A7F3...
Log 2: "Ataque"    → hash_2 = B9C1... (calculado con hash_1)
Log 3: "Heartbeat" → hash_3 = D4E2... (calculado con hash_2)
```

Si alguien modifica el Log 2 sin recalcular los hashes, la cadena
desde ese punto queda inválida. El sistema lo detecta automáticamente.

**Analogía:** Actas notariales donde cada página tiene el sello
que incluye el contenido de la página anterior. Arrancar una página
invalida todo el cuaderno.

### En la industria
SIEM empresariales (Splunk, IBM QRadar), blockchain forense,
registros de auditoría bancaria. Cualquier sistema donde la
evidencia deba ser admisible en juicio.

### Demo en vivo
```
docker exec attacker bash /scripts/attack_phase3.sh
```
**Resultado:** El dashboard SIEM muestra el registro modificado
con ❌ ROTO en rojo. La barra superior cambia a "INTEGRIDAD COMPROMETIDA".

**Orador:**
> "El atacante cambió el mensaje. Pero no puede cambiar el hash
> sin que se note. Y no puede recalcular toda la cadena
> porque necesitaría reescribir el historial completo."

---

## DIAPOSITIVA 9 — FASE 4: Anti-Inyección SQL

### La amenaza
**Título:** "La base de datos habla SQL. Yo también."

El atacante tiene acceso a la red interna. No necesita credenciales
para hablar con la base de datos directamente. Puede enviar
comandos SQL disfrazados de búsquedas normales.

**El payload:**
```
ci = ' OR '1'='1
```
Convierte una búsqueda normal en:
```sql
SELECT * FROM estudiantes WHERE ci = '' OR '1'='1'
```
`'1'='1'` siempre es verdadero → devuelve TODOS los registros.

### El mecanismo
**Consultas parametrizadas — el intérprete que no ejecuta texto del usuario**

```python
# VULNERABLE — concatenación directa:
query = f"SELECT * FROM estudiantes WHERE ci = '{ci}'"

# SEGURO — consulta parametrizada:
cursor.execute("SELECT * FROM estudiantes WHERE ci = ?", (ci,))
```

Con el `?`, el motor SQLite trata el valor del usuario como
**texto puro**, nunca como código SQL. El payload del atacante
se busca literalmente como CI — no existe — devuelve 0 resultados.

**Analogía:** La diferencia entre darle a alguien un formulario
para completar (parametrizado) versus dejarle escribir
el documento completo (concatenación).

### En la industria
Inyección SQL sigue en el Top 3 de OWASP todos los años.
Filtraciones masivas en Yahoo, LinkedIn, Adobe usaron SQLi.
Prepared statements son la solución estándar desde hace 20 años
y sigue sin implementarse en muchos sistemas.

### Demo en vivo — dos pasos
**Paso A (protección activa):**
```
docker exec attacker bash /scripts/attack_phase4.sh
```
Resultado: 0 registros devueltos. El SIEM registra SQLI_BLOCKED.

**Paso B (sin protección):**
1. Panel admin → Base de Datos → Desactivar protección
2. Repetir el script
3. Resultado: 3 registros expuestos, incluyendo:
   `"Token API DTIC-SUNIVER: SK-2024-9f8e7d. SOLO USO INTERNO."`

**Orador:**
> "Con un solo payload de 14 caracteres, sin usuario ni contraseña,
> el atacante obtuvo el token maestro del DTIC.
> La diferencia entre seguro y vulnerable es una sola línea de código."

---

## DIAPOSITIVA 10 — Conclusiones

**Título:** Lo que esta demo realmente demuestra

**4 bullets grandes:**
- Cada capa bloquea un vector distinto — ninguna es redundante
- El atacante que pasa el firewall todavía enfrenta 4 controles internos
- DS5.17 no es teoría: es código que se escribe, se prueba y se verifica
- Una sola línea de código insegura (SQLi) puede comprometer todo el sistema

**Pregunta de cierre (grande, centrada):**
> "¿Cuál de estas 4 capas falta en tu sistema?"

**Pie:** Gracias · Preguntas · [link al repositorio si aplica]

**Orador:**
> "Esto no requiere infraestructura costosa ni herramientas empresariales.
> Todo lo que vieron corre en una laptop. Lo que requiere es la decisión
> de implementarlo. DS5.17 da el marco. Ustedes dan la implementación."

---

## Notas de diseño

- Capturas reales del lab en cada diapositiva de demo (las del SIEM y terminal)
- Tipografía: títulos ≥ 36pt, bullets ≥ 24pt
- Una sola idea visual por diapositiva
- Cada diapositiva de demo tiene captura de respaldo por si algo falla en vivo
- Transiciones: fade simple, sin animaciones
