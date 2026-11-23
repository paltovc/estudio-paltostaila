# Estudio Paltostaila

Herramientas para crear, revisar y publicar videos con Claude.

- **arquitecto-de-video**: el estudio que hace los videos (investigación, guion, imágenes, clips, voz, subtítulos, sala de edición, evaluador, juez y paquete para YouTube, TikTok e Instagram). Detalle en [plugins/arquitecto-de-video/README.md](plugins/arquitecto-de-video/README.md).
- **gerente-de-canales**: el que publica y sigue los canales (calendario, aprobación, subida a YouTube, TikTok e Instagram, métricas). Detalle en [plugins/gerente-de-canales/README.md](plugins/gerente-de-canales/README.md).

## Instalar en la app de Claude (escritorio)

1. Abre **Customize → Plugins**.
2. En **Personal plugins**, aprieta **+** → **Add marketplace** → **Add from a repository**.
3. Escribe `paltovc/estudio-paltostaila` y confirma.
4. Instala **arquitecto-de-video** y **gerente-de-canales**.
5. En una conversación con tu computador vinculado escribe: **instala el estudio**.

## Actualizar

1. **Customize → Plugins** → en la tienda `estudio-paltostaila`, aprieta **Update**.
2. En una conversación con tu computador vinculado escribe: **actualiza el motor**.
3. Para comprobar, pregunta: **¿qué versión del arquitecto y del gerente tengo?**

## Claude Code (terminal)

```
/plugin marketplace add paltovc/estudio-paltostaila
/plugin install arquitecto-de-video@estudio-paltostaila
/plugin install gerente-de-canales@estudio-paltostaila
```
Actualizar: `/plugin marketplace update estudio-paltostaila`.

Las claves (YouTube, Metricool) no vienen en este repositorio: cada persona guarda las suyas en `EstudioPaltostaila\claves\` de su propio computador.

Licencia MIT.
