import docx
import sys
sys.stdout.reconfigure(encoding='utf-8')

file_path = r"c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\Informe Final Métodos.docx"
doc = docx.Document(file_path)

body = doc.element.body
for idx, child in enumerate(body):
    if 35 <= idx <= 80:
        if child.tag.endswith('p'):
            p = docx.text.paragraph.Paragraph(child, doc)
            txt = p.text.strip()
            if txt:
                print(f"[{idx}] P: {txt[:100]}")
            else:
                print(f"[{idx}] P: (empty)")
        elif child.tag.endswith('tbl'):
            table = docx.table.Table(child, doc)
            hdr = [c.text.strip() for c in table.rows[0].cells]
            print(f"[{idx}] TBL: {len(table.rows)}x{len(table.columns)} Header: {hdr}")
