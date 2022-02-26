[CmdletBinding()]
param (
    [Parameter()]
    [String]
    $SiteUrl = "http://momoirocode.web.fc2.com/mocode.html"
    ,$OutFile = "4komaData.json"
)

$dom = Invoke-WebRequest $SiteUrl | Select-HtmlContent "li", @{
    title = "a"
    href = "a", ([AngleParse.Attr]::Href)
}

$list = $dom | % {
    #NOTE: 相対参照から絶対参照に変更、
    if (([string]$_.href).Contains("http://momoirocode.web.fc2.com")){
        return $_
    }else{
        $result = $_
        $result.href = $_.href -replace "^/", "http://momoirocode.web.fc2.com/"
        return $result
    }
}

class PageData {
    [string] $Title
    [string] $BaseUrl
    [string[]] $ImagesUrl
    PageData([string]$title, [string]$baseUrl, [string[]]$images){
        $this.Title = $title
        $this.BaseUrl = $baseUrl
        $this.ImagesUrl = $images
    }
}

$obj = $list | % {
    $imgs = Invoke-WebRequest $_.href | Select-HtmlContent "img", @{
        src = [AngleParse.Attr]::Src
    } | ? { !([string]$_.src).Contains("counter_img.php?id=50") } | % { $_.src }
    
    $result = New-Object PageData($_.title, $_.href, $imgs)
    Write-Information $result
    return $result
}

$obj
$obj | ConvertTo-Json | Out-File $OutFile -Encoding utf8
