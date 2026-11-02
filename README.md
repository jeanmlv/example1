# example1

python -c "import pandas as pd; d=pd.read_csv('video_inventory_output_anthem/processed_video_inventory.csv',dtype=str).fillna(''); print(d[['patient_id','site','visit','relative_path']].head(10).to_string(index=False))"
