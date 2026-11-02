# example1

python .\01_extract_video_inventory_multistudy_filtered.py --study ANTHEM --folder-prefix IMM_Endoscopy --mode test --max-folders 30 --output-dir "video_inventory_output_anthem"

python .\01_extract_video_inventory_multistudy.py --study ANTHEM --folder-prefix IMM_Endoscopy --mode full --output-dir "video_inventory_output_anthem"

python -c "import json; d=json.load(open('video_inventory_output_anthem/extraction_summary.json')); [print(r.get('study_folder'), '|', r.get('data_type'), '|', r.get('videos_found'), 'videos |', r.get('status')) for r in d['results']]"

python .\02_generate_video_reports.py --help
