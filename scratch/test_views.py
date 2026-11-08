import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import customtkinter as ctk

app = ctk.CTk()
app.withdraw()

from main import CraneFlowApp
from views.view_dashboard import DashboardView
from views.view_sensor_data import SensorDataView
from views.view_stats import StatsView
from views.view_tables import TablesView
from views.view_comparison import ComparisonView
from views.view_models import ModelsView
from views.view_operators import OperatorsView
from views.view_trash import TrashView

# Inicializar CraneFlowApp minimizado
capp = CraneFlowApp()
capp.withdraw()

views = [
    ("DashboardView", DashboardView),
    ("SensorDataView", SensorDataView),
    ("StatsView", StatsView),
    ("TablesView", TablesView),
    ("ComparisonView", ComparisonView),
    ("ModelsView", ModelsView),
    ("OperatorsView", OperatorsView),
    ("TrashView", TrashView),
]

for name, V in views:
    try:
        capp.clear_main_frame()
        v = V(capp.main_frame, capp)
        v.pack(fill="both", expand=True)
        capp.update_idletasks()
        print(f"[OK] Vista cargada sin errores: {name}")
    except Exception as e:
        print(f"[FAIL] Error cargando vista {name}: {e}")
        sys.exit(1)

capp.destroy()
app.destroy()
print("\n¡Todas las vistas del sistema se instancian y renderizan a la perfección!")

