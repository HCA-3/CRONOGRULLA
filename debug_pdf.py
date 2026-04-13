from fpdf import FPDF

def test_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 8, "Tarea 1", 1, 0, 'C', True)
    pdf.cell(40, 8, "Resp: Op 1", 1, 0, 'C', True)
    
    pdf.multi_cell(0, 8, " Actividad 1", 1, 'L', True)
    pdf.set_x(10) # RESET X
    
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 6, "Coloca el papel cuadrado con el color...", 1, 'L')
    pdf.set_x(10) # RESET X

if __name__ == '__main__':
    test_pdf()
    print("Success after set_x!")
