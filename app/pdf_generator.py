from fpdf import FPDF

def generate_pdf(title, content):
    """Generates a PDF from a title and content string, returning a byte string."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16, style="B")
    pdf.cell(0, 10, txt=title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=12)
    # multi_cell handles word wrap
    pdf.multi_cell(0, 8, txt=content)
    
    return bytes(pdf.output())
