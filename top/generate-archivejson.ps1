[CmdletBinding()]
param (
    $archivesUrl = "https://mo4koma.iranika.info/top/archives",
    $outfile = "$PSScriptRoot/archives.json"
)


$files = (Get-ChildItem -Path $PSScriptRoot/archives/).Name

$json = @{
    archivesUrl = $archivesUrl;
    files = $files;
}

ConvertTo-Json $json > $outfile