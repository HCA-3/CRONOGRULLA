import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
import customtkinter as ctk

from main import CraneFlowApp
from views.view_lesiones_3d import ModeloLesiones3DView

capp = CraneFlowApp()
capp.geometry("1200x800")

print("="*60)
print("TEST: PUNTOS SENSORICOS EN MANOS Y DEDOS (12 ZONAS BIOMECANICAS)")
print("="*60)

capp.clear_main_frame()
view_3d = ModeloLesiones3DView(capp.main_frame, capp)
view_3d.pack(fill="both", expand=True)
capp.update()
print("[OK] ModeloLesiones3DView montado con 12 zonas biomecánicas.")

# 1. Verificar que existen los puntos de manos y dedos en hotspots_def
hotspot_keys = list(view_3d.PATHOLOGIES_DB.keys())
print("Zonas patológicas registradas:", len(hotspot_keys))
for k in ["dedos_r", "mano_r", "dedos_l", "mano_l", "muñeca_r", "muñeca_l", "codo_r", "codo_l", "hombro_r", "hombro_l", "cuello", "espalda_alta"]:
    assert k in hotspot_keys, f"Falta zona patológica: {k}"
    assert k in view_3d.zone_impacts, f"Falta cálculo de impacto en: {k}"
    print(f"  [OK] Zona registrada: {k:12s} | Impacto base: {view_3d.zone_impacts[k]:.2f}")

# 2. Probar inspección de Dedos Mano Derecha
view_3d.selected_zone.set("dedos_r")
view_3d.update_diagnostic_panel()
capp.update()
assert "DEDOS MANO DERECHA" in view_3d.lbl_zone_name.cget("text")
assert "Pinza digital" in view_3d.lbl_zone_angle.cget("text")
print("  [OK] Inspección de Dedos Mano Derecha (Pinza digital / Pulgar-Índice) verificada.")

# 3. Probar inspección de Mano Derecha (Palma / Tenar)
view_3d.selected_zone.set("mano_r")
view_3d.update_diagnostic_panel()
capp.update()
assert "MANO DERECHA" in view_3d.lbl_zone_name.cget("text")
assert "Compresión palmar" in view_3d.lbl_zone_angle.cget("text")
print("  [OK] Inspección de Mano Derecha (Palma y Eminencia Tenar) verificada.")

# 4. Probar proyección de hotspots en canvas (12 puntos)
assert len(view_3d.projected_hotspots) == 12
for k, (u, v, r, rz) in view_3d.projected_hotspots.items():
    print(f"  [OK] Hotspot en pantalla {k:12s} -> (u={u:.1f}, v={v:.1f}, radio={r:.1f}, z={rz:.1f})")

# 5. Probar clics cerca de los dedos y las manos
dedos_u, dedos_v, _, _ = view_3d.projected_hotspots["dedos_r"]
detected = view_3d.detect_hotspot_click(dedos_u, dedos_v)
assert detected == "dedos_r"
print(f"  [OK] Clic sobre Dedos Mano Derecha detectado correctamente: {detected}")

mano_u, mano_v, _, _ = view_3d.projected_hotspots["mano_r"]
detected_m = view_3d.detect_hotspot_click(mano_u, mano_v)
assert detected_m == "mano_r"
print(f"  [OK] Clic sobre Mano Derecha detectado correctamente: {detected_m}")

view_3d.destroy()
capp.destroy()

print("="*60)
print("¡TODAS LAS PRUEBAS DE MANOS Y DEDOS PASARON AL 100%! (12/12 ZONAS)")
print("="*60)
