[CmdletBinding()]
param (
    [Parameter()]
    [string]
    $OutFile = "./update-info.dat",
    [switch]
    $ForceCheck
)

Import-Module AngleParse

$check = & $PSScriptRoot/check-update.ps1 -NoSaveHashFile -OutFile $OutFile

if ($check -or $ForceCheck){

    #
    & $PSScriptRoot/update-json.ps1
    & $PSScriptRoot/generate-4komaDataJs.ps1
    & $PSScriptRoot/download-img.ps1 -OnlyRecently
    & $PSScriptRoot/generate-webp.ps1 -OnlyRecently
    
    #NOTE: 現状は4komaData.jsonを自動生成しないのでReturnNewContentOnlyオプションで最短実行する
    $newContent = & $PSScriptRoot/update-json -ReturnNewContentOnly -Debug
    Write-Debug "new-content: $($newContent | ConvertTo-Json)"
    & $PSScriptRoot/update-feed.ps1 -DataObject $newContent -Debug
    $check.Hash | Out-File $OutFile -Encoding utf8 -NoNewline

    return $true

}else{
    Write-Debug "Has not update."

    return $false
}


