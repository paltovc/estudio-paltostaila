# Diseño local: funciones tipo Canva hechas en el estudio (diseno.py)

Lo que Canva hace bien para miniaturas, portadas y piezas para redes, hecho con código propio y licencias abiertas.

**Aprender de Canva sí; copiarlo no.** Se puede mirar qué funciones ofrece Canva (su ayuda y sus guías son públicas), usarlo como cualquier usuario, entender por qué un diseño funciona y hacer nuestra propia versión: las ideas y las funciones no se copian, se aprenden. Lo que no se hace es desarmar su software, extraer su contenido de forma automática, ni usar el conector para sacar sus plantillas, kits o la estructura de sus diseños y replicarlos aquí. Tampoco se usan sus elementos, fotos o fuentes con licencia fuera de Canva.

**No es ingeniería inversa de Canva:** sus términos prohíben copiar, descompilar o replicar su servicio, y su conector prohíbe sacar plantillas, kits o la estructura de los diseños para usarlos fuera de Canva. Aquí todo es de autoría propia: el kit de marca, las plantillas y los efectos.

## Qué hace cada parte
| Función | Cómo | Comando |
|---|---|---|
| Kit de marca | `canales\<canal>\marca.json`: colores por papel (texto, acento, acento2, borde, fondo, alerta), fuentes (titulo, texto, mano) y logo propio | `python diseno.py marca finanzas` (crea uno base si no existe) |
| Plantillas con campos (autofill local) | JSON con capas: imagen, texto, forma, logo; campos `{{titulo}}`, `{{imagen}}`, `{{sello}}`; capa opcional con `"si": "sello"` | `python diseno.py plantilla miniatura-lado --base <carpeta imágenes> --campo imagen=FIN-003_img-012.png --campo "titulo=¿Me lo\nvoy a perder?" --campo sello=FOMO --salida <proyecto>\08_PUBLICAR\miniatura-1.png` |
| Efectos de texto | `efecto`: contorno, sombra, elevar (`intensidad`), hueco (`grosor`), empalme (hueco + copia desplazada en `color2`), eco (dos copias detrás), glitch (`color_glitch1`, `color_glitch2`), neon, degradado (`color` → `color2`), curva (`radio_curva`), caja (`fondo`); `direccion` y `desplazamiento` para eco, glitch y empalme; `color_ultima` pinta la última línea; el tamaño se ajusta solo al ancho y al máximo de líneas | en la plantilla |
| Imágenes | `ajuste`: cubrir, contener, inteligente (busca el sujeto), relleno (completa sobre fondo desenfocado); `mascara`: circulo, redondeado; `marco`; `sombra` | en la plantilla |
| Formas | rect (con `radio`), circulo (`solo_borde` para resaltar), flecha, degradado (oscurece un lado para que el texto se lea) | en la plantilla |
| Redimensionar (tipo Magic Resize) | recorte inteligente o relleno a 16x9, 9x16, 1x1, 4x5 | `python diseno.py redimensionar imagen.jpg --formatos 16x9,9x16,1x1 [--modo relleno]` |
| Mismo diseño en otros formatos | `--formatos 9x16,1x1` en `plantilla`: recompone (fondo a pantalla completa, textos centrados en la zona segura). Revisar siempre: no sabe dónde está la cara; para Shorts es mejor `portada-short` | en `plantilla` |
| Vista en el celular | cada plantilla deja también `<nombre>_160px.png` (como se ve en la lista de YouTube): el texto tiene que leerse ahí | automático |
| Revisión de legibilidad | al armar, `<nombre>_revision.txt`: palabras (más de 6 = aviso), fuentes (más de 2 = aviso), jerarquía (el título ~2 veces el texto secundario), tamaño en el celular (menos de 8 px a 160 de ancho = no se lee), contraste con el fondo (mínimo 3:1, fórmula de accesibilidad WCAG, salvo que lleve contorno o caja) y zona segura en verticales | automático |
| Quitar fondo | `"sin_fondo": true` en una capa de imagen, con rembg y el modelo `isnet-general-use` (uso comercial permitido). **Nunca** el modelo por defecto `bria-rmbg` ni RMBG-2.0 (licencia no comercial) | instalado en el PC de Patricio (rembg con el modelo isnet-general-use, 179 MB en `%USERPROFILE%\.u2net`). En otro PC: `pip install "rembg[cpu]"` con permiso. Funciona mejor con un solo sujeto sobre fondo simple; en escenas con varios objetos puede dejar restos (puertas, muebles). Alternativa: `remove-background` del conector de Canva |

Kit del canal de finanzas (`canales\finanzas\marca.json`): sacado de las miniaturas propias de FIN-002 con `receta_miniatura.py` — fondo azul oscuro `#112F65`, texto blanco con contorno `#0A162D`, última línea en verde `#6AD15B`, amarillo `#FFD23F` de segundo acento. Usar `--canal finanzas`. Cada canal nuevo saca su kit igual: medir sus miniaturas propias (o las que ustedes hicieron en Canva, exportadas como imagen) y anotar los colores; nunca se copian kits de Canva.

Plantillas incluidas (en `motor\plantillas`): `miniatura-lado` (imagen completa, franja oscura y texto a un lado), `miniatura-centro` (personaje en marco sobre color de marca, texto arriba), `portada-short` (9:16 con el texto dentro de la zona segura). Para un canal nuevo: copiar una, cambiarle nombre y ajustar posiciones; los colores salen del kit de marca.

## Qué sigue en Canva (con el conector oficial)
- Lo que ya vive allá: el tablero de ideas y las miniaturas de la pareja. Se trabaja siempre en una **copia**.
- Plantillas de marca con autofill y `resize-design`: solo con cuenta Pro o superior.
- Relleno generativo tipo Magic Expand: en el editor de Canva (o regenerar la imagen en el formato correcto).
- Cada persona usa su propia cuenta: si Patricio edita diseños de la pareja, que ella lo invite a su equipo; no usar su inicio de sesión.

## Qué no se hace
- Leer plantillas o kits de Canva con el conector para copiarlos aquí.
- Automatizar el sitio de Canva con el navegador, usar cookies o contraseñas.
- Instalar un clon completo de Canva (Doory, Penpot): pesados y no hacen falta.
