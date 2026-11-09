# Ronda 0: estrategia al empezar un canal, una serie o un proyecto

Va **antes** de la entrevista por video del estudio (`entrevista.md` del arquitecto). Se pregunta con la herramienta de preguntas con opciones, máximo 4 por vez y 2 rondas. Se salta lo que ya está en `canales\<canal>\ESTRATEGIA.md` o en la biblia del canal. Si la persona dice «decide tú», se toma el valor por defecto y se anota como supuesto.

## Ronda A: qué y para quién

1. **Para qué es este canal o proyecto** (selección múltiple): crecer en audiencia / monetizar YouTube / vender un producto o servicio propio / marca personal / proyecto artístico (música). Por defecto: lo que diga la biblia.
2. **Mercados** (selección múltiple): Chile / resto de Latinoamérica / España / EE. UU. hispano / Oceanía (en inglés) / Brasil (portugués). Hay que explicar que monetizar depende del país donde viven ellos y no del público (`mercados.md`).
3. **Ritmo que pueden sostener:** 1 video largo por semana más 3 Shorts / 1 largo cada 2 semanas más 2 Shorts / solo Shorts (3 a 5 por semana) / otro. Hay que avisar que publicar más no compensa si los videos se parecen demasiado (política de contenido no auténtico).
4. **Nivel de autonomía para publicar:** 2 (aprueban y Claude programa; recomendado) / 1 (Claude sube privado) / 0 (ellos suben).

## Ronda B: según lo respondido

- **Fuentes de ingreso esperadas:** anuncios de YouTube / afiliados / patrocinios / producto propio / regalos y suscripciones. Ojo: un afiliado o patrocinio de finanzas para público australiano choca con ASIC.
- **Límites:** temas que no se tocan, qué no se promete, si aparecen personas reales o menores.
- **Quién aprueba** cada publicación (Patricio, su pareja o cualquiera de los dos).
- **Voz:** la actual, una con licencia comercial o la propia.
- **Presupuesto:** ¿Metricool gratis (20 publicaciones al mes) o pago? ¿Créditos de vidIQ por mes?

## Lo que se entrega

`canales\<canal>\ESTRATEGIA.md`, un archivo nuevo. Si ya existe, va como `ESTRATEGIA_v2.md`:

```markdown
# Estrategia — <canal o serie>
Fecha: · Aprobó: · Revisar el: <fecha + 90 días>
- Objetivo y por qué:
- Mercados e idioma:
- Ritmo: (largos/semana, Shorts/semana, redes por pieza)
- Nivel de autonomía:
- Metas a 90 días (medibles): suscriptores, horas de visualización, vistas de Shorts, seguidores en TikTok e Instagram
- Fuentes de ingreso y cuándo se activan:
- Límites y reglas de contenido (incluidas las de país, p. ej. ASIC):
- Quién aprueba:
- Presupuesto (Metricool, vidIQ, otros):
- Supuestos (lo que se decidió por defecto):
```

Con eso se arma el calendario base de 4 semanas: fechas tentativas y estado `por_aprobar`, que el calendario solo recibe cuando existe el `publicacion.json`. Hasta entonces el plan queda escrito en la estrategia.
