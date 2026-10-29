"""
Automated Pytest Suite for OpenMrnaVaxGen Pipeline

Tests path resolution, VCF parsing, HLA allele validation, peptide generation,
IMPROVE ranking score weights and normalization, Held-Karp TSP epitope ordering,
mRNA construct assembly, and end-to-end synthetic demo mode.
"""

import gzip
import json
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add root and scripts directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

import paths
import neoantigen_peptides
import candidate_ranking
import epitope_ordering
import mrna_design
import report_generate
import main as main_cli


def test_paths_resolution():
    """Test path resolution and step output directory structure."""
    assert paths.BASE.exists()
    run_id = paths.RUN_ID
    assert run_id.startswith("run_")
    step1_dir = paths.step_dir(1)
    assert step1_dir == paths.RUN_DIR / "step1"


def test_vcf_parsing(tmp_path):
    """Test pure-Python VCF parsing and variant filtering."""
    vcf_content = textwrap.dedent("""\
        ##fileformat=VCFv4.2
        #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tTUMOR\tNORMAL
        chr17\t7674220\t.\tC\tT\t.\tPASS\t.\tGT:AD:AF\t0/1:10,30:0.75\t0/0:40,0:0.0
        chr17\t7675088\t.\tC\tT\t.\tLOW_QUAL\t.\tGT:AD:AF\t0/1:15,25:0.62\t0/0:35,0:0.0
    """)
    vcf_path = tmp_path / "test.vcf.gz"
    with gzip.open(vcf_path, "wt", encoding="utf-8") as f:
        f.write(vcf_content)

    df = neoantigen_peptides.parse_vcf(vcf_path)
    assert len(df) == 1  # LOW_QUAL should be filtered out
    assert df.iloc[0]["chrom"] == "chr17"
    assert df.iloc[0]["pos"] == 7674220
    assert df.iloc[0]["vaf"] == 0.75


def test_hla_allele_validation(tmp_path):
    """Test HLA allele file loading and normalization."""
    hla_path = tmp_path / "hla.txt"
    hla_path.write_text("HLA-A*02:01\nHLA-A*24:02\n  HLA-B*07:02 \n")

    alleles = neoantigen_peptides.load_hla_alleles(hla_path)
    assert len(alleles) == 3
    assert alleles[0] == "HLA-A*02:01"
    assert alleles[2] == "HLA-B*07:02"


def test_fallback_peptide_generation():
    """Test fallback peptide generation for test/demo mode."""
    v_df = pd.DataFrame([{"chrom": "chr17", "pos": 7674220, "ref": "C", "alt": "T", "vaf": 0.75}])
    p_df = neoantigen_peptides.generate_fallback_peptides(v_df)
    assert not p_df.empty
    assert "peptide" in p_df.columns
    assert "wt_peptide" in p_df.columns
    assert p_df.iloc[0]["gene"] == "TP53"


def test_ranking_weights_and_normalization():
    """Test IMPROVE immunogenicity score weighting and normalization."""
    df = pd.DataFrame([
        {
            "mutation_id": "chr17:7674220:C>T",
            "peptide": "CTYSPALNK",
            "wt_peptide": "RTYSPALNK",
            "length": 9,
            "vaf": 0.75,
            "gene": "TP53",
            "best_allele": "HLA-A*02:01",
            "affinity": 110.0,
            "presentation_score": 0.91,
            "agretopicity": 2.5,
        },
        {
            "mutation_id": "chr17:7675088:C>T",
            "peptide": "LNKMFMQLA",
            "wt_peptide": "LNKMFCQLA",
            "length": 9,
            "vaf": 0.62,
            "gene": "TP53",
            "best_allele": "HLA-A*02:01",
            "affinity": 180.0,
            "presentation_score": 0.79,
            "agretopicity": 2.0,
        },
    ])

    total_weight = (
        candidate_ranking.W_PRESENTATION +
        candidate_ranking.W_AGRETOPICITY +
        candidate_ranking.W_VAF +
        candidate_ranking.W_BLOSUM +
        candidate_ranking.W_FOREIGNNESS
    )
    assert abs(total_weight - 1.0) < 1e-5

    df = candidate_ranking.compute_blosum_score(df)
    scored_df = candidate_ranking.score_candidates(df)
    assert "composite_score" in scored_df.columns
    assert scored_df.iloc[0]["composite_score"] >= scored_df.iloc[1]["composite_score"]


def test_tsp_epitope_ordering():
    """Test Held-Karp exact TSP epitope ordering and linker construction."""
    epitopes = [
        {"mutation_id": "m1", "peptide": "PALNKMFCQ", "best_allele": "HLA-A*02:01"},
        {"mutation_id": "m2", "peptide": "KMFMQLAKT", "best_allele": "HLA-A*02:01"},
        {"mutation_id": "m3", "peptide": "LNKMFMQLA", "best_allele": "HLA-A*02:01"},
    ]
    junction_matrix = np.zeros((3, 3))

    best_order, cost = epitope_ordering.exact_ordering(epitopes, junction_matrix)
    assert len(best_order) == 3
    assert set(best_order) == {0, 1, 2}

    ordered_peptides = [epitopes[i]["peptide"] for i in best_order]
    full_string = "GPGPG".join(ordered_peptides)
    assert "GPGPG" in full_string
    assert len(full_string) == 3 * 9 + 2 * 5  # 3 x 9mers + 2 x 5mer linkers = 37 aa


def test_mrna_construct_assembly():
    """Test mRNA construct assembly, UTR/Kozak addition, and frame check."""
    epitope_aa = "PALNKMFCQGPGPGKMFMQLAKT"
    cds_dna = mrna_design.simple_codon_optimize(epitope_aa)

    assert cds_dna.startswith("ATG")
    assert cds_dna.endswith("TGA")
    assert len(cds_dna) % 3 == 0

    full_mrna, cds_full_rna = mrna_design.assemble_construct(cds_dna)
    assert "U" in full_mrna
    assert "T" not in full_mrna
    assert len(full_mrna) > len(cds_full_rna)


def test_demo_mode_end_to_end():
    """Test deterministic synthetic demo mode execution end-to-end."""
    main_cli.run_demo_mode()
    # Check demo run output directory exists
    demo_dirs = [d for d in paths.RESULTS.iterdir() if d.is_dir() and d.name.startswith("run_DEMO_")]
    assert len(demo_dirs) > 0

    latest_demo = sorted(demo_dirs, reverse=True)[0]
    assert (latest_demo / "step1" / "sorted.bam").exists()
    assert (latest_demo / "step2" / "filtered_variants.vcf.gz").exists()
    assert (latest_demo / "step3" / "hla_alleles.txt").exists()
    assert (latest_demo / "step4" / "candidate_neoantigens.tsv").exists()
    assert (latest_demo / "step5" / "ranked_neoantigens.tsv").exists()
    assert (latest_demo / "step6" / "ordered_epitopes.fasta").exists()
    assert (latest_demo / "step7" / "A_balanced" / "vaccine_mrna.fasta").exists()
    assert (latest_demo / "step9" / "vaccine_report.md").exists()
