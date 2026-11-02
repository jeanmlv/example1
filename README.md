# example1

$json = Get-Clipboard -Raw | ConvertFrom-Json

$env:THEA_API_KEY = $json.key

Remove-Variable json


Write-Host "API Key configured:" ([bool]$env:THEA_API_KEY)
Write-Host "Key length:" $env:THEA_API_KEY.Length


Set-Clipboard -Value ""

python .\00_test_thea_auth.py


Remove-Item Env:THEA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:THEA_TOKEN -ErrorAction SilentlyContinue

$env:THEA_API_KEY = Read-Host "Paste the new API Key"
