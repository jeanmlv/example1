# example1

/mnt/quasar/venv/bin/python -c "import duckdb, pyarrow, openpyxl; print('Dependencias OK')"

grep -nE 'INPUT_FOLDER|OUTPUT_FOLDER|temp_directory|memory_limit|FILES_TO_MERGE' /mnt/quasar/scripts/merge_ard_files_v4.pygrep -nE 'INPUT_FOLDER|OUTPUT_FOLDER|temp_directory|memory_limit|FILES_TO_MERGE' /mnt/quasar/scripts/merge_ard_files_v4.py

INPUT_FOLDER = Path("/mnt/quasar/input")
OUTPUT_FOLDER = Path("/mnt/quasar/output")

mkdir -p /mnt/quasar/tmp

con.execute("SET temp_directory='/mnt/quasar/tmp'")
con.execute("SET memory_limit='16GB'")

cd /mnt/quasar/scripts
set -o pipefail
TMPDIR=/mnt/quasar/tmp /mnt/quasar/venv/bin/python -u merge_ard_files_v4.py 2>&1 | tee /mnt/quasar/output/merge_v4.log
  
