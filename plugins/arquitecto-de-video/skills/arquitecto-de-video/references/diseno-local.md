# Diseño local: funciones tipo Canva hechas en el estudio (diseno.py)

Lo que Canva hace bien para miniaturas, portadas y piezas para redes, hecho con código propio y licencias abiertas. **No es ingeniería inversa de Canva:** sus términos prohíben copiar, descompilar o replicar su servicio, y su conector prohíbe sacar plantillas, kits o la estructura de los diseños para usarlos fuera de Canva. Aquí todo es de autoría propia: el kit de marca, las plantillas y los efectos.

## Qué hace cada parte
| Función | Cómo | Comando |
|---|---|---|
| Kit de marca | `canales\<canal>\marca.json`: colores por papel (texto, acento, acento2, borde, fondo, alerta), fuentes (titulo, texto, mano) y logo propio | `python diseno.py marca finanzas` (crea uno base si no existe) |
| Plantillas con campos (autofill local) | JSON con capas: imagen, texto, forma, logo; campos `{{titulo}}`, `{{imagen}}`, `{{sello}}`; capa opcional con `"si": "sello"` | `python diseno.py plantilla miniatura-lado --base <carpeta imágenes> --campo imagen=FIN-003_img-012.png --campo "titulo=¿Me lo\nvoy a perder?" --campo sello=FOMO --salida <proyecto>\08_PUBLICAR\miniatura-1.png` |
| Efectos de texto | `efecto`: contorno, sombra, neon, degradado (`color` → `color2`), curva (`radio_curva`), caja (`fondo`); `color_ultima` pinta la última línea; el tamaño se ajusta solo al ancho y al máximo de líneas | en la plantilla |
| Imágenes | `ajuste`: cubrir, contener, inteligente (busca el sujeto), relleno (completa sobre fondo desenfocado); `mascara`: circulo, redondeado; `marco`; `sombra` | en la plantilla |
| Formas | rect (con `radio`), circulo (`solo_borde` para resaltar), flecha, degradado (oscurece un lado para que el texto se lea) | en la plantilla |
| Redimensionar (tipo Magic Resize) | recorte inteligente o relleno a 16x9, 9x16, 1x1, 4x5 | `python diseno.py redimensionar imagen.jpg --formatos 16x9,9x16,1x1 [--modo relleno]` |
| Mismo diseño en otros formatos | `--formatos 9x16,1x1` en `plantilla`: recompone (fondo a pantalla completa, textos centrados en la zona segura). Revisar siempre: no sabe dónde está la cara; para Shorts es mejor `portada-short` | en `plantilla` |
| Vista en el celular | cada plantilla deja también `<nombre>_160px.png` (como se ve en la lista de YouTube): el texto tiene que leerse ahí | automático |
| Quitar fondo | `"sin_fondo": true` en una capa de imagen, con rembg y el modelo `isnet-general-use` (uso comercial permitido). **Nunca** el modelo por defecto `bria-rmbg` ni RMBG-2.0 (licencia no comercial) | requiere `pip install "rembg[cpu]"` y bajar ~170 MB la primera vez: pedir permiso antes. Alternativa sin instalar: `remove-background` del conector de Canva |

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
