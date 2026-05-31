import sys
from pypdf import PdfReader

# Set stdout to UTF-8 to prevent any console encoding issues
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

output_file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\scratch\pdf_analysis.txt"

def analyze_pdf(file_path, out_file):
    out_file.write(f"\n==================================================\n")
    out_file.write(f"ANALYZING: {file_path}\n")
    out_file.write(f"==================================================\n")
    
    try:
        reader = PdfReader(file_path)
        out_file.write(f"Number of pages: {len(reader.pages)}\n")
        
        # Print metadata
        meta = reader.metadata
        out_file.write("\n--- Metadata ---\n")
        if meta:
            for key, val in meta.items():
                out_file.write(f"{key}: {val}\n")
        else:
            out_file.write("No metadata found.\n")
            
        # Read text from first 2 pages
        out_file.write("\n--- Text from Page 1 (First 3000 chars) ---\n")
        p1_text = reader.pages[0].extract_text()
        out_file.write(p1_text[:3000] + "\n")
        
        out_file.write("\n--- Text from Page 2 (First 3000 chars) ---\n")
        if len(reader.pages) > 1:
            p2_text = reader.pages[1].extract_text()
            out_file.write(p2_text[:3000] + "\n")
            
        # Let's extract section titles or outlines
        out_file.write("\n--- Headings Search and Structure ---\n")
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            full_text += f"\n--- PAGE {i+1} ---\n" + text
            
        # Search for references section
        ref_idx = full_text.lower().rfind("references")
        if ref_idx == -1:
            ref_idx = full_text.lower().rfind("referencias")
            
        if ref_idx != -1:
            out_file.write(f"\n--- References Section (Snippet) ---\n")
            out_file.write(full_text[ref_idx:ref_idx+2000] + "\n")
            
        # Let's write the first 1000 chars of last page (often Conclusions / Future Work)
        out_file.write("\n--- Text from Last Page (First 1500 chars) ---\n")
        last_page_text = reader.pages[-1].extract_text()
        out_file.write(last_page_text[:1500] + "\n")
                
    except Exception as e:
        out_file.write(f"Error reading PDF: {e}\n")

with open(output_file_path, "w", encoding="utf-8") as f:
    analyze_pdf(r"C:\Users\dsant\Desktop\esta\Ejemplo_paper 2.pdf", f)
    analyze_pdf(r"C:\Users\dsant\Desktop\esta\Therbligs in Action_ Video Understanding Through Motion Primitives.pdf", f)

print("Done! Analysis written to pdf_analysis.txt")
