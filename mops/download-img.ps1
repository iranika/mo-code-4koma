[CmdletBinding()]
param (
    [Parameter()]
    [string]
    $InputFile = "4komaData.json"
    ,[switch]$OnlyRecently #直近のみDLするオプション
)

Import-Module AngleParse

$json = Get-Content $InputFile | ConvertFrom-Json
$saveDir = "./4koma/"
if (!(Test-Path "$saveDir/ja")) { mkdir "$saveDir/ja" -Force }

$spfile = Join-Path $saveDir "ja/sp.jpg"
if (!(Test-Path $spfile)){
    $l = New-Object System.Uri((New-Object System.Uri("http://momoirocode.web.fc2.com/")), $spfile)
    Invoke-WebRequest $l -OutFile $spfile
}

if (!$OnlyRecently) {
    $json | % -parallel {
        #$VerbosePreference = $using:VerbosePreference
        $_.ImagesUrl | % {
            $DebugPreference = $using:DebugPreference
            $savePath = Join-Path $using:saveDir "ja/$_"
            $downloadFilePath = Join-Path $using:saveDir $_
            Write-Debug "savePath: $savePath"
            if (Test-Path $savePath){
                Write-Debug "already file exists: $savePath"
            }else{
                Write-Debug "new file"
                $link = New-Object System.Uri((New-Object System.Uri("http://momoirocode.web.fc2.com/")), $downloadFilePath)
                Write-Debug "link: $link"
                Invoke-WebRequest $link -OutFile $savePath
            }        
        }
    }    
}

$json[-2..-1] | % -parallel {
    $_.ImagesUrl | % {
        $DebugPreference = $using:DebugPreference
        $savePath = Join-Path $using:saveDir "ja/$_"
        $downloadFilePath = Join-Path $using:saveDir $_
        Write-Debug "savePath: $savePath"
        Write-Debug "sp-check: $savePath : $($using:spfile)"
        if ($savePath -ne $using:spfile){
            Write-Debug "new file(sp skip mode)"
            $link = New-Object System.Uri((New-Object System.Uri("http://momoirocode.web.fc2.com/")), $downloadFilePath)
            Write-Debug "link: $link"
            Invoke-WebRequest $link -OutFile $savePath
        }
    }
}