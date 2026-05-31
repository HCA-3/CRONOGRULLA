import docx

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\Informe Final Métodos.docx"
doc = docx.Document(file_path)

print("Listing all paragraph texts with their indices:")
for idx, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if txt:
        # If it looks like a heading or has a number at the start, or is short and bold
        is_bold = any(run.bold for run in p.runs) if p.runs else False
        first_word = txt.split()[0] if txt.split() else ""
        if is_bold or len(txt) < 80 or any(char.isdigit() for char in first_word):
            print(f"{idx}: {txt[:120]} (Bold={is_bold})")
