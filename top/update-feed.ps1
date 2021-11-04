param (
    $feedfile =".\feed.atom"
)

$dateTimeOffset = [System.DateTimeOffset]::Now
$id = "tag:iranika.github.io,2019:Repository/194400309/" + $dateTimeOffset.ToString("yyyyMMddHHmmdd")
$updated = $dateTimeOffset.ToString("yyyy-MM-ddTHH:mm:ssK")
$entry = @"
<!--insertEntry-->
  <entry>
    <id>$($id)</id>
    <updated>$($updated)</updated>
    <published>$($updated)</published>
    <link rel="alternate" type="text/html" href="http://momoirocode.web.fc2.com/"/>
    <title>TOP絵が更新されたよ</title>
    <content type="html" xml:lang="ja">https://mo4koma.iranika.info/top/top.jpg</content>
    <author>
      <name>iranika</name>
    </author>
  </entry>
"@

(Get-Content $feedfile) -replace "<!--insertEntry-->", $entry | Out-File -Encoding utf8 $feedfile