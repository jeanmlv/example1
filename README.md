# example1

processed = processed.reset_index(drop=True)

print("RAW columns:", raw.columns.tolist())
print("PROCESSED columns:", processed.columns.tolist())

python .\02_generate_video_reports.py --input "video_inventory_output_power/all_video_inventory.csv" --output-dir "video_reports_output_power"

python -c "import pandas as pd; d=pd.read_csv('video_inventory_output_power/all_video_inventory.csv',dtype=str).fillna(''); print(d.groupby('data_type').agg(video_files=('filename','size'),unique_patients=('patient_id','nunique')).to_string()); print(d[['data_type','site','patient_id','visit','relative_path']].head(10).to_string(index=False))"
