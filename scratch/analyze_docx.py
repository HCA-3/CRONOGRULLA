import docx

doc_path = r"C:\Users\dsant\Desktop\Articulo CronoGrulla inlges.docx"
try:
    doc = docx.Document(doc_path)
    print("Number of paragraphs:", len(doc.paragraphs))
    print("Number of tables:", len(doc.tables))
    total_text_len = sum(len(p.text) for p in doc.paragraphs)
    print("Total text length in paragraphs:", total_text_len)
    
    # Show first few paragraphs
    print("\n--- FIRST 10 PARAGRAPHS ---")
    count = 0
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            print(f"P{i}: {p.text[:100]}...")
            count += 1
            if count >= 10:
                break
except Exception as e:
    print("Error:", e)
