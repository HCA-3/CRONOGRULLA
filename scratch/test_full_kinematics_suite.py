import sys
sys.path.insert(0, ".")
import tkinter as tk
import customtkinter as ctk
import time

ctk.set_appearance_mode("dark")

root = ctk.CTk()
root.geometry("1100x750")
root.title("Testing ModeloLesiones3DView Kinematics & Fingers")

class MockApp:
    def __init__(self):
        self.operator_data = [{"name": "Diego", "gender": "Masculino"}]
        self.data = {
            "measurements": [
                {
                    "operator": "Diego",
                    "codo_r": 105.0,
                    "codo_l": 98.0,
                    "posture_r": "Normal",
                    "therbligs": [{"code": "G", "name": "Tomar"}]
                }
            ],
            "operators": [{"name": "Diego", "gender": "Masculino"}],
            "active_operator": "Diego"
        }

mock_app = MockApp()

from views.view_lesiones_3d import ModeloLesiones3DView

view = ModeloLesiones3DView(root, mock_app)
view.pack(fill="both", expand=True)
root.update()

print("Initial render successful!")

# Test each motion mode
for mode in [
    "🫁 Respiración", 
    "⚙️ Plegado Completo (Hombro-Codo-Mano-Dedos)", 
    "🎯 Articular Zona Seleccionada", 
    "⏸ Estático"
]:
    print(f"Testing mode: {mode}")
    view.on_motion_mode_changed(mode)
    for _ in range(6):
        root.update()
        time.sleep(0.04)

# Test selecting various joint zones
for z in ["hombro_r", "codo_r", "muñeca_r", "mano_r", "dedos_r", "cuello", "espalda_alta", "hombro_l", "dedos_l"]:
    print(f"Testing zone selection: {z}")
    view.selected_zone.set(z)
    view.update_diagnostic_panel()
    view.draw_mannequin_3d()
    root.update()
    time.sleep(0.03)

# Test genders
for g in ["Mujer ♀", "Hombre ♂"]:
    print(f"Testing gender: {g}")
    view.on_gender_toggled(g)
    root.update()
    time.sleep(0.03)

# Test zoom and angles
view.zoom_in()
view.zoom_out()
view.set_angles(45, -10)
root.update()

root.destroy()
print("ALL TESTS PASSED WITH ZERO ERRORS!")
