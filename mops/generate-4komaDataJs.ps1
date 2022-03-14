[CmdletBinding()]
param (
    [Parameter()]
    [string]
    $InputFile = "./4komaData.json"
    ,$OutFile = "./4komaData.js"
    ,$JsMinFile = "./4komaDataMin.js"

)

$json = Get-Content $InputFile | ConvertFrom-Json

$js = $json | % {
    #$result = $_
    $_.ImagesUrl = $_.ImagesUrl | % {
        return (New-Object System.Uri((New-Object System.Uri("https://mo4koma.iranika.info/4koma/ja/")), $_)).AbsoluteUri
    }
    if ($_.ImagesUrl -is [System.String]){
        $_.ImagesUrl = [System.String[]]@($_.ImagesUrl)
    }
    return $_
}

"pageData = " > $OutFile
$js | Select-Object Title,ImagesUrl,Index | ConvertTo-Json >> $OutFile

#Note: 破壊的変更で$jsを壊しちゃうので上記の後ろで実行する
$jsMin = $js | % {
    $_.ImagesUrl = $_.ImagesUrl | % {
        return $_ -replace "https://mo4koma.iranika.info/4koma/ja"
    }
    if ($_.ImagesUrl -is [System.String]){
        $_.ImagesUrl = [System.String[]]@($_.ImagesUrl)
    }
    return $_
}

"pageData = " > $JsMinFile
$jsMin | Select-Object Title,ImagesUrl,Index | ConvertTo-Json >> $JsMinFile