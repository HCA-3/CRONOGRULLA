import win32com.client
import os

file_path = r"C:\Users\dsant\Desktop\esta\Articulo_CronoGrulla_IEEE.docx"

if not os.path.exists(file_path):
    print("Error: File does not exist")
    exit(1)

try:
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(file_path)
    
    # Force layout update to get accurate page count
    word.ActiveDocument.ComputeStatistics(2) # 2 = wdStatisticPages
    pages = doc.ComputeStatistics(2)
    
    print(f"Total Pages in Word Document: {pages}")
    
    doc.Close(False)
    word.Quit()
except Exception as e:
    print("Error getting page count:", e)
