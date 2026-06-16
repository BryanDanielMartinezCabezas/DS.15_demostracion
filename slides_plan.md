# Brief para generación de presentación — DS5.17 COBIT
# Instrucciones para NotebookLM

Genera una presentación de 10 diapositivas sobre el control COBIT DS5.17
"Defensa en Profundidad" para una conferencia universitaria en la USFX Bolivia.
Paleta oscura: fondo #0d1117, texto blanco, azul #58a6ff, verde #3fb950, rojo #f85149.
Tipografía grande. Mínimo texto visible. El orador habla el resto.

---

## SLIDE 1 — Portada

Título principal: **Defensa en Profundidad**
Subtítulo: **Control DS5.17 COBIT · USFX 2026**
Pie de página: nombre del presentador y fecha.
Imagen de fondo: escudo digital con circuitos (ya proporcionada).

---

## SLIDE 2 — El control DS5.17

Muestra esta cita centrada en pantalla, tipografía grande, como elemento principal:

> "Los mecanismos de seguridad deben protegerse a sí mismos."
> — COBIT DS5.17

Debajo, tres bullets cortos:
- No alcanza con tener antivirus — hay que proteger el antivirus
- No alcanza con tener logs — hay que garantizar que no se falsifiquen
- No alcanza con tener base de datos — hay que proteger cómo se consulta

---

## SLIDE 3 — El sistema objetivo

Título: **¿Qué estamos protegiendo?**
Imagen: captura del portal SUNIVER (login con topbar naranja).

Tres bullets:
- Portal estudiantil USFX — expedientes, calificaciones, matrículas
- Administrado por el DTIC — contiene credenciales de acceso interno
- Un atacante dentro de la red puede robar todo sin contraseña

---

## SLIDE 4 — La metáfora de las capas

Título: **El castillo medieval tenía capas**
Imagen central: diagrama de capas concéntricas (ya proporcionada).

Analogía a mostrar en pantalla:
- Foso → Firewall
- Muralla → Autenticación MFA
- Torre de guardia → Antivirus / EDR
- Cámara del tesoro → Base de datos

Frase destacada al pie: **"Cada capa asume que la anterior ya fue comprometida."**

---

## SLIDE 5 — Mapa de los 4 controles

Título: **4 ataques · 4 controles**
Imagen: diagrama kill chain horizontal con las 4 fases (ya proporcionada).

Tabla de dos columnas:

| El ataque | El control DS5.17 |
|-----------|-------------------|
| Robé tu contraseña | MFA — código TOTP cada 30 s |
| Apago el antivirus | Tamper Protection — el EDR se protege a sí mismo |
| Borro las huellas | Hash Chain SHA-256 — cadena de evidencia incorruptible |
| Robo la base de datos | Consultas parametrizadas — el motor ignora código del atacante |

---

## SLIDE 6 — Fase 1: Autenticación MFA

Título: **"Tengo tu contraseña. ¿Y ahora?"**

Estructura de la diapositiva en tres bloques:

**Amenaza:** El atacante obtuvo usuario y contraseña por phishing o filtración.
Con solo eso debería poder entrar al panel de control del sistema.

**Analogía:** Como un cajero automático — tener la tarjeta robada no alcanza.
También necesitás el PIN. El atacante tiene la tarjeta, no sabe el PIN.

**Defensa:** Código TOTP generado por algoritmo matemático usando un secreto
compartido más la hora actual. Cambia cada 30 segundos.
Sin el secreto físico, es imposible calcularlo.

Captura a insertar: terminal mostrando `"status": "DENEGADO"`.
Etiqueta en verde: **BLOQUEADO ✓**

---

## SLIDE 7 — Fase 2: Tamper Protection

Título: **"Lo primero: apagar el antivirus"**

Estructura en tres bloques:

**Amenaza:** El 90% del ransomware real desactiva el antivirus antes de ejecutarse.
Si el EDR cae, el atacante puede actuar sin ser detectado.

**Analogía:** Como un sereno con instrucciones escritas del dueño:
"Solo obedecé órdenes de apagado si el director viene en persona con su CI."
Cualquier llamada por teléfono diciendo "soy el jefe, andate" — ignorada.

**Defensa:** El EDR rechaza la señal de apagado cuando está protegido.
Registra el intento como alerta CRITICAL en el SIEM automáticamente.

Captura a insertar: `"status": "BLOCKED"` en terminal + alerta roja en SIEM.
Mostrar contraste: con protección → BLOQUEADO / sin protección → el EDR cae.

---

## SLIDE 8 — Fase 3: Integridad de Logs

Título: **"Ya entré. Ahora borro las huellas."**

Estructura en tres bloques:

**Amenaza:** El atacante edita el registro del SIEM para eliminar evidencia
de su intrusión. La investigación forense posterior no encontraría nada.

**Analogía:** Como el libro de actas de la universidad — páginas numeradas
y selladas en cadena. Si arrancás una hoja, los números no cuadran.
Si cambiás algo en una página, el sello de la siguiente ya no coincide.

**Defensa:** Cada log contiene el hash SHA-256 del log anterior.
Modificar cualquier registro sin recalcular toda la cadena es detectable
de forma automática e instantánea.

Captura a insertar: dashboard SIEM con fila marcada ❌ ROTO en rojo
y barra superior "INTEGRIDAD COMPROMETIDA".
Etiqueta: **DETECTADO ✓**

---

## SLIDE 9 — Fase 4: Anti-Inyección SQL

Título: **"No necesito contraseña. Solo sé hablar SQL."**

Estructura en tres bloques:

**Amenaza:** El atacante tiene acceso a la red interna y consulta la base
de datos directamente. Sin usuario, sin contraseña, solo un payload de 14 caracteres
que hace devolver todos los registros — incluyendo el token secreto del DTIC.

**Analogía:** En la ventanilla de matrículas te piden tu CI.
Vos escribís: `7559063' O devolveme todos los registros --`
Una ventanilla inteligente solo acepta números de CI.
Una ventanilla descuidada ejecuta lo que escribiste como instrucción.

**Defensa:** Consultas parametrizadas — el motor de base de datos trata
el input del atacante como texto puro, nunca como código SQL ejecutable.
El payload se busca literalmente: no existe como CI → 0 resultados.

Captura a insertar: dos resultados lado a lado —
izquierda (protegido): 0 resultados / derecha (sin protección): token DTIC expuesto.
Etiqueta: **NEUTRALIZADO ✓**

---

## SLIDE 10 — Conclusión

Título: **Lo que esta demo demuestra**

Cuatro bullets finales:
- Cada capa bloquea un vector distinto — ninguna sobra
- El atacante que pasa el firewall todavía enfrenta 4 controles internos
- DS5.17 no es burocracia: es código que se escribe, se prueba y se verifica
- Una línea de código insegura puede exponer todo el sistema

Frase de cierre centrada y destacada:

> "¿Cuál de estas 4 capas falta en tu sistema?"

Pie: agradecimiento + espacio para preguntas.
