# example1

$json = Get-Clipboard -Raw | ConvertFrom-Json

$env:THEA_API_KEY = $json.key

Remove-Variable json


Write-Host "API Key configured:" ([bool]$env:THEA_API_KEY)
Write-Host "Key length:" $env:THEA_API_KEY.Length


Set-Clipboard -Value ""

python .\00_test_thea_auth.py
