[CmdletBinding()]
param (
    [Parameter()]
    [switch]
    $OnlyRecently
)

$base = pwd
Set-Location ./4koma/ja
Write-Debug "current dir: $(pwd)"
if ($OnlyRecently){
    Write-Debug "generate-webp is OnlyRecently mode;"
    (Get-ChildItem -Filter "*.jpg" | Sort-Object -Property LastWriteTime)[-5..-1] | % -Parallel {
        Write-Debug "webp fille: $($_.Name)"
        ffmpeg -y -i $_.Name ("webp/$($_.Name)" -replace ".jpg",".webp") || "ffmpeg was done: $($_.Name)"
    }
}else{
    $last5 = ((Get-ChildItem -Filter "*.jpg") | Sort-Object { $_.LastWriteTime })[-1..-5].Name
    (Get-ChildItem -Filter "*.jpg") | % -Parallel {
        Write-Debug "webp fille: $($_.Name)"
        if ($($_.Name) -in $last5){
            ffmpeg -n -i $_ ("webp/$($_.Name)" -replace ".jpg",".webp")
        }else{
            ffmpeg -y -i $_ ("webp/$($_.Name)" -replace ".jpg",".webp")
        }
    }    
}

Set-Location $base

