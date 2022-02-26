[CmdletBinding()]
param (
    [Parameter()]
    [String]
    $SiteUrl = "http://momoirocode.web.fc2.com/mocode.html"
    ,$OutFile = "update-hash.dat"
    ,$ReadFile = $OutFile
    ,[switch]$NoSaveHashFile
)


$content = [String](Invoke-WebRequest $SiteUrl -UseBasicParsing).Content

$stream = [IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes($content))

$hash = Get-FileHash -InputStream $stream -Algorithm SHA256

$oldHash = (Get-Content $ReadFile -Raw)

echo $hash.Hash
echo $oldHash
if ($oldHash -eq $hash.Hash){
    echo "hash has not updated."
}else {
    echo "hash has update."
    if (!$NoSaveHashFile){
        $hash.Hash | Out-File -FilePath $OutFile -Encoding utf8 -NoNewline
        echo "hash saved $OutFile"
    }
}

