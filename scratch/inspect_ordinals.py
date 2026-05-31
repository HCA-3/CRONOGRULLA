import docx

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\Informe Final Métodos.docx"
doc = docx.Document(file_path)

p = doc.paragraphs[106]
print("Text:")
print(p.text[:120])
print("Ordinals:")
for c in p.text[:50]:
    print(f"'{c}': {ord(c)}")
