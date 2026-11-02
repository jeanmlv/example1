# example1

$secureKey = Read-Host "Enter THEA API Key" -AsSecureString
$env:THEA_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
Remove-Variable secureKey
Remove-Item Env:THEA_TOKEN -ErrorAction SilentlyContinue



python 01_extract_video_inventory_multistudy.py --study ANTHEM --mode test --max-folders 30 --output-dir "video_inventory_output_anthem"

INFO | Authenticated; 1 study folders selected; mode=test
INFO | Study 1/1: ...ANTHEM...
INFO | rawdata: folders=30, ...
INFO | processed: folders=30, ...
INFO | Finished: ... video items.


python 01_extract_video_inventory_multistudy.py --study ANTHEM --mode full --output-dir "video_inventory_output_anthem"

video_inventory_output_anthem/
├── all_video_inventory.csv
├── rawdata_video_inventory.csv
├── processed_video_inventory.csv
├── extraction_summary.json
└── extraction.log


python 02_generate_video_reports.py --input "video_inventory_output_anthem/all_video_inventory.csv" --output-dir "video_reports_output_anthem"
