---
name: analizar-referente
description: Analiza uno o varios videos de YouTube, TikTok o Instagram a partir de su enlace para explicar por qué funcionan (números frente a su canal, empaque, gancho, estructura, ritmo, comentarios) y cómo aplicarlo al video o canal propio, con guion o cambios propuestos. Usar cuando se pegue un enlace de video y se pregunte por qué le fue bien, "analiza este video", "mira este TikTok", "qué hace este canal", "compara estos videos", o para minar comentarios de los videos propios.
---

# Analizar un referente

1. Con computador vinculado: lanzar al agente **analista-de-referentes** con los enlaces, el canal propio y, si existe, la carpeta del video en curso (para proponer cambios a su guion). Varios enlaces → un agente por enlace en paralelo y después una comparación.
2. El agente usa `referente.py` del motor (`%USERPROFILE%\EstudioPaltostaila\motor`), en segundo plano con log. Solo datos y comentarios (rápido): `--sin-video`.
3. Sin computador vinculado: con WebFetch o búsqueda se puede leer título, descripción y a veces cifras; decir que el análisis de imagen, ritmo y comentarios necesita el PC, y ofrecerlo.
4. Instagram o TikTok bloqueados: no usar contraseñas ni cookies. Pedir el video descargado o una grabación de pantalla y capturas de los comentarios, y analizar eso.
5. Minería de comentarios propios (mensual): `referente.py <enlace> --sin-video` sobre los últimos videos del canal; agrupar preguntas repetidas y convertirlas en ideas.

Entrega: `referentes\<carpeta>\analisis.md` con por qué funciona (con evidencia), cómo aplicarlo respetando la biblia del canal, guion o cambios propuestos, y qué necesita de la persona. Resumir en el chat las 3 ideas más útiles y el enlace al archivo. El material del referente nunca se reutiliza en videos propios.
