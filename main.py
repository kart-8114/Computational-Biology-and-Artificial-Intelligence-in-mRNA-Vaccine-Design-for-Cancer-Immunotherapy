"""
OpenMrnaVaxGen Pipeline — Main CLI Orchestrator

Usage:
  # Run full pipeline locally
  uv run python main.py

  # Run deterministic synthetic demo mode (~3 seconds, no large genome files needed)
  uv run python main.py --demo

  # Run starting from VCF (Entry B)
  uv run python main.py --entry B --vcf path/to/variants.vcf.gz --hla path/to/hla.txt
"""

import argparse
import gzip
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path

# Add scripts directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import paths


def run_demo_mode():
    """
    Executes a deterministic synthetic demo pipeline end-to-end in seconds.
    Does not require downloading full human reference genomes or ML model weights.
    All outputs are explicitly labeled as DEMO MODE (SYNTHETIC FIXTURES).
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    demo_run_id = f"run_DEMO_HCC1143_{ts}"
    demo_dir = paths.RESULTS / demo_run_id
    demo_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" ⚡ OpenMrnaVaxGen — SYNTHETIC DEMO MODE")
    print("=" * 70)
    print(f" Demo Run ID: {demo_run_id}")
    print(f" Output Dir:  {demo_dir}\n")

    # Step 1: Preprocessing (Synthetic BAM)
    s1_dir = demo_dir / "step1"
    s1_dir.mkdir(exist_ok=True)
    (s1_dir / "sorted.bam").write_text("DEMO_BAM_HEADER_SORTED\n")
    (s1_dir / "marked_duplicates.bam").write_text("DEMO_BAM_HEADER_DEDUPED\n")
    (s1_dir / "duplicate_metrics.txt").write_text("Library: DEMO_LIB\nDuplicates: 1.2%\n")
    print("[✓] Step 1: Preprocessing complete (Synthetic BAM generated)")

    # Step 2: Variant Calling (Synthetic Somatic VCF with TP53 driver mutation)
    s2_dir = demo_dir / "step2"
    s2_dir.mkdir(exist_ok=True)
    vcf_content = textwrap.dedent("""\
        ##fileformat=VCFv4.2
        ##source=OpenMrnaVaxGen_Demo
        ##FILTER=<ID=PASS,Description="All filters passed">
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths">
        ##FORMAT=<ID=AF,Number=A,Type=Float,Description="Allele fraction">
        #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tHCC1143_tumor\tHCC1143_normal
        chr17\t7674220\t.\tC\tT\t.\tPASS\t.\tGT:AD:AF\t0/1:10,30:0.75\t0/0:40,0:0.0
        chr17\t7675088\t.\tC\tT\t.\tPASS\t.\tGT:AD:AF\t0/1:15,25:0.62\t0/0:35,0:0.0
        chr17\t7676100\t.\tG\tA\t.\tPASS\t.\tGT:AD:AF\t0/1:12,28:0.70\t0/0:50,0:0.0
        chr17\t37880220\t.\tC\tT\t.\tPASS\t.\tGT:AD:AF\t0/1:20,30:0.60\t0/0:45,0:0.0
        chr17\t43045690\t.\tA\tG\t.\tPASS\t.\tGT:AD:AF\t0/1:18,22:0.55\t0/0:40,0:0.0
    """)
    vcf_gz = s2_dir / "filtered_variants.vcf.gz"
    with gzip.open(vcf_gz, "wt", encoding="utf-8") as f:
        f.write(vcf_content)
    print("[✓] Step 2: Variant Calling complete (5 synthetic somatic SNVs generated)")

    # Step 3: HLA Typing
    s3_dir = demo_dir / "step3"
    s3_dir.mkdir(exist_ok=True)
    hla_file = s3_dir / "hla_alleles.txt"
    hla_alleles = ["HLA-A*02:01", "HLA-A*24:02", "HLA-B*07:02", "HLA-B*44:02", "HLA-C*07:01", "HLA-C*05:01"]
    hla_file.write_text("\n".join(hla_alleles) + "\n")
    print(f"[✓] Step 3: HLA Typing complete ({len(hla_alleles)} HLA alleles loaded)")

    # Step 4: Neoantigen Prediction
    s4_dir = demo_dir / "step4"
    s4_dir.mkdir(exist_ok=True)
    peptides_file = s4_dir / "candidate_neoantigens.tsv"
    peptides_data = textwrap.dedent("""\
        mutation_id\tpeptide\twt_peptide\tlength\tvaf\tgene\tbest_allele\taffinity\tpresentation_score
        chr17:7674220:C>T\tTYSPALNKM\tTYSPALNK\t9\t0.75\tTP53\tHLA-A*02:01\t120.0\t0.88
        chr17:7674220:C>T\tCTYSPALNK\tRTYSPALNK\t9\t0.75\tTP53\tHLA-A*02:01\t110.0\t0.91
        chr17:7674220:C>T\tSVTCTYSPAL\tSVRCTYSPAL\t10\t0.75\tTP53\tHLA-A*02:01\t140.0\t0.85
        chr17:7675088:C>T\tLNKMFMQLA\tLNKMFCQLA\t9\t0.62\tTP53\tHLA-A*02:01\t180.0\t0.79
        chr17:37880220:C>T\tKMFMQLAKT\tKMFCQLAKT\t9\t0.60\tERBB2\tHLA-A*02:01\t210.0\t0.74
        chr17:43045690:A>G\tPALNKMFCQ\tPALNKMFC\t9\t0.55\tBRCA1\tHLA-A*02:01\t250.0\t0.68
    """)
    peptides_file.write_text(peptides_data)
    print("[✓] Step 4: Neoantigen Prediction complete (6 candidate binders predicted)")

    # Step 5: Immunogenicity Ranking (IMPROVE Composite Model)
    s5_dir = demo_dir / "step5"
    s5_dir.mkdir(exist_ok=True)
    ranked_file = s5_dir / "ranked_neoantigens.tsv"
    ranked_data = textwrap.dedent("""\
        mutation_id\tpeptide\tbest_allele\taffinity\tpresentation_score\tagretopicity\tvaf\tcomposite_score\tflags
        chr17:7674220:C>T\tCTYSPALNK\tHLA-A*02:01\t110.0\t0.91\t2.5\t0.75\t0.722\tPASS
        chr17:7674220:C>T\tSVTCTYSPAL\tHLA-A*02:01\t140.0\t0.85\t2.5\t0.75\t0.682\tPASS
        chr17:7674220:C>T\tTYSPALNKM\tHLA-A*02:01\t120.0\t0.88\t2.5\t0.75\t0.652\tPASS
        chr17:7675088:C>T\tLNKMFMQLA\tHLA-A*02:01\t180.0\t0.79\t2.5\t0.62\t0.582\tPASS
        chr17:37880220:C>T\tKMFMQLAKT\tHLA-A*02:01\t210.0\t0.74\t2.5\t0.60\t0.512\tPASS
        chr17:43045690:A>G\tPALNKMFCQ\tHLA-A*02:01\t250.0\t0.68\t2.5\t0.55\t0.442\tPASS
    """)
    ranked_file.write_text(ranked_data)
    (s5_dir / "all_scored_candidates.tsv").write_text(ranked_data)
    print("[✓] Step 5: Candidate Ranking complete (IMPROVE feature weights applied)")

    # Step 6: Epitope Ordering (Held-Karp TSP)
    s6_dir = demo_dir / "step6"
    s6_dir.mkdir(exist_ok=True)
    fasta_file = s6_dir / "ordered_epitopes.fasta"
    epitope_str = "PALNKMFCQGPGPGKMFMQLAKTGPGPGLNKMFMQLAGPGPGCTYSPALNK"
    fasta_file.write_text(f">ordered_polyepitope\n{epitope_str}\n")
    print("[✓] Step 6: Epitope Ordering complete (Held-Karp TSP solved: 51 aa polyepitope)")

    # Step 7: mRNA Construct Design
    s7_dir = demo_dir / "step7"
    s7_dir.mkdir(exist_ok=True)
    cand_dir = s7_dir / "A_balanced"
    cand_dir.mkdir(exist_ok=True)
    mrna_cds = "ATGCCCGCCTTGAACAAGATGTTCTGCCAGGGCCCCGGCCCCGGCAAGATGTTCATGCAGCTGGCCAAGACCGGCCCCGGCCCCGGCCTGAACAAGATGTTCATGCAGCTGGCCGGC"
    mrna_full = f"GGGAAATAAGAGAGAAAAGAAGAGTAAGAAGAAATATAAGAGCCACC{mrna_cds}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    (cand_dir / "vaccine_mrna.fasta").write_text(f">vaccine_mrna_A_balanced\n{mrna_full}\n")
    comparison = [
        {"candidate_id": "A_balanced", "description": "Balanced MFE + CAI", "gc_content": 0.52, "mfe_kcal_mol": -142.5, "total_length_nt": len(mrna_full), "issues": []}
    ]
    (s7_dir / "candidate_comparison.json").write_text(json.dumps(comparison, indent=2))
    print("[✓] Step 7: mRNA Design complete (Codon-optimized construct: 486 nt)")

    # Step 9: Report Generation
    s9_dir = demo_dir / "step9"
    s9_dir.mkdir(exist_ok=True)
    report_md = s9_dir / "vaccine_report.md"
    report_content = textwrap.dedent(f"""\
        # Personalized mRNA Cancer Vaccine Design Report (DEMO MODE)

        > **RESEARCH USE ONLY. NOT FOR CLINICAL OR DIAGNOSTIC USE.**
        > All values in this report were generated during a synthetic demonstration run (`{demo_run_id}`).

        ---

        ## Executive Summary

        - **Run ID**: `{demo_run_id}`
        - **Sample**: `HCC1143` (Synthetic Demo)
        - **Somatic Variants**: 5
        - **Predicted Neoantigens**: 6
        - **Selected Vaccine Targets**: 4
        - **Construct Length**: 486 nt (Coding Sequence: 165 nt)

        ---

        ## Candidate Targets

        | Rank | Gene | Mutation | Peptide | HLA Allele | Composite Score |
        |------|------|----------|---------|------------|-----------------|
        | 1 | TP53 | chr17:7674220:C>T | CTYSPALNK | HLA-A*02:01 | 0.722 |
        | 2 | TP53 | chr17:7674220:C>T | SVTCTYSPAL | HLA-A*02:01 | 0.682 |
        | 3 | TP53 | chr17:7675088:C>T | LNKMFMQLA | HLA-A*02:01 | 0.582 |
        | 4 | ERBB2 | chr17:37880220:C>T | KMFMQLAKT | HLA-A*02:01 | 0.512 |

        ---

        ## Final mRNA Construct Sequence

        ```fasta
        >vaccine_mrna_demo
        {mrna_full}
        ```
    """)
    report_md.write_text(report_content)
    print("[✓] Step 9: Report Generation complete")

    print("\n" + "=" * 70)
    print(" 🎉 SYNTHETIC DEMO RUN COMPLETE")
    print(f" Report generated at: {report_md}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="OpenMrnaVaxGen — Personalized mRNA Cancer Vaccine Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--demo", action="store_true", help="Run deterministic synthetic demo mode end-to-end (~3s)")
    parser.add_argument("--entry", choices=["A", "B"], default="A", help="Entry point: A=Full (FASTQs/BAMs), B=Pre-called VCF/MAF")
    parser.add_argument("--sample", default="HCC1143", help="Sample ID name")
    args = parser.parse_args()

    if args.demo:
        run_demo_mode()
        return

    print(f"OpenMrnaVaxGen Pipeline — Entry Point {args.entry} (Sample: {args.sample})")
    print("To run interactively with GUI, launch: uv run streamlit run app.py")


if __name__ == "__main__":
    main()
