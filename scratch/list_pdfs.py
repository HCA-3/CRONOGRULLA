import os
import glob
from datetime import datetime
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("Listing all PDF files in the workspace:")
pdf_files = glob.glob("**/*.pdf", recursive=True)
for f in pdf_files:
    stat = os.stat(f)
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    print(f"- {f} ({stat.st_size} bytes, Modified: {mtime})")
