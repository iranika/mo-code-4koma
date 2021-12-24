import httpclient
import htmlparser
import streams
import xmltree
import pegs, unicode
import os, times
import uri
import nimquery
import json, marshal
import strformat, sequtils
import times
import nre,options,strutils
import threadpool
{.experimental: "parallel".}


# use get4komaUrl
type 
  PageData = object
    Title: string
    ImagesUrl: seq[string]

const file4komaDataOrg = "4komaData.js.org"
const exportFile4komaData = "4komaData.js"
const exportFile4komaDataMin = "4komaDataMin.js"
const exportFile4komaDataJson = "4komaData.json"
const originalSite = "http://momoirocode.web.fc2.com"
const provideSite = "https://mo4koma.iranika.info/4koma/ja"
#const sqAgent = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.99 Safari/537.36"

proc getItemJsonString(a: XmlNode, domain: Uri): string =
  var titleName: string = $a.innerText
  var imagesUrl: seq[string]
  var client = newHttpClient()
  var res = client.get($(domain / "mocode.html"))
  
  debugEcho $a.attr("href")
  res = client.get($(domain / a.attr("href")))
  let nodes = res.body.newStringStream().parseHtml().querySelectorAll("img")
  for img in nodes:
    if (".jpg" in img.attr("src")) or (".png" in img.attr("src")):
      let image_url = $(domain / "4koma" / img.attr("src").replace("./", ""))
      imagesUrl.add(image_url)
      debugEcho $image_url
  result = $$PageData(Title: titleName, ImagesUrl: imagesUrl)


proc writeJson4komaData*[T](stream: T, url: string) =
  var domain = parseUri(url)
  block uriPathClear:    
    domain.path = ""
    domain.query = ""
    domain.anchor = ""
  var client = newHttpClient()
  var res = client.get($(domain / "mocode.html"))
  var items: seq[tuple[n: int, val: FlowVar[string]]]

  let nodes = res.body.newStringStream().parseHtml().querySelectorAll("li > a")
  stream.write "pageData = [\n"
  parallel: 
    for i, a in nodes:
    #li.child
      var item = spawn getItemJsonString(a, domain)
      items.add((n: i, val: item))
  stream.write items.map(proc (item: tuple[n: int, val: FlowVar[string]]): string = ^item.val).join(",\n")
  stream.write "]"

  
proc update4komaData*() =
  var fp: File = open(file4komaDataOrg, FileMode.fmWrite)
  defer:
    close(fp)
  writeJson4komaData(fp, url=originalSite)
  close(fp)
  #4komaData.jsと4komaData.jsonの生成
  fp = open(file4komaDataOrg, FileMode.fmRead)
  var f4koma = open(exportFile4komaData, FileMode.fmWrite)
  var f4komamin = open(exportFile4komaDataMin, FileMode.fmWrite)
  var f4komajson = open(exportFile4komaDataJson, FileMode.fmWrite)
  defer:
    close(f4koma)
    close(f4komamin)
    close(f4komajson)
  
  while not fp.endOfFile:
    let line = fp.readLine().replace(originalSite & "/4koma", provideSite)
    f4koma.write(line & "\n")
    f4komamin.write(line.replace(provideSite, "") & "\n")
    f4komajson.write(line.replace("pageData = ", "") & "\n")

proc download4komaImage*() =
  if not dirExists("4koma"):
    createDir("4koma")
    createDir("4koma/ja")
  if not dirExists("4koma/ja"):
    createDir("4koma/ja")
  let jsonNode4koma = readFile(file4komaDataOrg).replace("pageData = ", "").parseJson
  let list4koma: seq[PageData] = to(jsonNode4koma, seq[PageData])
  for index,item in list4koma:
    parallel:
      for imgUrl in item.ImagesUrl:
        let saveFilename = imgUrl.replace(re".*4koma","4koma/ja") # save 4koma/filename
        if fileExists(saveFilename) and index + 1 < list4koma.len : #skip other than last index.
          debugEcho "skiped save: " & saveFilename
          continue #skip download
        var hc = newHttpClient()
        spawn hc.downloadFile(imgUrl, saveFilename)
        debugEcho "saved file: " & saveFilename


proc updateFeedAtom*() =
  let list4koma: seq[PageData] = readFile(exportFile4komaDataJson).parseJson.to(seq[PageData])
  let title = list4koma[^1].Title
  let lastImage = list4koma[^1].ImagesUrl.filter(
    proc (img: string): bool = img.contains("sp.jpg") == false
  )[^1]

  proc jstInfo(time: Time): ZonedTime =
    ZonedTime(utcOffset: -32400, isDst: false, time: time)
  let jst = newTimezone("Asia/Tokyo", jstInfo, jstInfo)
  let update = now().inZone(jst).format("yyyy-MM-dd'T'HH':'mm':'sszzz")
  let published = now().format("yyyyMMddHHmm")
  let content = """$lastImage""" % ["lastImage", lastImage]
  let auther = "iranika"
  let entry_url = "https://movue.iranika.info/#/?page=latest"

  let addFeedEntryStr = """<!--insertEntry-->
  <entry>
    <id>tag:iranika.github.io,2019:Repository/194400309/$published</id>
    <updated>$update</updated>
    <published>$update</published>
    <link rel="alternate" type="text/html" href="$entry_url"/>
    <title>$title</title>
    <content type="html" xml:lang="ja">$content</content>
    <author>
      <name>$auther</name>
    </author>
  </entry>""" % ["title", title, "update", update, "content", content, "auther", auther, "entry_url", entry_url, "published", published]
  writeFile("feed.atom", readFile("feed.atom").replace("<!--insertEntry-->", addFeedEntryStr))
  debugEcho addFeedEntryStr
  return

proc updateFeedRss*() =
  let list4koma: seq[PageData] = readFile(exportFile4komaDataJson).parseJson.to(seq[PageData])
  let title = list4koma[^1].Title
  let lastImage = list4koma[^1].ImagesUrl.filter(
    proc (img: string): bool = img.contains("sp.jpg") == false
  )[^1]
  let update = now().format("yyyy-MM-dd'T'HH':'mm':'sszzz")
  let published = now().format("yyyyMMddHHmm")
  let content = """$lastImage""" % ["lastImage", lastImage]
  let auther = "iranika"
  let entry_url = "https://movue.iranika.info/#/?page=latest"

  let addFeedEntryStr = """<!--insertEntry-->
  <entry>
    <id>tag:iranika.github.io,2019:Repository/194400309/$published</id>
    <updated>$update</updated>
    <published>$published</published>
    <link rel="alternate" type="text/html" href="$entry_url"/>
    <title>$title</title>
    <content type="html" xml:lang="ja">$content</content>
    <author>
      <name>$auther</name>
    </author>
  </entry>""" % ["title", title, "update", update, "content", content, "auther", auther, "entry_url", entry_url, "published", published]
  writeFile("feed.atom", readFile("feed.atom").replace("<!--insertEntry-->", addFeedEntryStr))
  debugEcho addFeedEntryStr
  return
