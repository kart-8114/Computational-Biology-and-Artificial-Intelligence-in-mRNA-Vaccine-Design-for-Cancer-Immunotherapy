"""
Download and decompress the hg38 reference genome from UCSC.

Output: reference/hg38.fa (~3.5 GB uncompressed)

Indexing (run after Docker image is built):
    docker compose run --rm index-reference

Run from the project root:
    uv run --with requests --with tqdm --no-project python scripts/download_reference.py
"""

import gzip
import shutil
import time
from pathlib import Path

import requests
from tqdm import tqdm

URL = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz"
ROOT = Path(__file__).resolve().parent.parent
OUT_GZ = ROOT / "reference" / "hg38.fa.gz"
OUT_FA = ROOT / "reference" / "hg38.fa"


def download(url: str, dest: Path, max_retries: int = 15) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        head_resp = requests.head(url, headers=headers, timeout=30, allow_redirects=True)
        total = int(head_resp.headers.get("content-length", 0))
    except Exception:
        total = 0

    downloaded = dest.stat().st_size if dest.exists() else 0
    if total and downloaded >= total:
        print(f"File already complete ({downloaded} bytes).")
        return

    mode = "ab" if downloaded > 0 else "wb"

    with open(dest, mode) as f, tqdm(
        desc="Downloading hg38.fa.gz",
        total=total if total else None,
        initial=downloaded,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for attempt in range(1, max_retries + 1):
            downloaded = dest.stat().st_size if dest.exists() else 0
            if total and downloaded >= total:
                break

            req_headers = dict(headers)
            if downloaded > 0:
                req_headers["Range"] = f"bytes={downloaded}-"

            try:
                with requests.get(url, headers=req_headers, stream=True, timeout=60) as r:
                    if r.status_code in (200, 206):
                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)
                                f.flush()
                                bar.update(len(chunk))
                    elif r.status_code == 416:  # Range Not Satisfiable (already fully downloaded)
                        break
                    else:
                        r.raise_for_status()

                downloaded = dest.stat().st_size if dest.exists() else 0
                if total == 0 or downloaded >= total:
                    break
            except Exception as e:
                downloaded = dest.stat().st_size if dest.exists() else 0
                bar.n = downloaded
                bar.refresh()
                if attempt < max_retries:
                    print(
                        f"\n[Warning] Connection interrupted ({e}). Retrying ({attempt}/{max_retries}) in 5s from byte {downloaded}..."
                    )
                    time.sleep(5)
                else:
                    raise e


def decompress(src: Path, dest: Path) -> None:
    print(f"Decompressing {src.name} ...")
    with gzip.open(src, "rb") as f_in, open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    src.unlink()
    print(f"Done — {dest}")


def create_fai_index_python(fa_path: Path) -> None:
    fai_path = Path(str(fa_path) + ".fai")
    if fai_path.exists():
        print(f"Reference index {fai_path.name} already exists.")
        return

    print(f"Generating FASTA index {fai_path.name}...")
    offset = 0
    name = None
    length = 0
    line_blen = 0
    line_len = 0
    curr_offset = 0

    with open(fa_path, "rb") as f_in, open(fai_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            line_bytes = len(line)
            if line.startswith(b">"):
                if name is not None:
                    f_out.write(f"{name}\t{length}\t{curr_offset}\t{line_blen}\t{line_len}\n")
                name = line[1:].split()[0].decode("ascii", errors="ignore")
                length = 0
                line_blen = 0
                line_len = 0
                curr_offset = offset + line_bytes
            else:
                clean_len = len(line.rstrip(b"\r\n"))
                if line_blen == 0:
                    line_len = line_bytes
                    line_blen = clean_len
                length += clean_len
            offset += line_bytes
        if name is not None:
            f_out.write(f"{name}\t{length}\t{curr_offset}\t{line_blen}\t{line_len}\n")
    print(f"FASTA index created: {fai_path}")


def index_reference(fa_path: Path) -> None:
    fai_path = Path(str(fa_path) + ".fai")
    if not fai_path.exists():
        samtools = shutil.which("samtools")
        if samtools:
            print(f"Indexing {fa_path.name} with samtools...")
            try:
                import subprocess

                subprocess.run([samtools, "faidx", str(fa_path)], check=True)
                print("Indexing complete.")
            except Exception:
                create_fai_index_python(fa_path)
        else:
            create_fai_index_python(fa_path)


if __name__ == "__main__":
    if OUT_FA.exists():
        print(f"{OUT_FA} already exists.")
        index_reference(OUT_FA)
    else:
        download(URL, OUT_GZ)
        decompress(OUT_GZ, OUT_FA)
        index_reference(OUT_FA)
        print("\nReference genome download and setup complete!")
