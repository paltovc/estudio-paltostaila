# Estudio Paltostaila · equipo.py (motor 0.16)
# Mira qué puede hacer ESTE computador con video local (NVIDIA, Intel o nada) y lo deja en equipo.json.
# Solo lee: no instala, no descarga ni cambia nada del sistema.
#   python equipo.py              → resumen en pantalla y equipo.json en la carpeta del estudio
#   python equipo.py --json       → solo el JSON
#   python equipo.py bienvenida   → muestra una sola vez el mensaje para la pareja (computador con NVIDIA)
# Para pruebas: ESTUDIO_EQUIPO_SIMULADO='{"nvidia":[["RTX 3060",12288]],"graficas":["NVIDIA GeForce RTX 3060"]}'
import json, os, shutil, subprocess, sys, ctypes
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MOTOR = Path(__file__).resolve().parent
BASE = Path(os.environ.get("ESTUDIO_BASE") or MOTOR.parent)
VIDEO_LOCAL = BASE / "video_local"
VRAM_MIN_NVIDIA = 6 * 1024        # MB: menos que esto no alcanza ni para los modelos chicos de WanGP

BIENVENIDA = """Hola, amor 💛
Este motor de video no corre en el computador de Patricio: le falta una tarjeta gráfica NVIDIA. Pero él dejó la puerta abierta para que funcionara en el tuyo, porque este estudio lo está construyendo para los dos.
Todo lo que se genere aquí queda en tu computador, sin gastar créditos.
— Patricio (y el Estudio Palto Style)"""


