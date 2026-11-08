import sys
import os
sys.path.insert(0, os.path.abspath("."))
import customtkinter as ctk

app = ctk.CTk()
app.withdraw()

from main import CraneFlowApp
from views.view_atlas_biomecanico import AtlasBiomecanicoView

capp = CraneFlowApp()
capp.withdraw()

print("Probando inicialización de AtlasBiomecanicoView...")
capp.clear_main_frame()
atlas = AtlasBiomecanicoView(capp.main_frame, capp)
atlas.pack(fill="both", expand=True)
capp.update_idletasks()
print("[OK] AtlasBiomecanicoView inicializado correctamente.")

# Probar cambio de operarios
for op in ["Todos", "Laura", "Diego", "David"]:
    atlas.selected_operator.set(op)
    atlas.on_param_changed()
    print(f"[OK] Operario probado: {op} | Ángulo codo D: {atlas.metrics['avg_elbow_r']:.1f}°")

# Probar cambio de género
for g in ["Femenino ♀", "Masculino ♂"]:
    atlas.btn_gender.set(g)
    atlas.on_gender_toggled(g)
    print(f"[OK] Género probado: {g} | Afectación muñeca D: {atlas.zone_impacts['muñeca_r']:.2f}")

# Probar todos los horizontes temporales
for h in atlas.HORIZONS:
    atlas.seg_time.set(h)
    atlas.on_horizon_changed(h)
    cie_code = atlas.lbl_diag_cie.cget("text")
    eva_score = atlas.lbl_eva.cget("text")
    print(f"[OK] Horizonte: {h} -> Diagnóstico: {cie_code[:35]}... (EVA: {eva_score})")

# Probar todas las zonas de inspección
for z in atlas.PATHOLOGIES_DB.keys():
    atlas.selected_zone.set(z)
    atlas.update_diagnostic_panel()
    z_name = atlas.lbl_zone_name.cget("text")
    print(f"[OK] Zona seleccionada: {z_name}")

# Probar controles de zoom
atlas.zoom_in()
atlas.zoom_in()
assert atlas.zoom_level > 1.0
atlas.zoom_out()
atlas.reset_zoom()
assert atlas.zoom_level == 1.0
print("[OK] Controles de zoom y paneo funcionan correctamente.")

capp.destroy()
app.destroy()
print("\n¡BATERÍA DE PRUEBAS DEL ATLAS BIOMECÁNICO COMPLETADA CON ÉXITO (100% PASS)!")

