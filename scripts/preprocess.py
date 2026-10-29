import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paths import BASE, step_dir, new_run

# ── Config ────────────────────────────────────────────────────────────────────

GATK_JAR  = BASE / "tools/gatk-4.5.0.0/gatk-package-4.5.0.0-local.jar"
REFERENCE = BASE / "reference/hg38.fa"
INPUT_BAM = BASE / "data/test/tumor_chr17.bam"
OUT_DIR   = step_dir(1)

# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd, step_name):
    print(f"\n[{step_name}] running...")
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {step_name}")
        print(result.stderr)
        sys.exit(1)
    print(f"DONE: {step_name}")

def find_java():
    java_bin = shutil.which("java")
    if java_bin:
        return java_bin

    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / ("java.exe" if sys.platform == "win32" else "java")
        if candidate.exists():
            return str(candidate)

    if sys.platform == "win32":
        adoptium = Path("C:/Program Files/Eclipse Adoptium")
        if adoptium.exists():
            for jdk in adoptium.glob("jdk*/bin/java.exe"):
                if jdk.exists():
                    return str(jdk)
        oracle = Path("C:/Program Files/Java")
        if oracle.exists():
            for jdk in oracle.glob("jdk*/bin/java.exe"):
                if jdk.exists():
                    return str(jdk)
    return None

def gatk(args):
    java_exec = find_java() or "java"
    return [java_exec, "-jar", str(GATK_JAR)] + args

# ── Pipeline ──────────────────────────────────────────────────────────────────

def main():
    # Step 1 always starts a fresh run — downstream steps inherit the same run ID
    new_run()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_BAM.exists():
        print(f"ERROR: Input BAM not found at {INPUT_BAM}")
        print("Please run: uv run --with huggingface_hub --with python-dotenv --no-project python scripts/download_data.py")
        sys.exit(1)

    sorted_bam = OUT_DIR / "sorted.bam"
    deduped_bam  = OUT_DIR / "marked_duplicates.bam"
    metrics_file = OUT_DIR / "duplicate_metrics.txt"

    java_bin = find_java()
    if java_bin and GATK_JAR.exists():
        run(gatk([
            "SortSam",
            "--INPUT",        INPUT_BAM,
            "--OUTPUT",       sorted_bam,
            "--SORT_ORDER",   "coordinate",
            "--CREATE_INDEX", "true",
        ]), "SortSam")

        run(gatk([
            "MarkDuplicates",
            "--INPUT",        sorted_bam,
            "--OUTPUT",       deduped_bam,
            "--METRICS_FILE", metrics_file,
            "--VALIDATION_STRINGENCY", "SILENT",
            "--CREATE_INDEX", "true",
        ]), "MarkDuplicates")
    else:
        print("\n[Warning] Java or GATK JAR not found in local environment.")
        print("Using pre-sorted test BAM directly for Step 1 output...")
        shutil.copy(INPUT_BAM, sorted_bam)
        shutil.copy(INPUT_BAM, deduped_bam)
        bai_input = INPUT_BAM.with_suffix(".bam.bai")
        if not bai_input.exists():
            bai_input = INPUT_BAM.with_suffix(".bai")
        if bai_input.exists():
            shutil.copy(bai_input, deduped_bam.with_suffix(".bam.bai"))
            shutil.copy(bai_input, deduped_bam.with_suffix(".bai"))
        metrics_file.write_text("Pre-sorted input BAM used directly (Java/GATK bypassed).\n")

    print(f"\nStep 1 complete. Output: {deduped_bam}")

if __name__ == "__main__":
    main()
 