def _correr(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def _simulado():
    t = os.environ.get("ESTUDIO_EQUIPO_SIMULADO")
    return json.loads(t) if t else None


def nvidia():
    """Lista de (nombre, MB de VRAM o None si no se pudo leer, generación compute_cap o None) de las NVIDIA,
    en el orden de nvidia-smi (la primera es la GPU 0, la que usa WanGP)."""
    s = _simulado()
    if s is not None:
        return [(x[0], x[1], x[2] if len(x) > 2 else None) for x in s.get("nvidia", [])]
    if not shutil.which("nvidia-smi"):
        return []
    out = _correr(["nvidia-smi", "--query-gpu=name,memory.total,compute_cap", "--format=csv,noheader,nounits"])
    if not out:   # controladores viejos no conocen compute_cap
        out = _correr(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    gpus = []
    for linea in out.splitlines():
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) >= 2 and partes[0]:
            vram = int(partes[1]) if partes[1].isdigit() else None
            try:
                cap = float(partes[2]) if len(partes) > 2 else None
            except ValueError:
                cap = None
            gpus.append((partes[0], vram, cap))
    return gpus


def graficas():
    """Nombres de todas las tarjetas gráficas que ve Windows (Intel, NVIDIA, AMD)."""
    s = _simulado()
    if s is not None:
        return list(s.get("graficas", []))
    if os.name != "nt":
        return []
    out = _correr(["powershell", "-NoProfile", "-Command",
                   "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def memoria():
    """(RAM total GB, memoria virtual total GB) en Windows; (None, None) si no se puede leer."""
    s = _simulado()
    if s is not None:
        return s.get("ram_gb"), s.get("virtual_gb")
    if os.name != "nt":
        return None, None

    class MEM(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MEM()
    m.dwLength = ctypes.sizeof(MEM)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        return None, None
    return round(m.ullTotalPhys / 1024**3, 1), round(m.ullTotalPageFile / 1024**3, 1)


def resultado_intel():
    """Lo que dejó la prueba en Intel (video_local\\s4_resultado.json), si se hizo."""
    p = VIDEO_LOCAL / "s4_resultado.json"
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))   # -sig: PowerShell lo escribe con BOM
    except Exception:
        return None


def decidir(gpus_nv, nombres, intel_s4=None):
    """Qué ruta de video local corresponde a este equipo y hasta qué resolución llega.
    Las rutas: nvidia_wangp (imagen a video con WanGP), intel_experimental (solo texto a video, LTX en OpenVINO,
    si la prueba S4 salió usable) o ninguna (el video local queda instalado pero cerrado: puerta abierta)."""
    gpus_nv = [tuple(g) + (None,) * (3 - len(g)) for g in gpus_nv]
    gpu0 = gpus_nv[0] if gpus_nv else None          # WanGP usa la GPU 0
    hay_intel = any("intel" in n.lower() for n in nombres)
    vram, cap = (gpu0[1], gpu0[2]) if gpu0 else (None, None)
    gb = round(vram / 1024) if vram else None
    if gpu0 and vram and vram >= VRAM_MIN_NVIDIA and (cap is None or cap >= 7.5):
        res = "720p" if vram >= 7.5 * 1024 else "480p"   # 7,5: muchas de 8 GB informan algo menos (8188 MiB)
        return {"ruta": "nvidia_wangp", "tarjeta": gpu0[0], "vram_mb": vram, "compute_cap": cap,
                "resolucion_local": res, "imagen_a_video": True,
                "mensaje": f"Video local disponible: {gpu0[0]} ({gb} GB). WanGP anima la imagen del "
                           f"personaje hasta {res}."}
    if gpu0 and vram is None:
        nota = f"Hay una NVIDIA ({gpu0[0]}), pero no se pudo leer su memoria: no se instala por las dudas."
    elif gpu0 and cap is not None and cap < 7.5 and vram >= VRAM_MIN_NVIDIA:
        nota = (f"La NVIDIA {gpu0[0]} es de una generación antigua (GTX 10xx o anterior): WanGP pide otra "
                f"instalación para ella y este instalador no la cubre.")
    elif gpu0:
        nota = f"La NVIDIA {gpu0[0]} tiene {gb} GB: no alcanza (mínimo {VRAM_MIN_NVIDIA // 1024} GB)."
    else:
        nota = "Este equipo no tiene tarjeta NVIDIA."
    if hay_intel and intel_s4 and intel_s4.get("usable"):
        return {"ruta": "intel_experimental", "tarjeta": next(n for n in nombres if "intel" in n.lower()),
                "resolucion_local": intel_s4.get("resolucion", "baja"), "imagen_a_video": False,
                "mensaje": nota + " Hay una opción experimental en Intel (LTX, solo texto a video, no anima la "
                                  "imagen del personaje). Para las escenas del canal: Flow o Higgsfield."}
    return {"ruta": "ninguna", "tarjeta": None, "resolucion_local": None, "imagen_a_video": False,
            "mensaje": nota + " El video local queda instalado pero cerrado: la puerta está abierta para un "
                              "computador con NVIDIA (video_local\\instalar_nvidia.cmd). Aquí se usa Flow o Higgsfield."}


def resolucion_uniforme(fuentes):
    """Regla de Patricio (21-11-2026): un video no mezcla resoluciones. Si todas las fuentes de movimiento
    alcanzan 1080p, todo va en 1080p (también Higgsfield); si alguna queda bajo eso, todo el video va en 720p."""
    alto = {"2160p": 2160, "4k": 2160, "1440p": 1440, "1080p": 1080, "720p": 720, "480p": 480}
    vals = [alto.get(str(f).lower(), 0) for f in fuentes if f]
    if not vals:
        return "1080p"
    return "1080p" if min(vals) >= 1080 else "720p"


def bienvenida(mostrar_ventana=True):
    """Muestra el mensaje para la pareja una sola vez por computador (marca en video_local\\.bienvenida_vista).
    Devuelve True si lo mostró ahora."""
    marca = VIDEO_LOCAL / ".bienvenida_vista"
    if marca.exists():
        return False
    print("\n" + BIENVENIDA + "\n", flush=True)
    if mostrar_ventana and os.name == "nt" and not os.environ.get("ESTUDIO_SIN_VENTANA"):
        try:
            ctypes.windll.user32.MessageBoxW(None, BIENVENIDA, "Estudio Palto Style", 0x40)
        except Exception:
            pass
    VIDEO_LOCAL.mkdir(parents=True, exist_ok=True)
    marca.write_text("vista\n", encoding="utf-8")
    return True


def revisar():
    gpus, nombres = nvidia(), graficas()
    ram, virtual = memoria()
    try:
        libre = round(shutil.disk_usage(BASE).free / 1024**3, 1)
    except Exception:
        libre = None
    info = {"graficas": nombres, "nvidia": [{"nombre": g[0], "vram_mb": g[1], "compute_cap": g[2]} for g in gpus], "ram_gb": ram,
            "memoria_virtual_gb": virtual, "disco_libre_gb": libre}
    info.update(decidir(gpus, nombres, resultado_intel()))
    return info


if __name__ == "__main__":
    A = sys.argv[1:]
    if A[:1] == ["bienvenida"]:
        bienvenida()
        sys.exit(0)
    if A[:1] == ["resolucion"]:
        print(resolucion_uniforme(A[1:]))
        sys.exit(0)
    info = revisar()
    if A[:1] == ["ruta"]:          # para los .cmd: imprime solo la ruta (nvidia_wangp, intel_experimental o ninguna)
        print(info["ruta"])
        sys.exit(0)
    if "--json" in A:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        sys.exit(0)
    destino = BASE / "equipo.json"
    destino.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Tarjetas gráficas: " + (", ".join(info["graficas"]) or "no se pudieron leer"))
    print(f"RAM: {info['ram_gb']} GB · memoria virtual: {info['memoria_virtual_gb']} GB · disco libre: {info['disco_libre_gb']} GB")
    print(info["mensaje"])
    print(f"LISTO {destino}")
