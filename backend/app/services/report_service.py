import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.core.config import settings

logger = logging.getLogger("wound_ai.report")

class PDFReportGenerator:
    """
    Generates professional clinical wound assessment PDF reports with disclaimers,
    measurement matrices, image masks/overlays, and longitudinal history.
    """

    @staticmethod
    def generate_assessment_pdf(assessment_data: dict, output_path: str) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=15
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=10,
            spaceAfter=8
        )
        normal_style = styles['Normal']
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#94a3b8'),
            spaceBefore=15
        )
        warning_style = ParagraphStyle(
            'ClinicalWarning',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#991b1b'),
            spaceBefore=4,
            spaceAfter=4,
        )
        warning_title_style = ParagraphStyle(
            'ClinicalWarningTitle',
            parent=styles['Heading2'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#991b1b'),
            spaceBefore=0,
            spaceAfter=4,
        )

        story = []

        # Title Header
        story.append(Paragraph("AI WOUND ASSESSMENT & HEALING REPORT", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Decision Support Tool — Clinical Review Required", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=15))

        # Patient & Case Summary Table
        pat_code = assessment_data.get("patient_code", "PAT-1001")
        pat_name = assessment_data.get("patient_name", "Synthetic Patient")
        case_code = assessment_data.get("case_code", "WC-1001")
        location = assessment_data.get("location", "Left lower leg")
        w_type = assessment_data.get("wound_type", "Venous Ulcer")

        patient_meta = [
            [Paragraph("<b>Patient ID:</b>", normal_style), Paragraph(pat_code, normal_style),
             Paragraph("<b>Case Code:</b>", normal_style), Paragraph(case_code, normal_style)],
            [Paragraph("<b>Patient Name:</b>", normal_style), Paragraph(pat_name, normal_style),
             Paragraph("<b>Anatomical Location:</b>", normal_style), Paragraph(location, normal_style)],
            [Paragraph("<b>Wound Category:</b>", normal_style), Paragraph(w_type, normal_style),
             Paragraph("<b>Visit Number:</b>", normal_style), Paragraph(str(assessment_data.get("visit_number", 1)), normal_style)]
        ]

        t_meta = Table(patient_meta, colWidths=[110, 160, 110, 160])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(t_meta)
        story.append(Spacer(1, 15))

        # Quantitative Metrics Table
        story.append(Paragraph("Automated Measurement Results", heading_style))

        area_mm2 = assessment_data.get("area_mm2", 0.0)
        area_cm2 = assessment_data.get("area_cm2", 0.0)
        width_mm = assessment_data.get("width_mm", 0.0)
        height_mm = assessment_data.get("height_mm", 0.0)
        scale_val = assessment_data.get("scale_mm_per_px", 0.1)
        conf_val = assessment_data.get("confidence_score", 0.92)
        pct_change = assessment_data.get("percentage_change")
        status_txt = assessment_data.get("healing_status", "Baseline")
        seg_method = assessment_data.get("segmentation_method", "cv_color")

        pct_str = f"{pct_change}%" if pct_change is not None else "--"

        # Dynamic score label based on actual segmentation method
        if seg_method == "unet":
            score_label = "U-Net Confidence"
            score_note = "Automated segmentation threshold"
        else:
            score_label = "CV Heuristic Score"
            score_note = "Adaptive color-based segmentation score"

        metrics_data = [
            [Paragraph("<b>Metric</b>", normal_style), Paragraph("<b>Value</b>", normal_style), Paragraph("<b>Clinical Notes</b>", normal_style)],
            [Paragraph("Wound Surface Area (mm²)", normal_style), Paragraph(f"<b>{area_mm2} mm²</b>", normal_style), Paragraph(f"Equivalent to {area_cm2} cm²", normal_style)],
            [Paragraph("Max Width / Height", normal_style), Paragraph(f"{width_mm} mm x {height_mm} mm", normal_style), Paragraph("Bounding contour dimension", normal_style)],
            [Paragraph("Calibration Scale", normal_style), Paragraph(f"{scale_val:.4f} mm/px", normal_style), Paragraph("Linear scale factor", normal_style)],
            [Paragraph(score_label, normal_style), Paragraph(f"{int(conf_val*100)}%", normal_style), Paragraph(score_note, normal_style)],
            [Paragraph("Area Change vs Prior", normal_style), Paragraph(f"<b>{pct_str}</b>", normal_style), Paragraph(f"Trajectory: {status_txt}", normal_style)]
        ]

        t_metrics = Table(metrics_data, colWidths=[180, 160, 200])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')])
        ]))
        story.append(t_metrics)
        story.append(Spacer(1, 15))

        # Images (Original, Mask, Overlay)
        story.append(Paragraph("Segmentation Visualizations", heading_style))

        orig_p = assessment_data.get("original_path")
        mask_p = assessment_data.get("mask_path")
        overlay_p = assessment_data.get("overlay_path")

        # Resolve relative paths to absolute filesystem paths within STORAGE_DIR
        # The database stores paths relative to STORAGE_DIR (e.g. "images/foo.jpg")
        # but os.path.exists() needs the full filesystem path.
        storage_dir = settings.STORAGE_DIR
        def resolve_path(p):
            if not p:
                return None
            if os.path.isabs(p):
                return p if os.path.exists(p) else None
            abs_p = os.path.join(storage_dir, p)
            return abs_p if os.path.exists(abs_p) else None

        orig_abs = resolve_path(orig_p)
        mask_abs = resolve_path(mask_p)
        overlay_abs = resolve_path(overlay_p)

        img_cells = []
        if orig_abs:
            try:
                img_cells.append(Image(orig_abs, width=170, height=140))
            except Exception:
                img_cells.append(Paragraph("Original Image (error)", normal_style))
        else:
            img_cells.append(Paragraph("Original Image (unavailable)", normal_style))

        if mask_abs:
            try:
                img_cells.append(Image(mask_abs, width=170, height=140))
            except Exception:
                img_cells.append(Paragraph("Binary Mask (error)", normal_style))
        else:
            img_cells.append(Paragraph("Binary Mask (unavailable)", normal_style))

        if overlay_abs:
            try:
                img_cells.append(Image(overlay_abs, width=170, height=140))
            except Exception:
                img_cells.append(Paragraph("Highlight Overlay (error)", normal_style))
        else:
            img_cells.append(Paragraph("Highlight Overlay (unavailable)", normal_style))

        t_images = Table([[img_cells[0], img_cells[1], img_cells[2]]], colWidths=[180, 180, 180])
        t_images.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_images)
        story.append(Spacer(1, 15))

        # Clinician Notes
        notes = assessment_data.get("clinician_notes", "Routine evaluation recorded. Surface area reduction observed.")
        story.append(Paragraph("Clinician Notes", heading_style))
        story.append(Paragraph(f"<i>{notes}</i>", normal_style))

        # Clinical Review Warning Box (prominent, bordered)
        story.append(Spacer(1, 20))
        warning_title = Paragraph("CLINICAL REVIEW REQUIRED", warning_title_style)
        warning_body = Paragraph(
            "AI-assisted wound segmentation is provided as a decision-support feature. "
            "Results require review by a qualified healthcare professional and are not "
            "intended for autonomous clinical decision-making. All segmentation masks, "
            "wound area calculations, and healing trend assessments <b>must be reviewed "
            "and approved by a qualified healthcare professional</b> before any clinical "
            "decision-making or treatment adjustment. The "
            + ("U-Net model" if seg_method == "unet" else "CV color segmentation pipeline")
            + " may produce false positives, false negatives, or inaccurate boundaries. "
            "Do not rely solely on automated output for patient care decisions.",
            warning_style
        )
        warning_table = Table([[warning_title], [warning_body]], colWidths=[540])
        warning_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#dc2626')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(warning_table)

        # Footer disclaimer
        story.append(Spacer(1, 10))
        disclaimer_text = (
            "<b>Notice:</b> This application is a technology demonstration prototype "
            "intended for decision support and research. Synthetic non-PHI data utilized. "
            "Automated "
            + ("U-Net" if seg_method == "unet" else "computer vision")
            + " measurements must be verified by a "
            "licensed healthcare professional prior to clinical decision-making."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        doc.build(story)
        return output_path
