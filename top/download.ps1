param(
    $url = "http://momoirocode.web.fc2.com"
)

$filename = (Invoke-WebRequest -Uri "$url/toppage.html").Images[0].src
Invoke-WebRequest -Uri "$url/$filename" -OutFile "./top.jpg"