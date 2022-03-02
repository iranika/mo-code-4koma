[CmdletBinding()]
param (
    [Parameter()]
    [switch]
    $OnlyRecently
)

$base = pwd
Set-Location ./4koma/ja

if ($OnlyRecently){
    (Get-ChildItem -Name -Filter "*.jpg" | Sort-Object { $_.LastWriteTime })[-1..-5] | % -Parallel {
        if ($_ -in $last5){
            ffmpeg -n -i $_ ("webp/$_" -replace ".jpg",".webp")
        }else{
            ffmpeg -y -i $_ ("webp/$_" -replace ".jpg",".webp")
        }
    }
}else{
    $last5 = ((Get-ChildItem -Filter "*.jpg") | Sort-Object { $_.LastWriteTime })[-1..-5].Name
    (Get-ChildItem -Name -Filter "*.jpg") | % -Parallel {
        if ($_ -in $last5){
            ffmpeg -n -i $_ ("webp/$_" -replace ".jpg",".webp")
        }else{
            ffmpeg -y -i $_ ("webp/$_" -replace ".jpg",".webp")
        }
    }    
}

Set-Location $base

