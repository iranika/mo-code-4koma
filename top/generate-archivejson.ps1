[CmdletBinding()]
param (
    $archivesUrl = "https://mo4koma.iranika.info/top/archives",
    $outfile = "$PSScriptRoot/archives.json"
)


$files = (Get-ChildItem -Path $PSScriptRoot/archives/ | Sort-Object -Property Name).Name

$json = [ordered]@{
    archivesUrl = $archivesUrl;
    files = $files;
}

ConvertTo-Json $json > $outfile