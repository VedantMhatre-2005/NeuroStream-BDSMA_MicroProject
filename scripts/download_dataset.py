#!/usr/bin/env python3
"""
PhysioNet EEGMMIDB Dataset Downloader
Downloads genuine EEG recordings (EDF format) from PhysioNet.
Dataset: https://physionet.org/content/eegmmidb/1.0.0/
"""

import os
import sys
import json
import time
import urllib.request
from typing import List, Dict

BASE_URL = "https://physionet.org/files/eegmmidb/1.0.0"
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw"))

# Default selection: Motor imagery runs for left vs right fist (Runs 4, 8, 12)
DEFAULT_PARTICIPANTS = ["S001", "S002", "S003"]
DEFAULT_RUNS = ["R04", "R08", "R12"]

def get_manifest_path() -> str:
    return os.path.join(DATA_DIR, "manifest.json")

def load_manifest() -> Dict:
    manifest_path = get_manifest_path()
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"dataset": "EEGMMIDB", "version": "1.0.0", "files": {}}

def save_manifest(manifest: Dict):
    manifest_path = get_manifest_path()
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

def validate_edf_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False
    size = os.path.getsize(file_path)
    if size < 10000: # EDF files should be at least ~10KB
        return False
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
            # Standard EDF begins with '0       '
            if header.startswith(b"0"):
                return True
    except Exception:
        return False
    return False

def download_file(url: str, dest_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        headers = {"User-Agent": "NeuroStream-EDF-Downloader/1.0"}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 64 * 1024
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    sys.stdout.write(f"\r  Progress: {pct:.1f}% ({downloaded / 1024 / 1024:.2f} MB)")
                    sys.stdout.flush()
        print()
        return validate_edf_file(dest_path)
    except Exception as e:
        print(f"\n  Error downloading {url}: {e}")
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception:
                pass
        return False

def download_dataset(participants: List[str] = None, runs: List[str] = None):
    participants = participants or DEFAULT_PARTICIPANTS
    runs = runs or DEFAULT_RUNS
    
    os.makedirs(DATA_DIR, exist_ok=True)
    manifest = load_manifest()
    
    print("=" * 60)
    print(" PhysioNet EEGMMIDB Dataset Acquisition")
    print(f" Target Directory: {DATA_DIR}")
    print(f" Participants: {participants}")
    print(f" Runs: {runs} (Motor Imagery: Left/Right Fist)")
    print("=" * 60)

    total_downloaded = 0
    total_skipped = 0

    for subject in participants:
        subject_dir = os.path.join(DATA_DIR, subject)
        os.makedirs(subject_dir, exist_ok=True)

        for run in runs:
            filename = f"{subject}{run}.edf"
            dest_file = os.path.join(subject_dir, filename)
            url = f"{BASE_URL}/{subject}/{filename}"

            print(f"[{subject}] Checking {filename}...")

            if validate_edf_file(dest_file):
                print(f"  -> File already exists and is valid ({os.path.getsize(dest_file) / 1024 / 1024:.2f} MB). Skipping.")
                total_skipped += 1
                manifest["files"][filename] = {
                    "participant": subject,
                    "run": run,
                    "path": dest_file,
                    "size_bytes": os.path.getsize(dest_file),
                    "valid": True,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                continue

            print(f"  -> Downloading from {url}...")
            success = download_file(url, dest_file)
            
            # Also download event file if available
            event_filename = f"{filename}.event"
            event_url = f"{url}.event"
            event_dest = os.path.join(subject_dir, event_filename)
            try:
                urllib.request.urlretrieve(event_url, event_dest)
            except Exception:
                pass

            if success:
                print(f"  -> Successfully downloaded and verified {filename}.")
                total_downloaded += 1
                manifest["files"][filename] = {
                    "participant": subject,
                    "run": run,
                    "path": dest_file,
                    "size_bytes": os.path.getsize(dest_file),
                    "valid": True,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                print(f"  -> Failed to validate {filename}.")

    save_manifest(manifest)
    print("=" * 60)
    print(f"Acquisition Summary: {total_downloaded} downloaded, {total_skipped} skipped.")
    print(f"Total valid recordings in manifest: {len(manifest['files'])}")
    print(f"Manifest written to: {get_manifest_path()}")
    print("=" * 60)
    return total_downloaded + total_skipped

if __name__ == "__main__":
    download_dataset()

