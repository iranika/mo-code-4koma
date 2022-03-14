param (
    [Parameter()][String]$JsonFile = "4komaData.json"
    ,$OutFile = $JsonFile
    ,[switch] $ReturnNewContentOnly
)

$json = (get-content -Raw $JsonFile) | ConvertFrom-Json

$patch2_3 = @(
    [pscustomobject]@{
        Title = "隣町より遠く"
        BaseUrl = "http://momoirocode.web.fc2.com/4koma/2-3.html"
        ImagesUrl = @("./2.jpg")
    },
    [pscustomobject]@{
        Title = "手渡し"
        BaseUrl = "http://momoirocode.web.fc2.com/4koma/2-3.html"
        ImagesUrl = @("./3.jpg")
    }
)

$result = @($json[0]) + $patch2_3 + $json[2..($json.Length)]

# indexの追加
0..($result.Count -1) | % {
    if ($result[$_].Title -eq "りれきしょ"){
        $result[$_] | Add-Member -MemberType NoteProperty -Name "Index" -Value "ri"
    }elseif($_ -ge 81){
        $result[$_] | Add-Member -MemberType NoteProperty -Name "Index" -Value $_
    }else{
        $result[$_] | Add-Member -MemberType NoteProperty -Name "Index" -Value ($_ + 1)
    }
}

$result | ConvertTo-Json | Out-File $OutFile -Encoding utf8
$result