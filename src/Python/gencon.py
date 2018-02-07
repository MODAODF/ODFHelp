# -*- coding: utf-8 -*-
## 將 rest data 下載轉成 zip(index) 及圖檔目錄

import http.client
import json
import zipfile
import io
import requests
import base64
from RestData import *
from DocTempl import formatDoc

# 1) 下載 index -> zip
zf = zipfile.ZipFile('src/' + CONTENTZIP, 'w')

jvarContent = list()
imgs = list()
jvarImgs = list()
for qidx, title in enumerate(HelpObj('h').getIndex()):
    #print('process for index=' + str(qidx))

    content = HelpObj('h').getContent(qidx, '')
    zf.writestr(title, content)
    jvarContent.append({'id': qidx, 'title': title, 'content': content})

    oo = formatDoc(None, content, qidx, '')
    imgs.append(oo[1])
zf.close()

# 2) 下載圖片 -> 圖片目錄
in_memory_zip = io.BytesIO()
zf = zipfile.ZipFile(in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)

for idx, img in enumerate(imgs):
    for qidx, imgurl in enumerate(img):
        #print("process for pic, index=%d/%d" % (qidx, idx))

        content = requests.get(imgurl).content
        fname = 'p' + str(idx) + '/p' + str(qidx)
        zf.writestr(fname, content)

        content = base64.b64encode(content).decode("utf-8")
        jvarImgs.append({'id': idx, 'imgserial': qidx, 'content': content})
        print(IMAGEDIR + '/' + fname + " \\")

zf.extractall('src/' + IMAGEDIR)
zf.close()

jvar = {'content': jvarContent, 'images': jvarImgs}
jfile = open('helpdata.json', 'w')
jfile.write(json.dumps(jvar))
jfile.close()
