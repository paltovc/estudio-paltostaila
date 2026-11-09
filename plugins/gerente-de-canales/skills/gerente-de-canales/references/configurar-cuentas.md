# Configurar las cuentas (una sola vez)

Lo hace Patricio con sus cuentas; Claude lo guía. Ninguna contraseña pasa por el chat. Cada paso que abre el navegador se avisa antes, y lo personal va en Chrome.

## A. YouTube: API propia (gratis)

1. En Chrome, entrar a console.cloud.google.com con la cuenta dueña del canal y crear un proyecto llamado `estudio-paltostaila`.
2. En **APIs y servicios → Biblioteca**, habilitar **YouTube Data API v3** y **YouTube Analytics API**.
3. En **Google Auth Platform** (pantalla de consentimiento OAuth):
   - tipo **Externo**, nombre de la app «Estudio Palto Style» y su correo;
   - en **Público / Audiencia**, apretar **Publicar app** para pasarla a «En producción». En modo «Prueba» el permiso vence cada 7 días;
   - no hace falta pedir la verificación de Google. Al autorizar aparecerá el aviso «Google no verificó esta app»: entrar en *Configuración avanzada → Ir a Estudio Palto Style*. Es una app propia, para su propio canal.
4. En **Clientes** (Credenciales), crear un **ID de cliente OAuth** de tipo **App de escritorio**, descargar el JSON y guardarlo como `EstudioPaltostaila\claves\youtube_cliente.json`. No se pega en el chat.
5. Claude corre `python yt_api.py autorizar`. Se abre el navegador una vez: elegir la cuenta y el canal y aceptar 4 permisos:
   - subir videos;
   - **administrar la cuenta de YouTube**: este permiso lo exigen los subtítulos, y técnicamente también permite editar y borrar videos y comentarios. El gerente no lo usa para eso: sus scripts solo suben, ponen miniaturas, subtítulos y listas, y quitan una fecha de publicación con el sí de Patricio;
   - ver la cuenta de YouTube (solo lectura: comprobar el canal y si un video ya es público);
   - ver estadísticas.
   Queda `claves\youtube_token.json`. Ese archivo es una llave del canal: no se copia, no se sube al repositorio ni se comparte.
6. Claude corre `python yt_api.py canal` y le muestra a Patricio el nombre y el id del canal. Solo si él dice que es el correcto, Claude corre `python yt_api.py canal --confirmar`, que lo fija en `config.json`. Sin ese paso no se sube nada, y si después se conecta otro canal, las subidas se detienen.
7. Verificar el canal por teléfono en youtube.com/verify: lo piden las miniaturas personalizadas y los videos de más de 15 minutos.

Para quitar el permiso más adelante: myaccount.google.com → Seguridad → Apps de terceros → Estudio Palto Style → Quitar acceso.

## B. Metricool: TikTok e Instagram (plan gratis: 20 publicaciones al mes)

1. Entrar a app.metricool.com/brands/connections?blogId=7952517 (la marca del estudio).
2. Conectar **TikTok** y **Instagram**. Instagram tiene que ser una cuenta profesional (Creador o Empresa) y se conecta con el inicio de sesión de Instagram.
3. YouTube se puede conectar ahí solo para ver la analítica junto a las demás redes: ver no gasta publicaciones; publicar sí.
4. Opcional: vincular Google Drive en Metricool, si el plan lo permite, para que tome los Shorts directo desde Drive.
5. Claude confirma con `getBrandSettings` que aparecen las redes.

## C. vidIQ (plan gratis: 150 créditos al mes)

1. Conectar el canal de YouTube (para la analítica) y, si se quiere publicar Reels desde YouTube, también Instagram.
2. Fijar en `gerente\config.json` → `vidiq.creditos_mes_autorizados` cuántos créditos puede usar Claude por mes sin preguntar. Hoy es 0, así que pregunta cada vez.

## D. Carpeta de Drive para los Shorts (si TikTok e Instagram van por Metricool)

Crear en Google Drive la carpeta `EstudioPaltostaila_publicar`, compartida como «cualquier persona con el enlace puede ver». Ahí van solo las piezas aprobadas: quien tenga el enlace puede verlas antes de que se publiquen.

## E. Instalar el gerente en el PC

`instalar_gerente.cmd`:
- copia los scripts a `EstudioPaltostaila\gerente`;
- instala `google-api-python-client`, `google-auth-oauthlib` y `tzdata`;
- corre `prueba_gerente.py`, que tiene que terminar en «PRUEBA SUPERADA».
