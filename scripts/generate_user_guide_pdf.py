"""
Script to generate the OpenMrnaVaxGen Pipeline User Guide PDF using ReportLab.
Output: OpenMrnaVaxGen_Pipeline_User_Guide.pdf in the project root directory.
"""

import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = ROOT / "OpenMrnaVaxGen_Pipeline_User_Guide.pdf"


def create_user_guide():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    PRIMARY = colors.HexColor("#1e3a8a")     # Deep Navy
    SECONDARY = colors.HexColor("#0284c7")   # Teal / Blue
    DARK_TEXT = colors.HexColor("#1f2937")   # Charcoal
    LIGHT_BG = colors.HexColor("#f8fafc")    # Slate 50
    ACCENT_BG = colors.HexColor("#e0f2fe")   # Sky 100
    BORDER_COLOR = colors.HexColor("#cbd5e1")# Slate 300
    WARNING_BG = colors.HexColor("#fffbebe") # Amber light

    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=DARK_TEXT,
        spaceAfter=6,
    )

    code_style = ParagraphStyle(
        'CodeText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#7c2d12"),
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=DARK_TEXT,
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white,
    )

    story = []

    # Title Block
    story.append(Paragraph("OpenMrnaVaxGen Pipeline", title_style))
    story.append(Paragraph("Personalized mRNA Cancer Vaccine Design Pipeline — Complete User Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=0, spaceAfter=10))

    # Research Notice Box
    notice_text = Paragraph("<b>RESEARCH USE ONLY:</b> Not for clinical or diagnostic use. OpenMrnaVaxGen is an open-source computational pipeline designed for personalized neoantigen discovery and mRNA construct optimization.", callout_style)
    notice_table = Table([[notice_text]], colWidths=[7.5 * inch])
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#f59e0b")),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(notice_table)
    story.append(Spacer(1, 10))

    # Section 1: Overview
    story.append(Paragraph("1. Executive Overview", h1_style))
    p1 = ("OpenMrnaVaxGen automates the end-to-end computational workflow for personalized cancer mRNA vaccines. "
          "Given patient tumor/normal Whole Exome Sequencing (WES) data and an HLA profile, the pipeline identifies "
          "tumor-specific somatic mutations, predicts mutant peptide presentation across HLA alleles, ranks neoantigen candidates "
          "by immunogenicity, optimizes epitope ordering to minimize junctional immunogenicity, and constructs a fully codon-optimized "
          "mRNA sequence ready for wet lab synthesis.")
    story.append(Paragraph(p1, body_style))

    # Section 2: Pipeline Workflow Table
    story.append(Paragraph("2. Pipeline Workflow & 9 Core Steps", h1_style))
    
    steps_data = [
        [Paragraph("Step", table_header), Paragraph("Name", table_header), Paragraph("Key Tools & Algorithms", table_header), Paragraph("Output Artifact", table_header)],
        [Paragraph("Step 1", table_cell), Paragraph("Preprocessing", table_cell), Paragraph("GATK MarkDuplicates + SortSam", table_cell), Paragraph("Clean sorted BAMs", table_cell)],
        [Paragraph("Step 2", table_cell), Paragraph("Variant Calling", table_cell), Paragraph("GATK Mutect2 + FilterMutectCalls", table_cell), Paragraph("Somatic VCF (filtered)", table_cell)],
        [Paragraph("Step 3", table_cell), Paragraph("HLA Typing", table_cell), Paragraph("OptiType / Manual Clinical Entry", table_cell), Paragraph("hla_alleles.txt", table_cell)],
        [Paragraph("Step 4", table_cell), Paragraph("Neoantigen Prediction", table_cell), Paragraph("MHCflurry 2.0 (affinity & presentation)", table_cell), Paragraph("candidate_neoantigens.tsv", table_cell)],
        [Paragraph("Step 5", table_cell), Paragraph("Immunogenicity Ranking", table_cell), Paragraph("IMPROVE composite scoring model", table_cell), Paragraph("ranked_neoantigens.tsv", table_cell)],
        [Paragraph("Step 6", table_cell), Paragraph("Epitope Ordering", table_cell), Paragraph("Held-Karp exact TSP / Greedy linker opt.", table_cell), Paragraph("ordered_epitopes.fasta", table_cell)],
        [Paragraph("Step 7", table_cell), Paragraph("mRNA Construct Design", table_cell), Paragraph("VaxPress + ViennaRNA / LinearFold", table_cell), Paragraph("vaccine_mrna_*.fasta", table_cell)],
        [Paragraph("Step 8", table_cell), Paragraph("CodonFM Validation", table_cell), Paragraph("nvidia/NV-CodonFM-80M (Experimental)", table_cell), Paragraph("expression_score.json", table_cell)],
        [Paragraph("Step 9", table_cell), Paragraph("Report Generation", table_cell), Paragraph("Markdown + Matplotlib PDF reporting", table_cell), Paragraph("vaccine_report.md & figures", table_cell)],
    ]

    t_steps = Table(steps_data, colWidths=[0.8 * inch, 1.8 * inch, 2.7 * inch, 2.2 * inch])
    t_steps.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_steps)
    story.append(Spacer(1, 10))

    # Section 3: Ranking Methodology
    story.append(Paragraph("3. Neoantigen Ranking Methodology (IMPROVE Model)", h1_style))
    p_rank = ("Candidates are evaluated using a multi-feature composite immunogenicity score based on feature weights "
              "derived from the IMPROVE benchmark (Frontiers in Immunology, 2024). All weights can be customized in the UI:")
    story.append(Paragraph(p_rank, body_style))

    weights_data = [
        [Paragraph("Feature", table_header), Paragraph("Weight", table_header), Paragraph("Biological Rationale", table_header)],
        [Paragraph("MHCflurry Presentation Score", table_cell), Paragraph("40%", table_cell), Paragraph("Predicts cell surface antigen presentation probability.", table_cell)],
        [Paragraph("Agretopicity (DAI)", table_cell), Paragraph("25%", table_cell), Paragraph("log2(WT / Mutant affinity). Higher DAI indicates non-tolerized T cell repertoire.", table_cell)],
        [Paragraph("VAF / Clonality", table_cell), Paragraph("20%", table_cell), Paragraph("Variant Allele Frequency. Prioritizes clonal mutations present across all tumor cells.", table_cell)],
        [Paragraph("BLOSUM Mutation Score", table_cell), Paragraph("10%", table_cell), Paragraph("Measures amino acid divergence (radical substitutions are more immunogenic).", table_cell)],
        [Paragraph("Foreignness", table_cell), Paragraph("5%", table_cell), Paragraph("BLOSUM kernel similarity between mutant and wildtype peptides.", table_cell)],
    ]
    t_weights = Table(weights_data, colWidths=[2.2 * inch, 0.8 * inch, 4.5 * inch])
    t_weights.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_weights)
    story.append(Spacer(1, 10))

    # Section 4: Installation & Prerequisites
    story.append(Paragraph("4. Installation & Prerequisites", h1_style))
    
    story.append(Paragraph("A. Initial Folder Setup", h2_style))
    p_cmd1 = Paragraph("mkdir \"data/test\", \"reference\", \"results\"", code_style)
    t_cmd1 = Table([[p_cmd1]], colWidths=[7.5 * inch])
    t_cmd1.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), ACCENT_BG), ('PADDING', (0, 0), (-1, -1), 6)]))
    story.append(t_cmd1)

    story.append(Paragraph("B. Download hg38 Reference Genome (~3.5 GB uncompressed)", h2_style))
    p_cmd2 = Paragraph("uv run --with requests --with tqdm --no-project python scripts/download_reference.py", code_style)
    t_cmd2 = Table([[p_cmd2]], colWidths=[7.5 * inch])
    t_cmd2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), ACCENT_BG), ('PADDING', (0, 0), (-1, -1), 6)]))
    story.append(t_cmd2)

    story.append(Paragraph("C. Download Test Dataset (HCC1143 BAMs)", h2_style))
    p_cmd3 = Paragraph("cp .env.example .env<br/>uv run --with huggingface_hub --with python-dotenv --no-project python scripts/download_data.py", code_style)
    t_cmd3 = Table([[p_cmd3]], colWidths=[7.5 * inch])
    t_cmd3.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), ACCENT_BG), ('PADDING', (0, 0), (-1, -1), 6)]))
    story.append(t_cmd3)

    story.append(Spacer(1, 10))

    # Section 5: Execution Modes
    story.append(Paragraph("5. Execution Modes", h1_style))

    story.append(Paragraph("Launch Streamlit Web UI (Recommended)", h2_style))
    story.append(Paragraph("Launch the web application directly from terminal using uv:", body_style))
    p_cmd4 = Paragraph("uv run streamlit run app.py", code_style)
    t_cmd4 = Table([[p_cmd4]], colWidths=[7.5 * inch])
    t_cmd4.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), ACCENT_BG), ('PADDING', (0, 0), (-1, -1), 6)]))
    story.append(t_cmd4)
    story.append(Paragraph("Access the interactive UI at: <b>http://localhost:8501</b>", body_style))

    story.append(Paragraph("Individual CLI Execution", h2_style))
    p_cmd6 = Paragraph("uv run python scripts/preprocess.py<br/>uv run python scripts/variant.py<br/>uv run python scripts/neoantigen_prediction.py<br/>uv run python scripts/candidate_ranking.py<br/>uv run python scripts/epitope_ordering.py<br/>uv run python scripts/mrna_design.py", code_style)
    t_cmd6 = Table([[p_cmd6]], colWidths=[7.5 * inch])
    t_cmd6.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), ACCENT_BG), ('PADDING', (0, 0), (-1, -1), 6)]))
    story.append(t_cmd6)

    story.append(Spacer(1, 10))

    # Section 6: Output Hierarchy
    story.append(Paragraph("6. Output Directory Structure", h1_style))
    story.append(Paragraph("Every pipeline run generates a versioned results directory under <code>results/run_&lt;sample&gt;_&lt;timestamp&gt;/</code>:", body_style))

    tree_text = Paragraph(
        "results/run_HCC1143_20261008_143000/<br/>"
        "├── step1/   sorted.bam<br/>"
        "├── step2/   filtered_variants.vcf.gz<br/>"
        "├── step3/   hla_alleles.txt<br/>"
        "├── step4/   candidate_neoantigens.tsv<br/>"
        "├── step5/   ranked_neoantigens.tsv, all_scored_candidates.tsv, subclonal_filtered.tsv<br/>"
        "├── step6/   ordered_epitopes.fasta, junction_scores.tsv<br/>"
        "├── step7/   vaccine_mrna_*.fasta, candidate_comparison.json<br/>"
        "└── step9/   vaccine_report.md, figures/",
        code_style
    )
    t_tree = Table([[tree_text]], colWidths=[7.5 * inch])
    t_tree.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG), ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR), ('PADDING', (0, 0), (-1, -1), 8)]))
    story.append(t_tree)

    story.append(Spacer(1, 10))

    # Section 7: Troubleshooting
    story.append(Paragraph("7. Troubleshooting & FAQ", h1_style))
    
    story.append(Paragraph("• Docker API Connection Error:", h2_style))
    story.append(Paragraph("Ensure Docker Desktop is launched and running in the Windows system tray before calling <code>docker compose up app</code>.", body_style))

    story.append(Paragraph("• Connection Interrupted During Genome Download:", h2_style))
    story.append(Paragraph("The updated <code>download_reference.py</code> script includes automatic HTTP Range request resumption. Re-running the command resumes right where it left off.", body_style))

    story.append(Paragraph("• LinearFold C++ Compilation Error in uv sync:", h2_style))
    story.append(Paragraph("If running locally without Docker, the pipeline automatically detects the available folding engine and falls back to open-source <b>ViennaRNA</b> (<code>vienna</code>).", body_style))

    # Footer/Page Callback
    def add_page_decorations(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(0.5 * inch, 0.3 * inch, "OpenMrnaVaxGen User Guide — Research Use Only")
        canvas.drawRightString(8.0 * inch, 0.3 * inch, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    print(f"User Guide PDF generated successfully at: {OUTPUT_PDF}")

if __name__ == "__main__":
    create_user_guide()
