# example1

Remove-Item Env:THEA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:THEA_TOKEN -ErrorAction SilentlyContinue

$secureKey = Read-Host "Enter THEA API Key" -AsSecureString
$env:THEA_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password.Trim()
Remove-Variable secureKey


$env:THEA_API_KEY.Length




Remove-Item Env:THEA_API_KEY -ErrorAction SilentlyContinue

$secureKey = Read-Host "Enter THEA API Key" -AsSecureString
$env:THEA_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password.Trim()
Remove-Variable secureKey


python .\00_test_thea_auth.py
