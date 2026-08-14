import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

def generate_result_pdf(student, results):
    """Generate PDF result for a student"""
    
    # Create PDF directory if not exists
    pdf_dir = os.path.join('static', 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # PDF file path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"result_{student.roll_no}_{timestamp}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    
    # Create document
    doc = SimpleDocTemplate(filepath, pagesize=A4, 
                           topMargin=1*cm, bottomMargin=1*cm,
                           leftMargin=1.5*cm, rightMargin=1.5*cm)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#34495e')
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=3,
        alignment=TA_LEFT
    )
    
    # Title
    title = Paragraph("ACADEMIC RESULT REPORT", title_style)
    story.append(title)
    
    subtitle = Paragraph("OFFICIAL GRADE REPORT", subtitle_style)
    story.append(subtitle)
    
    story.append(Spacer(1, 0.5*cm))
    
    # Student Information Section
    student_info_data = [
        [Paragraph("<b>Roll Number:</b>", header_style), 
         Paragraph(student.roll_no, normal_style)],
        [Paragraph("<b>Student Name:</b>", header_style), 
         Paragraph(student.full_name, normal_style)],
        [Paragraph("<b>Class:</b>", header_style), 
         Paragraph(student.class_name or "Not Specified", normal_style)],
        [Paragraph("<b>Date of Birth:</b>", header_style), 
         Paragraph(student.date_of_birth.strftime('%d/%m/%Y'), normal_style)],
    ]
    
    if student.email:
        student_info_data.append(
            [Paragraph("<b>Email:</b>", header_style), 
             Paragraph(student.email, normal_style)]
        )
    
    student_info_table = Table(student_info_data, colWidths=[2.5*cm, 12*cm])
    student_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7'))
    ]))
    
    story.append(student_info_table)
    story.append(Spacer(1, 1*cm))
    
    # Results Table
    if results:
        # Group results by term
        results_by_term = {}
        for result in results:
            term = result.term or "General"
            if term not in results_by_term:
                results_by_term[term] = []
            results_by_term[term].append(result)
        
        # Calculate overall statistics
        total_obtained = sum([r.marks_obtained for r in results])
        total_max = sum([r.subject.max_marks for r in results])
        overall_percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
        
        for term, term_results in results_by_term.items():
            # Term header
            term_header = Paragraph(f"<b>{term.upper()} EXAMINATION</b>", header_style)
            story.append(term_header)
            story.append(Spacer(1, 0.3*cm))
            
            # Create results table for this term
            result_data = [
                ["Subject Code", "Subject Name", "Max Marks", "Marks Obtained", "Percentage"]
            ]
            
            term_total_obtained = 0
            term_total_max = 0
            
            for result in term_results:
                percentage = (result.marks_obtained / result.subject.max_marks * 100) if result.subject.max_marks > 0 else 0
                result_data.append([
                    result.subject.code,
                    result.subject.name,
                    str(result.subject.max_marks),
                    str(result.marks_obtained),
                    f"{percentage:.1f}%"
                ])
                term_total_obtained += result.marks_obtained
                term_total_max += result.subject.max_marks
            
            # Add term total row
            term_percentage = (term_total_obtained / term_total_max * 100) if term_total_max > 0 else 0
            result_data.append([
                "<b>TOTAL</b>", 
                "", 
                f"<b>{term_total_max}</b>", 
                f"<b>{term_total_obtained}</b>", 
                f"<b>{term_percentage:.1f}%</b>"
            ])
            
            # Create table
            result_table = Table(result_data, colWidths=[2.5*cm, 6*cm, 2*cm, 2.5*cm, 2.5*cm])
            result_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            story.append(result_table)
            story.append(Spacer(1, 0.5*cm))
        
        # Overall Summary
        story.append(Spacer(1, 0.5*cm))
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold',
            backColor=colors.HexColor('#ecf0f1'),
            borderPadding=10,
            borderColor=colors.HexColor('#3498db'),
            borderWidth=1
        )
        
        # Determine grade based on percentage
        if overall_percentage >= 90:
            grade = "A+ (Excellent)"
            remark = "Outstanding Performance"
        elif overall_percentage >= 80:
            grade = "A (Very Good)"
            remark = "Excellent Performance"
        elif overall_percentage >= 70:
            grade = "B+ (Good)"
            remark = "Very Good Performance"
        elif overall_percentage >= 60:
            grade = "B (Above Average)"
            remark = "Good Performance"
        elif overall_percentage >= 50:
            grade = "C (Average)"
            remark = "Satisfactory Performance"
        elif overall_percentage >= 40:
            grade = "D (Pass)"
            remark = "Needs Improvement"
        else:
            grade = "F (Fail)"
            remark = "Must Reappear for Examination"
        
        summary_text = f"""
        <b>OVERALL SUMMARY</b><br/>
        Total Marks Obtained: <b>{total_obtained}</b> out of <b>{total_max}</b><br/>
        Overall Percentage: <b>{overall_percentage:.2f}%</b><br/>
        Grade: <b>{grade}</b><br/>
        Result Status: <b>{'PASS' if overall_percentage >= 40 else 'FAIL'}</b><br/>
        <i>{remark}</i>
        """
        
        summary = Paragraph(summary_text, summary_style)
        story.append(summary)
        
    else:
        # No results found
        no_data = Paragraph("<b>No results found for this student.</b>", header_style)
        story.append(no_data)
    
    # Footer with generation info
    story.append(Spacer(1, 1*cm))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=0,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    footer_text = f"""
    Report generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>
    This is a computer-generated document. No signature required.
    """
    
    footer = Paragraph(footer_text, footer_style)
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    
    return filepath