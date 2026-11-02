# example1

Remove-Item Env:THEA_TOKEN -ErrorAction SilentlyContinue

$secureKey = Read-Host "Paste THEA API Key" -AsSecureString
$env:THEA_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password.Trim()
Remove-Variable secureKey

python .\00_test_thea_auth.py

python .\01_extract_video_inventory_multistudy.py --study POWER --folder-prefix IMM-Endoscopy --mode test --max-folders 30 --output-dir "video_inventory_output_power"

python .\01_extract_video_inventory_multistudy.py --study POWER --folder-prefix IMM-Endoscopy --mode full --output-dir "video_inventory_output_power"
