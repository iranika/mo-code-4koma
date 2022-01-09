# This is just an example to get you started. A typical hybrid package
# uses this file as the main entry point of the application.

import mosqpkg/[updateutils,utils4koma]
import cligen

const mocode_url = "http://momoirocode.web.fc2.com/mocode.html"

template Update =
  update4komaData()
  updateFeedAtom()
  download4komaImage()

proc update(nocash=false) =
  if nocash:
    Update
  else:
    if hasUpdated(mocode_url):
      Update
    else:
      echo "No updates. " & mocode_url 
      
proc dev(update=false, download=false, feed=false) =
  if update: update4komaData()
  if download: download4komaImage()
  if feed: updateFeedAtom()

when isMainModule:
  import cligen
  dispatchMulti([update], [dev])