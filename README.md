# example1

python -c "import duckdb; print('DuckDB:', duckdb.__version__)"

python -c "import pyarrow; print('PyArrow:', pyarrow.__version__)"

python -c "import openpyxl; print('OpenPyXL:', openpyxl.__version__)"

python -u merge_ard_files_v5.py 2>&1 | tee /mnt/quasar/output/merge_v5.log
