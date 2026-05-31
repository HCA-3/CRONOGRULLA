import docx

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\Informe Final Métodos.docx"
doc = docx.Document(file_path)

p = doc.paragraphs[90]
print("P[90] text:")
print(p.text)
for c in p.text[:100]:
    print(f"'{c}': {ord(c)}")
