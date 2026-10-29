# OpenMrnaVaxGen — mRNA Vaccine Pipeline

> **Research use only. Not for clinical or diagnostic use.**

> **This project is an open-source computational pipeline for personalized cancer vaccine design.**

OpenMrnaVaxGen automates the computational workflow for personalized mRNA cancer vaccines. Given tumor/normal sequencing data and a patient's HLA profile, it identifies tumor-specific neoantigens, ranks them by predicted immunogenicity, and encodes the top candidates into an optimized mRNA vaccine sequence ready for wet lab synthesis.

---

## Why this exists

Every cancer patient's tumor carries a unique set of somatic mutations. Some of those mutations produce altered proteins that the immune system can recognize as foreign — these are called **neoantigens**. Which neoantigens are visible to the immune system depends on the patient's HLA alleles, which determine what peptide fragments get displayed on the cell surface.

This pipeline automates the computational workflow: calling somatic variants from tumor/normal sequencing, predicting which mutant peptides bind the patient's specific HLA alleles, ranking candidates by predicted immunogenicity, and assembling the top epitopes into an optimized mRNA construct.

---

## Pipeline Architecture

```
Input: Tumor WES + Normal WES
       ↓
Step 1: Preprocessing          → Clean BAMs             [GATK MarkDuplicates + SortSam]
Step 2: Variant Calling        → Somatic VCF            [GATK Mutect2 + FilterMutectCalls]
Step 3: HLA Typing             → HLA alleles            [Clinical file / Manual HLA Entry]
Step 4: Neoantigen Prediction  → Candidate peptides     [MHCflurry 2.0]
Step 5: Immunogenicity Ranking → Ranked neoantigen list [composite score, IMPROVE weights]
Step 6: Epitope Ordering       → Ordered epitope string [Held-Karp exact TSP / greedy]
Step 7: mRNA Design            → Full mRNA sequence     [VaxPress + ViennaRNA/LinearFold]
Step 8: CodonFM Validation     → Expression scoring     [nvidia/NV-CodonFM-80M] (optional/experimental)
Step 9: Report                 → vaccine_report.md
       ↓
Output: results/run_<sample>_<timestamp>/
```

**Entry A — full:** Raw FASTQs / BAMs → Steps 1 → 2 → 3 → 4 → 5 → 6 → 7 → 9

**Entry B — pre-called:** Existing MAF/VCF → Steps 3 → 4 → 5 → 6 → 7 → 9

---

## Quickstart & Installation

### 1. Prerequisites
- **Python 3.12+**
- **Java 17+** (for GATK variant calling)
- [`uv`](https://github.com/astral-sh/uv) package manager (`pip install uv`)

### 2. Install Dependencies
```powershell
uv sync
```

### 3. Create Required Directories
```powershell
mkdir "data/test", "reference", "results"
```

### 4. Download Reference Genome & Test Dataset
```powershell
# Download and decompress hg38 reference genome (~3.5 GB)
uv run --with requests --with tqdm --no-project python scripts/download_reference.py

# Download HCC1143 tumor/normal BAM dataset
cp .env.example .env
uv run --with huggingface_hub --with python-dotenv --no-project python scripts/download_data.py
```

---

## Running the Application

### 1. Web Application (Streamlit UI)
Launch the interactive web application directly from your terminal:

```powershell
uv run streamlit run app.py
```

Open **[http://localhost:8501](http://localhost:8501)** in your browser. The Overview tab includes an interactive **Preflight System Check** panel that verifies local tool and database availability.

### 2. Fast Synthetic Demo Mode (~2 seconds)
Run the full pipeline end-to-end without downloading large human reference genomes or ML model weights:

```powershell
uv run python main.py --demo
```

### 3. Run Automated Tests
Run the automated test suite using `pytest`:

```powershell
uv run pytest
```

---

## Running Individual Steps via CLI

You can also execute individual pipeline steps from the command line:

```powershell
uv run python scripts/preprocess.py
uv run python scripts/variant.py
uv run python scripts/hla_typing.py --clinical data/test/sample_hla.txt
uv run python scripts/neoantigen_prediction.py
uv run python scripts/candidate_ranking.py
uv run python scripts/epitope_ordering.py
uv run python scripts/mrna_design.py
```

---

## Output Structure

Each run produces a versioned directory under `results/`:

```
results/run_<sample>_<timestamp>/
├── step1/   sorted.bam
├── step2/   filtered_variants.vcf.gz
├── step3/   hla_alleles.txt
├── step4/   candidate_neoantigens.tsv
├── step5/   ranked_neoantigens.tsv  all_scored_candidates.tsv  subclonal_filtered.tsv
├── step6/   ordered_epitopes.fasta  junction_scores.tsv
├── step7/   vaccine_mrna_*.fasta  candidate_comparison.json
└── step9/   vaccine_report.md  figures/
```

The final report (`vaccine_report.md`) includes ranked candidate tables, HLA coverage plots, junction score heatmaps, mRNA construct metrics, and a wet lab synthesis checklist.

---

## Ranking Methodology (IMPROVE Model)

Candidates are scored using a composite immunogenicity metric based on feature importance from [IMPROVE (Frontiers Immunology, 2024)](https://doi.org/10.3389/fimmu.2024.1397590):

| Feature | Weight | Rationale |
|---------|--------|-----------|
| MHCflurry presentation score | 40% | Most predictive of actual antigen presentation |
| Agretopicity (DAI) | 25% | log2(WT affinity / mutant affinity) — higher means T cell repertoire not tolerized to this peptide |
| VAF / clonality | 20% | Clonal mutations present in more tumor cells; clinical standard requires VAF ≥ 0.05 |
| BLOSUM mutation score | 10% | More radical amino acid substitution = more foreign to immune system |
| Foreignness | 5% | BLOSUM kernel similarity between mutant and wildtype peptide |

Candidates are flagged (but not removed) for `NEG_AGRETOPICITY` (mutant binds MHC worse than wildtype) and `LOW_VAF` (0.05–0.10, moderately subclonal).

---

## Epitope Ordering (Held-Karp TSP)

To minimize immunogenic junctional peptides at GPGPG linker boundaries, epitope concatenation order is solved as a Hamiltonian path problem where edge weights are the worst MHCflurry presentation score across all junction peptides between each pair of epitopes. The pipeline uses:

- **Held-Karp exact dynamic programming** for N ≤ 15 epitopes — globally optimal
- **Greedy nearest-neighbor** for N > 15 — O(N²), good approximation

---

## Scientific Background & Disclaimers

Inspired by the research review:
> *"Computational biology and artificial intelligence in mRNA vaccine design for cancer immunotherapy"* (PMC11788159)

**Disclaimer**: This repository is an open-source research software prototype. Computationally prioritized neoantigens are research candidates and are **not** clinically validated vaccine recommendations.

---

## License & Citations

Licensed under the **MIT License**.

If you use this pipeline in your research, please cite the underlying tools:
- **MHCflurry**: O'Donnell et al., *Cell Systems*, 2020
- **VaxPress**: Ju, Ku & Chang, 2023
- **GATK/Mutect2**: Van der Auwera & O'Connor, *Bioinformatics Data Skills*, 2020
- **OptiType**: Szolek et al., *Bioinformatics*, 2014
- **IMPROVE ranking weights**: Frontiers in Immunology, 2024
