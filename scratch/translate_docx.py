import docx
from deep_translator import GoogleTranslator
import os
import shutil

def translate_text(text, translator):
    if not text.strip():
        return text
    # If the text has no letters, don't translate
    if not any(c.isalpha() for c in text):
        return text
    
    # Simple heuristic: if it looks like it's already in English (e.g. abstract, keywords, intro section titles)
    # or doesn't have Spanish indicators, but let's let Google Translator handle it.
    # To speed up, we can check if it's already English using a simple check or just translate it.
    try:
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"Error translating: {e}", flush=True)
        return text

def translate_paragraph(p, translator):
    original_text = p.text.strip()
    if not original_text:
        return
    
    translated_text = translate_text(p.text, translator)
    
    if p.runs:
        p.runs[0].text = translated_text
        for run in p.runs[1:]:
            run.text = ""
    else:
        p.text = translated_text

def translate_docx(input_path, output_path):
    print(f"Loading document: {input_path}", flush=True)
    doc = docx.Document(input_path)
    
    translator = GoogleTranslator(source='auto', target='en')
    
    total_paragraphs = len(doc.paragraphs)
    print(f"Translating {total_paragraphs} paragraphs...", flush=True)
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            print(f"Paragraph {i}/{total_paragraphs}: {p.text[:40]}...", flush=True)
            translate_paragraph(p, translator)
            
    total_tables = len(doc.tables)
    print(f"Translating {total_tables} tables...", flush=True)
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                for p_idx, p in enumerate(cell.paragraphs):
                    if p.text.strip():
                        print(f"Table {t_idx} Row {r_idx} Col {c_idx} P {p_idx}: {p.text[:40]}...", flush=True)
                        translate_paragraph(p, translator)
                        
    print(f"Saving translated document to: {output_path}", flush=True)
    doc.save(output_path)
    
    # Overwrite the original file with the translated one
    print(f"Overwriting original file: {input_path}", flush=True)
    shutil.copyfile(output_path, input_path)
    print("All done successfully!", flush=True)

if __name__ == "__main__":
    input_file = r"C:\Users\dsant\Desktop\Articulo CronoGrulla inlges.docx"
    output_file = r"C:\Users\dsant\Desktop\Articulo CronoGrulla inlges_temp.docx"
    translate_docx(input_file, output_file)
