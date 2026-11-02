# example1

Remove-Item Env:THEA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:THEA_TOKEN -ErrorAction SilentlyContinue

$env:THEA_API_KEY = (Get-Clipboard -Raw).Trim()

Write-Host "API Key configured:" ([bool]$env:THEA_API_KEY)
Write-Host "Key length:" $env:THEA_API_KEY.Length




Remove-Item Env:THEA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:THEA_TOKEN -ErrorAction SilentlyContinue

$env:THEA_API_KEY = (Get-Clipboard -Format Text).Trim()

Write-Host "Key length:" $env:THEA_API_KEY.Length
