# example1

Remove-Item Env:THEA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:THEA_TOKEN -ErrorAction SilentlyContinue

$secureKey = Read-Host "Enter THEA API Key" -AsSecureString
$env:THEA_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password.Trim()
Remove-Variable secureKey


if ($env:THEA_API_KEY) {
    Write-Host "API Key configured - Length:" $env:THEA_API_KEY.Length
} else {
    Write-Host "API Key missing"
}
