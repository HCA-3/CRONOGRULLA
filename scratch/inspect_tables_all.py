import docx

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\Informe Final Métodos.docx"
doc = docx.Document(file_path)

for t_idx, table in enumerate(doc.tables[:2]):
    print(f"\n--- Table {t_idx} ---")
    for r_idx, row in enumerate(table.rows):
        row_txt = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        print(f"Row {r_idx}: {row_txt}")
