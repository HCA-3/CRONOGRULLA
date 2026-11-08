import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import pickle
import numpy as np

print("="*60)
print("EJECUTANDO BATERÍA DE PRUEBAS DEL SISTEMA CRONOGRULLA")
print("="*60)

# 1. Probar SoundSensorMonitor
print("\n[TEST 1] Probando SoundSensorMonitor...")
from views.view_timer import SoundSensorMonitor
sound = SoundSensorMonitor()
time.sleep(0.5)
print(f"  -> Decibelios detectados: {sound.current_db} dB")
print(f"  -> Estado acústico: {sound.status_text}")
print(f"  -> Disponible: {sound.available}")
sound.stop()
assert sound.current_db > 0, "Nivel de dB debe ser positivo"
print("  [PASÓ] SoundSensorMonitor funciona correctamente.")

# 2. Probar Modelo SVM de Therbligs
print("\n[TEST 2] Probando Modelo SVM Invariante de Therbligs...")
model_path = os.path.join("scratch", "therblig_svm_model.pkl")
assert os.path.exists(model_path), "El modelo SVM debe existir"
with open(model_path, "rb") as f:
    clf = pickle.load(f)

# Probar mano cerrada (G - Tomar)
feats_tomar = [0.85, 0.95, 1.0, 0.95, 0.85,  0.4, 0.45, 0.45, 0.4,  0.2, 0.2, 0.2,  0.92]
pred_tomar = clf.predict([feats_tomar])[0]
print(f"  -> Predicción mano cerrada (esperado 0: TOMAR): {pred_tomar}")
assert pred_tomar == 0, f"Mano cerrada debió ser 0, obtuvo {pred_tomar}"

# Probar mano abierta (RL - Soltar)
feats_soltar = [1.9, 2.1, 2.2, 2.0, 1.8,  1.3, 1.4, 1.35, 1.2,  0.45, 0.45, 0.45,  2.0]
pred_soltar = clf.predict([feats_soltar])[0]
print(f"  -> Predicción mano abierta (esperado 1: SOLTAR): {pred_soltar}")
assert pred_soltar == 1, f"Mano abierta debió ser 1, obtuvo {pred_soltar}"
print("  [PASÓ] Modelo SVM clasifica correctamente ambos micromovimientos.")

# 3. Probar Integridad de Datos en craneflow_data.json
print("\n[TEST 3] Verificando integridad de datos en craneflow_data.json...")
import json
with open("craneflow_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

measurements = data.get("measurements", [])
assert len(measurements) > 0, "Debe haber mediciones registradas"
print(f"  -> Total mediciones: {len(measurements)}")

splits_total = 0
for i, m in enumerate(measurements):
    assert "db_data" in m and len(m["db_data"]) > 0, f"Medición {i} sin db_data"
    assert "lux_data" in m and len(m["lux_data"]) > 0, f"Medición {i} sin lux_data"
    for s in m.get("splits", []):
        splits_total += 1
        th = s.get("therblig")
        assert th and "ESPERANDO" not in str(th).upper() and str(th) != "None", f"Split con therblig inválido: {th}"
        assert s.get("avg_angle", 0) > 0, f"Split con ángulo 0: {s}"
        assert "ergo_summary" in s and s["ergo_summary"].get("avg_elbow_r", 0) > 0, f"Split sin ergo_summary: {s}"

print(f"  -> Verificados {splits_total} splits en todas las mediciones sin fallas.")
print("  [PASÓ] craneflow_data.json tiene 100% de datos válidos (Therbligs, Ergonomía, Sonido, Lux).")

# 4. Probar Generación de Reporte PDF
print("\n[TEST 4] Probando generación de reporte PDF con datos corregidos...")
import customtkinter as ctk
app_mock = ctk.CTk()
app_mock.withdraw()  # Ocultar ventana durante test

from main import CraneFlowApp
# Mock app context
class MockApp:
    def __init__(self):
        self.data_file = "craneflow_data.json"
        self.pdf_folder = "guias_pdf"
        with open(self.data_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.operator_data = self.data.get("operators", [])
        self.line_config = self.data.get("line_config", {})
        self.operator_allowances = self.data.get("operator_allowances", {})
        self.current_model_name = self.data.get("current_model", "Grulla Clásica")
        self.models = self.data.get("models", {})
        m = self.models.get(self.current_model_name, {})
        self.ACTIVITIES = m.get("activities", [])
        self.FULL_DESCRIPTIONS = m.get("descriptions", [])
        self.TARGET_TOTAL_CYCLES = len(self.ACTIVITIES)

from tkinter import messagebox, filedialog
messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showwarning = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None
test_pdf_out = os.path.join("guias_pdf", "test_report.pdf")
filedialog.asksaveasfilename = lambda *args, **kwargs: test_pdf_out

from utils.pdf_report import PDFManager
mock_app = MockApp()
pdf_mgr = PDFManager(mock_app)
pdf_mgr.generate_pdf(selected_models=["Grulla Clásica"])
assert os.path.exists(test_pdf_out), f"El archivo PDF no fue generado en {test_pdf_out}"
print(f"  -> PDF generado exitosamente: {test_pdf_out} ({os.path.getsize(test_pdf_out)} bytes)")
print("  [PASÓ] Motor de Reportes PDF funciona correctamente.")

print("\n" + "="*60)
print("¡TODAS LAS PRUEBAS COMPLETADAS CON ÉXITO! (100% PASS)")
print("="*60)
