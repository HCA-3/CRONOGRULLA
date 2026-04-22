import pandas as pd
import sys

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\archivos\Ejemplo de cálculo de Tiempo Estándar.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print(f"Hojas encontradas: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        print(f"\n--- Contenido de la hoja: {sheet} (Primeras 20 filas) ---")
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)
        # Mostrar solo filas que tengan algún contenido
        clean_df = df.dropna(how='all').head(20)
        print(clean_df.to_string())
except Exception as e:
    print(f"Error al leer el archivo: {e}")
