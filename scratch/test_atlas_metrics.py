import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np

# Verificar datos de operadores para el Atlas
with open("craneflow_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

measurements = data.get("measurements", [])
operators = data.get("operators", [])

print(f"Mediciones encontradas: {len(measurements)}")
print(f"Operadores registrados: {operators}")

# Calcular métricas ergonómicas reales por operario
op_stats = {}
for op in operators:
    op_name = op if isinstance(op, str) else op.get("name")
    elbow_r_vals = []
    elbow_l_vals = []
    therbligs = []
    durations = []
    db_vals = []
    
    for m in measurements:
        for s in m.get("splits", []):
            if s.get("operator") == op_name:
                ergo = s.get("ergo_summary", {})
                if ergo.get("avg_elbow_r", 0) > 0:
                    elbow_r_vals.append(ergo["avg_elbow_r"])
                if ergo.get("avg_elbow_l", 0) > 0:
                    elbow_l_vals.append(ergo["avg_elbow_l"])
                if s.get("therblig"):
                    therbligs.append(s["therblig"])
                if s.get("duration", 0) > 0:
                    durations.append(s["duration"])
                if s.get("db_level", 0) > 0:
                    db_vals.append(s["db_level"])
                    
    op_stats[op_name] = {
        "count_steps": len(durations),
        "avg_elbow_r": np.mean(elbow_r_vals) if elbow_r_vals else 105.0,
        "avg_elbow_l": np.mean(elbow_l_vals) if elbow_l_vals else 105.0,
        "tomar_count": sum(1 for t in therbligs if "TOMAR" in t),
        "soltar_count": sum(1 for t in therbligs if "SOLTAR" in t),
        "avg_db": np.mean(db_vals) if db_vals else 52.0,
    }
    print(f"Estadísticas para {op_name}: {op_stats[op_name]}")

print("Extracción de métricas para Atlas exitosa!")

