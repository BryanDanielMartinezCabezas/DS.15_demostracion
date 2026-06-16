# DS5.17 — Defensa en Profundidad
# Guion de diapositivas · Estilo conferencia universitaria
# USFX — Universidad San Francisco Xavier de Chuquisaca

---

## SLIDE 1 — Portada

```
[IMAGEN: escudo digital de fondo]

        Defensa en Profundidad
   Control DS5.17 COBIT · USFX 2026

        [Nombre del presentador]
```

> Orador: "Hoy vamos a atacar un sistema universitario en vivo, frente a ustedes.
> Sin trucos. Sin grabaciones. Y vamos a ver exactamente qué lo detiene."

---

## SLIDE 2 — DS5.17 en una frase

```
   ┌─────────────────────────────────────────┐
   │                                         │
   │   "Los mecanismos de seguridad          │
   │    deben protegerse a sí mismos."       │
   │                                         │
   │              — COBIT DS5.17             │
   └─────────────────────────────────────────┘

   No alcanza con tener antivirus.
   Hay que proteger el antivirus.
```

> Orador: "DS5.17 no habla de proteger datos.
> Habla de proteger las herramientas que protegen los datos.
> Es un nivel más adentro."

---

## SLIDE 3 — El sistema objetivo

```
   [CAPTURA: portal SUNIVER — login naranja]

   ¿Qué protegemos?

   · Portal estudiantil USFX
   · Expedientes · Calificaciones · Credenciales DTIC
   · Un atacante dentro de la red puede robar todo
     sin una sola contraseña
```

> Orador: "Este es el sistema que el atacante quiere comprometer.
> El objetivo: expedientes de estudiantes y el token secreto del DTIC."

---

## SLIDE 4 — La metáfora

```
   [IMAGEN: diagrama de capas concéntricas]

   El castillo medieval tenía capas.

        Foso → Muralla → Guardias → Tesoro

   Cada capa asume que la anterior ya fue rota.
```

> Orador: "Si el atacante cruza el foso, todavía enfrenta la muralla.
> Si la rompe, todavía hay guardias adentro.
> Eso es defensa en profundidad."

---

## SLIDE 5 — Las 4 capas

```
   [IMAGEN: kill chain timeline — 4 fases]

   Ataque          →    Control DS5.17
   ─────────────────────────────────────
   Robé tu contraseña   →   MFA · TOTP
   Apago el antivirus   →   Tamper Protection
   Borro las huellas    →   Hash Chain SHA-256
   Robo la base datos   →   Consultas parametrizadas
```

> Orador: "Cuatro intentos del atacante. Cuatro defensas distintas.
> Cada fila es lo que vamos a demostrar ahora."

---

## SLIDE 6 — Fase 1 · MFA

```
   Autenticación Multi-Factor

   Amenaza:   El atacante tiene usuario y contraseña
   Analogía:  Cajero ATM — tarjeta robada + PIN desconocido
   Defensa:   Código TOTP · cambia cada 30 segundos

   [CAPTURA: respuesta JSON "status": "DENEGADO"]

   Resultado: BLOQUEADO
```

> Orador: "El atacante hizo todo bien. Consiguió las credenciales.
> Pero hay un segundo cerrojo que no puede calcular en tiempo real."

---

## SLIDE 7 — Fase 2 · Tamper Protection

```
   Protección del EDR

   Amenaza:   El malware intenta apagar el antivirus
   Analogía:  Sereno con instrucciones escritas del dueño —
              solo obedece órdenes del director en persona
   Defensa:   El EDR rechaza la señal · alerta CRITICAL en SIEM

   [CAPTURA: "status": "BLOCKED" + alerta roja en SIEM]

   Con protección: BLOQUEADO
   Sin protección: el EDR cae
```

> Orador: "El 90% del ransomware real desactiva el antivirus primero.
> Con DS5.17, ese intento queda registrado como evidencia."

---

## SLIDE 8 — Fase 3 · Hash Chain

```
   Integridad de Logs

   Amenaza:   El atacante edita el SIEM para borrar sus huellas
   Analogía:  Libro de actas universitario — páginas numeradas
              y selladas. Arrancás una hoja y los números no cuadran.
   Defensa:   Cada log lleva el hash del anterior (SHA-256)
              Modificar uno rompe toda la cadena

   [CAPTURA: dashboard SIEM con ❌ ROTO en rojo]

   Resultado: DETECTADO
```

> Orador: "El atacante cambió el texto del log.
> Pero no puede cambiar el hash sin que se note."

---

## SLIDE 9 — Fase 4 · Inyección SQL

```
   Protección de la Base de Datos

   Amenaza:   Robar todos los expedientes sin contraseña
   Analogía:  Ventanilla de matrículas — te piden tu CI
              pero vos escribís un comando completo
   Defensa:   Consultas parametrizadas — el motor trata
              el input del atacante como texto, nunca como código

   Con protección: 0 resultados
   Sin protección: token secreto DTIC expuesto

   [CAPTURA: comparación lado a lado]

   Resultado: NEUTRALIZADO
```

> Orador: "Con 14 caracteres, sin usuario ni contraseña,
> el atacante obtuvo el token maestro del DTIC.
> La diferencia: una sola línea de código."

---

## SLIDE 10 — Conclusión

```
   Lo que esta demo demuestra

   · Cada capa bloquea un vector distinto — ninguna sobra
   · El atacante que pasa el firewall aún enfrenta 4 controles
   · DS5.17 no es burocracia: es código que se prueba

   ┌─────────────────────────────────────────┐
   │                                         │
   │   ¿Cuál de estas 4 capas               │
   │   falta en tu sistema?                  │
   │                                         │
   └─────────────────────────────────────────┘
```

> Orador: "Todo lo que vieron corre en una laptop.
> No requiere infraestructura costosa.
> Lo que requiere es la decisión de implementarlo."

---

## Capturas necesarias para las slides

| Slide | Captura |
|-------|---------|
| 3 | Portal SUNIVER — pantalla de login |
| 6 | Terminal con `"status": "DENEGADO"` |
| 7 | Terminal con `"BLOCKED"` + SIEM con alerta roja |
| 8 | SIEM con fila marcada ❌ ROTO |
| 9 | Dos terminales: protegido (0 resultados) vs. desprotegido (token expuesto) |
