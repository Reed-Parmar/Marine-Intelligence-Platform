"""
Dataset Acquisition & Verification Module for Fish4Knowledge (F4K)
Marine Species Ground-Truth Benchmark.

Official Source: University of Edinburgh (EU FP7 Fish4Knowledge Project)
Ground-Truth URL: https://homepages.inf.ed.ac.uk/rbf/Fish4Knowledge/GROUNDTRUTH/RECOG/
"""

import io
import os
import tarfile
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

F4K_BASE_URL = "https://homepages.inf.ed.ac.uk/rbf/Fish4Knowledge/GROUNDTRUTH/RECOG"
CLASS_ID_URL = f"{F4K_BASE_URL}/class_id.csv"
ARCHIVE_BASE_URL = f"{F4K_BASE_URL}/Archive/fish_image"

SPECIES_CATALOG: Dict[int, Dict[str, str]] = {
    1: {"name": "Dascyllus reticulatus", "common": "Two-stripe damselfish", "family": "Pomacentridae"},
    2: {"name": "Plectroglyphidodon dickii", "common": "Blackbar damselfish", "family": "Pomacentridae"},
    3: {"name": "Chromis chrysura", "common": "Japanese damselfish", "family": "Pomacentridae"},
    4: {"name": "Amphiprion clarkii", "common": "Yellowtail clownfish", "family": "Pomacentridae"},
    5: {"name": "Chaetodon lunulatus", "common": "Oval butterflyfish", "family": "Chaetodontidae"},
    6: {"name": "Chaetodon trifascialis", "common": "Chevron butterflyfish", "family": "Chaetodontidae"},
    7: {"name": "Myripristis kuntee", "common": "Shoulderspot soldierfish", "family": "Holocentridae"},
    8: {"name": "Acanthurus nigrofuscus", "common": "Brown surgeonfish", "family": "Acanthuridae"},
    9: {"name": "Hemigymnus fasciatus", "common": "Barred thicklip wrasse", "family": "Labridae"},
    10: {"name": "Neoniphon sammara", "common": "Sammara squirrelfish", "family": "Holocentridae"},
    11: {"name": "Abudefduf vaigiensis", "common": "Indo-Pacific sergeant", "family": "Pomacentridae"},
    12: {"name": "Canthigaster valentini", "common": "Valentin's sharpnose puffer", "family": "Tetraodontidae"},
    13: {"name": "Pomacentrus moluccensis", "common": "Lemon damselfish", "family": "Pomacentridae"},
    14: {"name": "Zebrasoma scopas", "common": "Twotone tang", "family": "Acanthuridae"},
    15: {"name": "Hemigymnus melapterus", "common": "Blackeye thicklip wrasse", "family": "Labridae"},
    16: {"name": "Lutjanus fulvus", "common": "Blacktail snapper", "family": "Lutjanidae"},
    17: {"name": "Scolopsis bilineata", "common": "Two-lined monocle bream", "family": "Nemipteridae"},
    18: {"name": "Scaridae", "common": "Parrotfish", "family": "Scaridae"},
    19: {"name": "Pempheris vanicolensis", "common": "Vanikoro sweeper", "family": "Pempheridae"},
    20: {"name": "Zanclus cornutus", "common": "Moorish idol", "family": "Zanclidae"},
    21: {"name": "Neoglyphidodon nigroris", "common": "Black-and-gold chromis", "family": "Pomacentridae"},
    22: {"name": "Balistapus undulatus", "common": "Orange-lined triggerfish", "family": "Balistidae"},
    23: {"name": "Siganus fuscescens", "common": "Mottled spinefoot", "family": "Siganidae"},
}


def download_file_with_retry(url: str, dest_path: Path, max_retries: int = 5, timeout: int = 60) -> bool:
    """Download a file with user-agent, streaming, and automatic retry on DNS / network blips."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded_size = 0
                with open(temp_path, "wb") as out_file:
                    while True:
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded_size += len(chunk)

                if total_size > 0 and downloaded_size < total_size:
                    raise IOError(f"Incomplete download: {downloaded_size}/{total_size} bytes")

            # Rename atomically upon complete download
            if temp_path.exists():
                if dest_path.exists():
                    dest_path.unlink()
                temp_path.rename(dest_path)
            return True
        except Exception as e:
            print(f"[Attempt {attempt}/{max_retries}] Download error for {url}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            if attempt < max_retries:
                sleep_sec = 2 ** attempt
                print(f"Retrying in {sleep_sec} seconds...")
                time.sleep(sleep_sec)
            else:
                print(f"Failed to download {url} after {max_retries} attempts.")
                return False
    return False


def fetch_class_mapping(dest_dir: Path) -> Path:
    """Fetch official class_id.csv mapping."""
    dest_path = dest_dir / "class_id.csv"
    if not dest_path.exists():
        print(f"Fetching official class mapping from {CLASS_ID_URL}...")
        download_file_with_retry(CLASS_ID_URL, dest_path)
    return dest_path


def download_species_archives(
    raw_dir: Path,
    species_ids: List[int],
    max_images_per_class: Optional[int] = None
) -> Dict[int, Path]:
    """
    Downloads and extracts specified species archives from Edinburgh F4K repository.
    """
    archives_dir = raw_dir / "archives"
    images_dir = raw_dir / "images"
    archives_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    downloaded = {}
    for sid in species_ids:
        tar_name = f"fish_{sid:02d}.tar"
        tar_url = f"{ARCHIVE_BASE_URL}/{tar_name}"
        tar_path = archives_dir / tar_name
        species_dir = images_dir / f"species_{sid:02d}"
        species_dir.mkdir(parents=True, exist_ok=True)

        existing_images = list(species_dir.glob("*.png"))
        if len(existing_images) > 0:
            print(f"Species {sid:02d} ({SPECIES_CATALOG[sid]['name']}) already extracted: {len(existing_images)} images.")
            downloaded[sid] = species_dir
            continue

        # Check if tar is valid or needs download
        need_download = True
        if tar_path.exists():
            try:
                with tarfile.open(tar_path, "r") as t:
                    # Test if readable
                    _ = t.getmembers()
                need_download = False
            except Exception:
                print(f"Found corrupt or incomplete archive {tar_path}, removing...")
                tar_path.unlink()
                need_download = True

        if need_download:
            print(f"Downloading {tar_name} from {tar_url}...")
            ok = download_file_with_retry(tar_url, tar_path)
            if not ok:
                print(f"Failed to download {tar_name}, skipping.")
                continue

        print(f"Extracting {tar_name} to {species_dir}...")
        try:
            with tarfile.open(tar_path, "r") as tar:
                members = [m for m in tar.getmembers() if m.isfile() and m.name.lower().endswith(".png")]
                if max_images_per_class and len(members) > max_images_per_class:
                    members = members[:max_images_per_class]
                for m in members:
                    f_name = Path(m.name).name
                    extracted_path = species_dir / f_name
                    if not extracted_path.exists():
                        f_obj = tar.extractfile(m)
                        if f_obj:
                            extracted_path.write_bytes(f_obj.read())
            extracted_count = len(list(species_dir.glob("*.png")))
            print(f"Extracted {extracted_count} images for species {sid:02d}.")
            downloaded[sid] = species_dir
        except Exception as e:
            print(f"Error extracting {tar_name}: {e}")

    return downloaded
