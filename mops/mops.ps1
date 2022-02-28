[CmdletBinding()]
param (
    [Parameter()]
    [string]
    $OutFile = "./update-info.dat"
)

Import-Module AngleParse

$check = & $PSScriptRoot/check-update.ps1 -NoSaveHashFile -OutFile $OutFile

if ($check){
    #& $PSScriptRoot/update-json.ps1

    #.$PSScriptRoot/download-img.ps1
    #.$PSScriptRoot/generate-webp.ps1
    
    #NOTE: 現状は4komaData.jsonを自動生成しないのでReturnNewContentOnlyオプションで最短実行する
    $newContent = & $PSScriptRoot/update-json -ReturnNewContentOnly
    & $PSScriptRoot/update-feed.ps1 -DataObject $newContent
    $check.Hash | Out-File $OutFile -Encoding utf8 -NoNewline

    return $true

}else{
    Write-Debug "Has not update."

    return $false
}


