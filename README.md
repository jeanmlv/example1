# example1

from pathlib import Path
import shutil
import os

# CONFIGURATION
STUDY = "CNTO1959UCO3004-ASTRO"
LOAD = "load-2492"

SOURCE_ROOT = Path(
    "/domino/datasets/clinical-trial-data"
)

DESTINATION_ROOT = Path(
    "/domino/datasets/local/clinical_trial_data"
)

source = SOURCE_ROOT / STUDY / LOAD
destination = DESTINATION_ROOT / STUDY / LOAD

# VALIDATION
print(f"Source: {source}")
print(f"Destination: {destination}")

if not source.is_dir():
    raise FileNotFoundError(
        f"Source folder not found: {source}"
    )

if not DESTINATION_ROOT.is_dir():
    raise FileNotFoundError(
        f"Destination dataset not found: {DESTINATION_ROOT}"
    )

if not os.access(DESTINATION_ROOT, os.W_OK):
    raise PermissionError(
        "No write permission on destination dataset."
    )

if destination.exists():
    raise FileExistsError(
        f"Destination already exists: {destination}"
    )

# FILE INVENTORY
source_files = {
    str(f.relative_to(source)): f.stat().st_size
    for f in source.rglob("*")
    if f.is_file()
}

total_size = sum(source_files.values())

print(f"Files to copy: {len(source_files)}")
print(f"Total size: {total_size / 1024**3:.2f} GB")

# COPY
destination.parent.mkdir(
    parents=True,
    exist_ok=True
)

print("Copying files...")

shutil.copytree(source, destination)

# POST-COPY VALIDATION
destination_files = {
    str(f.relative_to(destination)): f.stat().st_size
    for f in destination.rglob("*")
    if f.is_file()
}

if source_files == destination_files:
    print("SUCCESS: Copy validation passed.")
    print(f"Files copied: {len(destination_files)}")
else:
    raise RuntimeError(
        "Copy validation failed. Check destination."
    )

print("Process completed.")
