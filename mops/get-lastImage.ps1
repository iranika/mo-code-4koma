[CmdletBinding()]
param (
    [Parameter()]
    [string]
    $JsonFile = "./4komaData.json"
)

if (!(Test-Path $JsonFile)){
    Write-Error "File is not found. $JsonFile"
}
function Get-LastContent() {
    param (
        [Parameter()]
        [string]
        $_JsonFile = $JsonFile
    )
    $json = (Get-Content -Raw $_JsonFile | ConvertFrom-Json)
    if ($json.Length -eq 0) {
        Write-Warning "No contents in $_JsonFile"
    }
    return $json[-1]
}
  
$lastContent = (Get-LastContent)

$lastImage = ($lastContent.ImagesUrl | ? { $_ -ne "sp.jpg" })[-1]
$lastImageUrl = New-Object System.Uri((New-Object System.Uri("http://momoirocode.web.fc2.com/4koma/")), $lastImage)

class lastContent{
    [string]$title
    [string]$url
    lastContent($_title, $_url){
        $this.title = $_title
        $this.url = $_url
    }
}

return New-Object lastContent($lastContent.Title, $lastImageUrl.AbsoluteUri)