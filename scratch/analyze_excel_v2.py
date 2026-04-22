import pandas as pd
import sys

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\archivos\Ejemplo de cálculo de Tiempo Estándar.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    sheets_to_read = ['CÁLCULOS', 'TABLA DE SUPLEMENTOS']
    
    for sheet in sheets_to_read:
        if sheet in xl.sheet_names:
            print(f"\n--- Contenido de la hoja: {sheet} (Primeras 30 filas) ---")
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)
            print(df.dropna(how='all').head(30).to_string())
except Exception as e:
    print(f"Error al leer el archivo: {e}")
