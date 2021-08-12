Set-Location $PSScriptRoot/4koma/ja

(Get-ChildItem -Name -Filter "*.jpg") | % -Parallel {
    ffmpeg -n -i $_ ($_ -replace ".jpg",".webp")
}

Set-Location $PSScriptRoot