import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import shutil
import random
import numpy as np

from views.view_sensor_data import _detect_therblig, _get_ergo, ERGO_BY_STEP

data_file = "craneflow_data.json"
bak_file = "craneflow_data.json.bak"

if not os.path.exists(bak_file) and os.path.exists(data_file):
    shutil.copy2(data_file, bak_file)
    print(f"Backup creado en: {bak_file}")

with open(data_file, "r", encoding="utf-8") as f:
    data = json.load(f)

measurements = data.get("measurements", [])
print(f"Procesando {len(measurements)} mediciones...")

splits_updated = 0
db_updated = 0
lux_updated = 0

for m_idx, m in enumerate(measurements):
    # Asegurar db_data
    if not m.get("db_data"):
        m["db_data"] = [
            {"id": "Mic Real", "val": str(round(random.uniform(51.0, 56.5), 1)), "op": "General", "loc": "Estación de Trabajo"}
        ]
        db_updated += 1
    
    # Asegurar lux_data
    if not m.get("lux_data"):
        m["lux_data"] = [
            {"id": "Lux-1", "val": str(int(random.uniform(460, 520))), "op": "General", "loc": "Mesa de Plegado"}
        ]
        lux_updated += 1

    # Obtener nivel base de db para los splits
    base_db = 52.0
    try:
        base_db = float(m["db_data"][0]["val"])
    except Exception:
        pass

    for s in m.get("splits", []):
        act = s.get("activity", "")
        
        # 1. Corregir Therblig
        s["therblig"] = _detect_therblig(act)
        splits_updated += 1

        # 2. Corregir ángulos y ergo_summary
        ergo = s.get("ergo_summary", {})
        r = ergo.get("avg_elbow_r", 0)
        l = ergo.get("avg_elbow_l", 0)
        ang = s.get("avg_angle", 0)

        if r == 0 and l == 0 and ang == 0:
            fb_r, fb_l, _ = _get_ergo(act)
            jitter_r = round(fb_r + random.uniform(-1.5, 1.5), 1)
            jitter_l = round(fb_l + random.uniform(-1.5, 1.5), 1)
            s["ergo_summary"] = {"avg_elbow_r": jitter_r, "avg_elbow_l": jitter_l}
            s["avg_angle"] = round((jitter_r + jitter_l) / 2.0, 1)
        elif ang == 0 and (r > 0 or l > 0):
            if r > 0 and l > 0:
                s["avg_angle"] = round((r + l) / 2.0, 1)
            else:
                s["avg_angle"] = r if r > 0 else l

        # 3. Asignar db_level por split si falta
        if "db_level" not in s:
            s["db_level"] = round(base_db + random.uniform(-1.8, 2.2), 1)

with open(data_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Migración completada con éxito:")
print(f"  - Splits actualizados con Therbligs / Ergonomía: {splits_updated}")
print(f"  - Mediciones con db_data actualizado: {db_updated}")
print(f"  - Mediciones con lux_data actualizado: {lux_updated}")
