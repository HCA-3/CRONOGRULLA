import pandas as pd
import sys

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\archivos\Ejemplo de cálculo de Tiempo Estándar.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print(f"Hojas encontradas: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        print(f"\n--- Contenido de la hoja: {sheet} (Primeras 30 filas) ---")
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)
        # Mostrar filas que tengan al menos una celda no nula
        data = df.dropna(how='all').head(30)
        if not data.empty:
            print(data.to_string())
        else:
            print("Hoja vacía o sin datos en las primeras 30 filas.")
except Exception as e:
    print(f"Error al leer el archivo: {e}")
