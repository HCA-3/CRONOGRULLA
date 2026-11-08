import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tkinter as tk
import customtkinter as ctk
import time
from views.view_lesiones_3d import ModeloLesiones3DView

class MockApp:
    def __init__(self):
        self.data = {
            "measurements": [
                {
                    "lux_data": [{"val": 450}],
                    "db_data": [{"val": 58}],
                    "splits": [
                        {
                            "operator": "Laura Gomez",
                            "duration": 3.2,
                            "therblig": "TOMAR (G)",
                            "ergo_summary": {"avg_elbow_r": 96.5, "avg_elbow_l": 92.0}
                        }
                    ]
                }
            ]
        }
        self.operator_data = ["Laura Gomez", "Diego Perez"]

root = ctk.CTk()
root.geometry("1100x750")
app = MockApp()

view = ModeloLesiones3DView(root, app)
view.pack(fill="both", expand=True)

root.update()

# Let's verify initial mode
print(f"Initial mode: {view.human_motion_mode.get()}")
assert view.human_motion_mode.get() == "🫁 Respiración", "Default mode should be Respiración"

# Run a few animation frames
for i in range(10):
    root.update()
    time.sleep(0.033)

print("Frames with Respiración rendered successfully.")

# Switch to Trabajo (Plegado)
view.on_motion_mode_changed("⚙️ Plegado (Trabajo)")
print(f"Switched mode: {view.human_motion_mode.get()}")

for i in range(15):
    root.update()
    time.sleep(0.033)

print("Frames with Plegado (Trabajo) rendered successfully.")

# Toggle Auto-Rotate
view.toggle_autorotate()
print(f"Auto-rotate active: {view.auto_rotate}")

for i in range(15):
    root.update()
    time.sleep(0.033)

view.toggle_autorotate()
print(f"Auto-rotate toggled off: {view.auto_rotate}")

# Switch to Estático
view.on_motion_mode_changed("⏸ Estático")
root.update()
print("Static mode rendered successfully.")

# Test Hotspot Click
view.selected_zone.set("codo_r")
view.update_diagnostic_panel()
root.update()
print("Hotspot update diagnostic panel passed.")

view.destroy()
root.destroy()
print("ALL TESTS PASSED WITH 0 ERRORS!")
