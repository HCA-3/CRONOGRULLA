import shutil
import os

src = r"C:\Users\dsant\Desktop\Articulo CronoGrulla inlges_temp.docx"
dst = r"C:\Users\dsant\Desktop\Articulo CronoGrulla inlges.docx"

try:
    shutil.copyfile(src, dst)
    os.remove(src)
    print("Success: Document updated and temporary file removed.")
except PermissionError:
    print("Error: Permission denied. Please ensure Microsoft Word is closed and try again.")
except Exception as e:
    print(f"Error: {e}")
