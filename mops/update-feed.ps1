[CmdletBinding()]
param (
    [Parameter()]
    [string]
    $OutFile = "feed.atom"
    ,$update = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
    ,$published = (Get-Date $update -Format "yyyyMMddHHmm")
    ,$auther = "iranika"
    ,$entry_url = "https://movue.iranika.info/#/?page=latest"
    ,$JsonFile = "./4komaData.json"
    ,$lastImage = (& $PSScriptRoot/get-lastImage.ps1)
    ,$DataObject = "null"
)

if (!(Test-Path $OutFile)){
  $FeedDefault = @"
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/" xml:lang="ja-JP">
  <id>tag:iranika.github.io,2019:movue.iranika.info</id>
  <link type="text/html" rel="alternate" href="https://movue.iranika.info" />
  <link type="application/atom+xml" rel="self" href="https://mo4koma.iranika.info/feed.atom" />
  <title>みちくさびゅあー</title>
  <updated>2020-01-26T01:00:54+09:00</updated>
  <!--insertEntry-->
</feed>
"@
  $FeedDefault | Out-File $OutFile -Encoding utf8 
}

if ($DataObject -eq "null"){
  $lastImage = & $PSScriptRoot/get-lastImage.ps1
}else{
  $lastImage = & $PSScriptRoot/get-lastImage.ps1 -DataObject $DataObject
}

Write-Debug "last-image: $lastImage"

$insertItem = @"
  <!--insertEntry-->
  <entry>
    <id>tag:iranika.github.io,2019:Repository/194400309/$($published)</id>
    <updated>$($update)</updated>
    <published>$($update)</published>
    <link rel="alternate" type="text/html" href="$($entry_url)"/>
    <title>$($lastImage.title)</title>
    <content type="html" xml:lang="ja">$($lastImage.url)</content>
    <author>
      <name>$($auther)</name>
    </author>
  </entry>
"@

$newFeed = (Get-Content $OutFile) -replace "^.+<!--insertEntry-->", $insertItem

Write-Debug "$newFeed"

$newFeed | Out-File $OutFile -Encoding utf8