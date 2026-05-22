import sys
import os
import json
from unittest.mock import MagicMock, patch

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar PDFManager
from utils.pdf_report import PDFManager

def run_test():
    print("Iniciando prueba headless de generación de PDF...")
    
    # Mock de la aplicación principal CraneFlowApp
    app = MagicMock()
    
    # Cargar datos reales de craneflow_data.json
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'craneflow_data.json'))
    with open(data_path, 'r', encoding='utf-8') as f:
        app.data = json.load(f)
        
    app.current_model_name = "Grulla Clásica"
    
    # Mockear el diccionario de modelos con las actividades del modelo actual
    app.models = app.data.get("models", {
        "Grulla Clásica": {
            "activities": [
                "Paso 1: Diagonal y mitad",
                "Paso 2: Pliegues cruzados",
                "Paso 3: Juntar esquinas (Base)",
                "Paso 4: Marcar solapas",
                "Paso 5: Marcar punta superior",
                "Paso 6: Abrir solapa superior",
                "Paso 7: Repetir cara posterior",
                "Paso 8: Solapas al centro",
                "Paso 9: Repetir lado opuesto",
                "Paso 10: Marcar patas inf.",
                "Paso 11: Pliegue invertido",
                "Paso 12: Cabeza y alas"
            ],
            "descriptions": ["Desc"] * 12
        }
    })
    
    # Instanciar el PDFManager
    manager = PDFManager(app)
    
    # Mockear filedialog.asksaveasfilename para que devuelva una ruta directa sin abrir diálogo de guardado
    out_pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_generated_report.pdf'))
    if os.path.exists(out_pdf_path):
        os.remove(out_pdf_path)
        
    with patch('tkinter.filedialog.asksaveasfilename', return_value=out_pdf_path):
        with patch('tkinter.messagebox.showinfo') as mock_info:
            with patch('tkinter.messagebox.showwarning') as mock_warning:
                # Generar el PDF para el modelo Grulla Clásica
                manager.generate_pdf(
                    selected_models=["Grulla Clásica"],
                    custom_data={"base": "1,2,3", "lote": "4,5"},
                    observations="Esta es una observación de prueba ergonómica.",
                    recommendations="Esta es una recomendación de prueba del taller."
                )
                
                print("Llamada completada.")
                if os.path.exists(out_pdf_path):
                    print(f"Éxito: PDF generado correctamente en: {out_pdf_path}")
                    print(f"Tamaño del archivo: {os.path.getsize(out_pdf_path)} bytes")
                else:
                    print("Error: El PDF no fue creado.")

if __name__ == '__main__':
    run_test()
