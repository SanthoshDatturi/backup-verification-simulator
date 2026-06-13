import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus.flowables import HRFlowable

def create_header_footer(canvas, doc):
    canvas.saveState()
    
    # --- HEADER ---
    # Dark blue top banner
    canvas.setFillColorRGB(10/255, 30/255, 60/255)
    canvas.rect(0, 792 - 70, 612, 70, fill=1, stroke=0)
    
    # White header text
    canvas.setFont('Helvetica-Bold', 18)
    canvas.setFillColorRGB(1, 1, 1)
    canvas.drawString(40, 792 - 42, "DATABASE VERIFICATION REPORT")
    
    # Date text
    canvas.setFont('Helvetica-Oblique', 10)
    canvas.setFillColorRGB(200/255, 200/255, 200/255)
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    canvas.drawRightString(612 - 40, 792 - 42, date_str)
    
    # --- FOOTER ---
    # Footer line
    canvas.setStrokeColorRGB(200/255, 200/255, 200/255)
    canvas.line(40, 40, 612 - 40, 40)
    
    # Footer text
    canvas.setFont('Helvetica-Oblique', 8)
    canvas.setFillColorRGB(150/255, 150/255, 150/255)
    canvas.drawCentredString(612 / 2, 25, f"Confidential - Automated System Report - Page {doc.page}")
    
    canvas.restoreState()

def generate_pdf(title, content):
    """Generates a highly professional PDF report from a title and content string using ReportLab."""
    buffer = BytesIO()
    # Provide top margin for header, bottom margin for footer
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=85, bottomMargin=60, leftMargin=40, rightMargin=40)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.Color(20/255, 20/255, 20/255), spaceAfter=5)
    style_pass = ParagraphStyle('Pass', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.Color(10/255, 120/255, 10/255), backColor=colors.Color(230/255, 255/255, 230/255), spaceAfter=6, borderPadding=(4, 4, 4, 4))
    style_fail = ParagraphStyle('Fail', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.Color(180/255, 10/255, 10/255), backColor=colors.Color(255/255, 230/255, 230/255), spaceAfter=6, borderPadding=(4, 4, 4, 4))
    style_subheader = ParagraphStyle('SubHeader', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.Color(10/255, 30/255, 60/255), spaceBefore=15, spaceAfter=5)
    style_bullet_good = ParagraphStyle('BulletGood', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.Color(30/255, 80/255, 30/255), leftIndent=15, spaceAfter=3)
    style_bullet_bad = ParagraphStyle('BulletBad', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.Color(180/255, 30/255, 30/255), leftIndent=15, spaceAfter=3)
    style_test_title = ParagraphStyle('TestTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.Color(40/255, 40/255, 40/255), spaceBefore=10, spaceAfter=2)
    style_query = ParagraphStyle('Query', parent=styles['Code'], fontName='Courier', fontSize=9, textColor=colors.Color(80/255, 80/255, 80/255), backColor=colors.Color(245/255, 245/255, 245/255), borderPadding=(4, 4, 4, 4), leftIndent=10, spaceAfter=6)
    style_normal = ParagraphStyle('Standard', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.Color(50/255, 50/255, 50/255), spaceAfter=4)
    
    story = []
    
    story.append(Paragraph(title, style_title))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(10/255, 30/255, 60/255), spaceAfter=15))
    
    # Process content
    lines = content.split("\n")
    for line in lines:
        if not line.strip():
            story.append(Spacer(1, 0.05 * inch))
            continue
            
        if line.startswith("Status: PASS"):
            story.append(Paragraph(f"&nbsp; {line}", style_pass))
        elif line.startswith("Status: FAIL"):
            story.append(Paragraph(f"&nbsp; {line}", style_fail))
        elif line.startswith("Details:") or line.startswith("Errors:") or line.startswith("AI Narrative Report:") or line.startswith("AI Dynamic Validation Report"):
            story.append(Paragraph(line, style_subheader))
            story.append(HRFlowable(width="100%", thickness=0.2, color=colors.Color(220/255, 220/255, 220/255), spaceAfter=5, spaceBefore=0))
        elif line.startswith("[+]"):
            clean_line = line.replace("[+]", "").strip()
            story.append(Paragraph(f"&bull; &nbsp; {clean_line}", style_bullet_good))
        elif line.startswith("[-]"):
            clean_line = line.replace("[-]", "").strip()
            story.append(Paragraph(f"x &nbsp; {clean_line}", style_bullet_bad))
        elif line.startswith("Query:"):
            # Preformatted maintains courier spacing
            story.append(Preformatted(line, style_query))
        elif line.startswith("Test:"):
            story.append(Paragraph(line, style_test_title))
        else:
            story.append(Paragraph(line, style_normal))
            
    doc.build(story, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
