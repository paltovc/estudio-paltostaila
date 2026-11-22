# Prueba S4 del estudio: LTX-Video (texto a video) con OpenVINO GenAI en Intel. Mide tiempos; no se usa en videos.
import sys, time, json, argparse
from pathlib import Path
import numpy as np, cv2, psutil
import openvino_genai as ov_genai

a = argparse.ArgumentParser()
a.add_argument("--modelo", default=str(Path(__file__).parent / "modelos" / "ltx_video_int8"))
a.add_argument("--dispositivo", default="GPU")
a.add_argument("--ancho", type=int, default=512)
a.add_argument("--alto", type=int, default=288)
a.add_argument("--cuadros", type=int, default=41)
a.add_argument("--pasos", type=int, default=20)
a.add_argument("--fps", type=int, default=25)
A = a.parse_args()
prompt = ("Flat 2D cartoon illustration, a simple stick figure with a round white head and a blue hoodie "
          "kneels and stacks a small cardboard box on top of others, clean thick outlines, plain blue background, "
          "no text")
neg = "realistic, photo, 3d, text, letters, watermark, blurry, distorted"
salidas = Path(__file__).parent / "salidas"
salidas.mkdir(parents=True, exist_ok=True)
n = 1
while (salidas / f"prueba_intel_{A.dispositivo}_{A.ancho}x{A.alto}_{n}.mp4").exists():
    n += 1
out = salidas / f"prueba_intel_{A.dispositivo}_{A.ancho}x{A.alto}_{n}.mp4"
proc = psutil.Process()
t0 = time.time()
pipe = ov_genai.Text2VideoPipeline(A.modelo, A.dispositivo)
t_carga = time.time() - t0
pico = [proc.memory_info().rss]
def cb(step, num_steps, latent):
    pico[0] = max(pico[0], proc.memory_info().rss)
    print(f"paso {step + 1}/{num_steps}  {time.time() - t0:.0f} s", flush=True)
    return False
t1 = time.time()
r = pipe.generate(prompt, negative_prompt=neg, width=A.ancho, height=A.alto, num_frames=A.cuadros,
                  num_inference_steps=A.pasos, guidance_scale=3.0, frame_rate=A.fps, callback=cb)
t_gen = time.time() - t1
v = np.array(r.video.data) if hasattr(r.video, "data") else np.array(r.video)
v = v[0]
w = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), A.fps, (v.shape[2], v.shape[1]))
if not w.isOpened():
    sys.exit(f"No se pudo escribir {out}")
for f in v:
    w.write(cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_RGB2BGR))
w.release()
res = {"archivo": out.name, "dispositivo": A.dispositivo, "ancho": A.ancho, "alto": A.alto, "cuadros": A.cuadros,
       "segundos_video": round(A.cuadros / A.fps, 2), "pasos": A.pasos, "carga_s": round(t_carga),
       "generacion_s": round(t_gen), "ram_pico_gb": round(pico[0] / 1024**3, 1)}
print("RESULTADO " + json.dumps(res, ensure_ascii=False), flush=True)
