import pandas as pd
import openpyxl

file_path = r"C:\Users\dsant\Desktop\esta\Distribución temáticas_Ing Métodos.xlsx"

try:
    # Load the workbook to check sheet names
    wb = openpyxl.load_workbook(file_path, read_only=True)
    sheets = wb.sheetnames
    print("Sheets:", sheets)
    
    for sheet in sheets:
        print(f"\n--- Sheet: {sheet} ---")
        df = pd.read_excel(file_path, sheet_name=sheet)
        print(df.to_string())
except Exception as e:
    print("Error reading Excel file:", e)
