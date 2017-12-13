# -*- coding: utf-8 -*-
import re
import html  # used for html.escape

if __name__ != '__main__':
    import uno
    import unohelper
    from com.sun.star.task import XJob


lineBreak = "<text:line-break/>"
header_t = "<text:h text:style-name=\"Heading_20_%d\" text:outline-level=\"%d\">%s</text:h>"
p1_t = "<text:p text:style-name=\"P1\">%s</text:p>"
img_p1_t = "<text:p text:style-name=\"圖形段落\">%s</text:p>"
span_t = "<text:span text:style-name=\"T1\">%s</text:span>"
image_t = "<draw:frame draw:style-name=\"fr1\" draw:name=\"Image%d\" text:anchor-type=\"as-char\" svg:width=\"%fcm\" svg:height=\"%fcm\" draw:z-index=\"0\"><draw:image xlink:href=\"%s\" xlink:type=\"simple\" xlink:show=\"embed\" xlink:actuate=\"onLoad\"/></draw:frame>"
chp1_t = """<text:list xml:id="list1547348446" text:style-name="L2">
<text:list-item>
    <text:p text:style-name="P4">%s</text:p>
</text:list-item>
</text:list>"""
chp2_t = """<text:list xml:id="list1547348446" text:style-name="L1">
<text:list-item>
    <text:list>
        <text:list-item>
            <text:p text:style-name="P3">%s</text:p>
        </text:list-item>
    </text:list>
</text:list-item>
</text:list>"""
table_t = """<table:table-row>
<table:table-cell table:style-name="Table1.A%d" office:value-type="float" office:value="0">
    <text:p text:style-name="P3">%s</text:p>
</table:table-cell>
</table:table-row>"""


## parse: P1
#  @param content str
#  @param escape bool escape html entry code
#  @return str
def parseP1(content, escape=True):
    if escape:
        content = html.escape(content)
    return p1_t % (content)


## convert from px to cm
#  @param num int
#  @return float/double
def convert2CM(num):
    return float(num) * 2.54 / 96

imgs = list()  # real image list


## parse: image
#  @param url str image url
#  @return str
def parseImage(url, w=None, h=None):
    img_idx = len(imgs) + 1
    if w is None:
        w, h = 4.63, 4.63
    else:
        w, h = convert2CM(w), convert2CM(h)
    return image_t % (img_idx, w, h, url)


## 以正規表示式替換圖片
#
#  格式:
#  ![tag](url WWxHH)
#
#  回傳假的圖片, 原因參照 formatDoc()
#  同時也會把真正的圖片位置存到 imgs
#
#  @param modpath str 圖片位址
#  @param buf str
#  @param idx int
#  @return buf str
def regCheckImg(modpath, buf, idx):
    global imgs, forZip

    forZip = modpath != ''
    regex = r'!\[[^\[]*\]\((.*)\)'
    result = re.search(regex, buf)

    if result:
        w, h = None, None
        imgurl = result.groups()[0].split()[0]  # 以 rest 匯入
        if len(result.groups()[0].split()) == 2:
            # 若有指定 WWxHH 就取出來
            line = result.groups()[0].split()[1]
            rst = re.match(r'=(\d+)x(\d+)', line)
            if rst:
                w, h = rst.groups()

        if forZip:  # 以 zip 匯入，真實圖片為下載下來的圖片
            from RestData import IMAGEDIR
            # 包成 msi 時 0/1 會出錯，因此加上 prefix
            imgurl = "file:///%s/%s/p%d/p%d"
            imgurl %= (html.escape(modpath), IMAGEDIR, idx, len(imgs))
            imgurl = imgurl.replace("\\", '/')

        # 組合
        middle = parseImage(modpath + '/dummy.gif', w, h)
        segment = buf.split(result.group())
        segment[0] = span_t % (html.escape(segment[0]))
        segment[1] = span_t % (html.escape(segment[1]))
        buf = img_p1_t % (segment[0] + middle + segment[1])

        imgs.append(imgurl)  # 存入真正的圖片位置
    else:
        buf = parseP1(buf)  # default value

    return buf


## 格式化文件成 odt content.xml
#
#  1) 解析 # ## ### ##### ######
#  2) 解析圖片網址:
#     odt 開啟時若有圖片會先等圖片都下載完才開，當圖片開太慢則 odt 畫面會卡到
#     因此要先開啟 local　端圖片後，再非同步置換真正的圖片
#
#  @param modpath str 參照到的 path, 給 import 定位用
#  @param templ str content.xml 內容
#  @param idx int index
#  @param keyword str 關鍵字查詢用
#  @return list [str of content.xml, list of image urls]
def formatDoc(modpath, templ, idx, keyword):
    global imgs, forZip

    forZip = modpath is not None

    # 透過 createUnoService(...)　呼叫過來時，若要 import 其他模駔
    # 則需由 caller 傳路徑以供定位
    if forZip:
        import sys
        op = 'z'
        modpath = uno.fileUrlToSystemPath(modpath)
        sys.path.insert(0, modpath + '/Python')
    else:
        op = 'h'
        modpath = ''
    from RestData import HelpObj

    imgs = list()
    content = list()
    data = HelpObj(op).getContent(idx, keyword, modpath)
    for buf in data.split('\n'):  # 處理每一行
        result = re.match('^(#{1,6})(.*)$', buf)  # 找 # ## ### ####
        chp1 = re.match(r'^\+\s(.*)$', buf)
        chp2 = re.match(r'^\s\s\-\s(.*)$', buf)

        if result:  # 解析 # ## ### #### 成 H1 Hn
            hnumber = len(result.groups()[0])
            subject = result.groups()[1]
            buf = header_t % (hnumber, hnumber, html.escape(subject))
        elif chp1:  # 項目第一層
            buf = chp1_t % (html.escape(chp1.groups()[0]))
        elif chp2:  # 項目第二層
            buf = chp2_t % (html.escape(chp2.groups()[0]))
        else:  # 解析圖片網址
            buf = regCheckImg(modpath, buf, idx)

        content.append(buf)

    content = '\n'.join(content)
    content = content.replace('\n', lineBreak)
    return [templ.replace("{%content}", content), imgs]


## QA　查詢結果：格式化成 odt content.xml
#
#  @param modpath str 參照到的 path, 給 import 定位用
#  @param templ str content.xml 內容
#  @param id int topic_id
#  @param breadcrumb str
#  @return list [str of content.xml, list of image urls]
def formatDocQA(modpath, templ, id, breadcrumb):
    # 透過 createUnoService(...)　呼叫過來時，若要 import 其他模駔
    # 則需由 caller 傳路徑以供定位
    import sys
    modpath = uno.fileUrlToSystemPath(modpath)
    sys.path.insert(0, modpath + '/Python')
    from RestData import QAObj

    content = ''
    for idx, buf in enumerate(QAObj().getSearchTopic(id)):  # 處理每一筆
        buf = buf.replace('\n', lineBreak)

        # 每筆以表格框起來
        pos = idx + 2  # A2
        if pos > 3:  # or A3
            pos = 2
        content += table_t % (pos, buf)

    templ = templ.replace("{%content}", content)
    templ = templ.replace("{%breadcrumb}", breadcrumb)  # ... >> ...
    return templ


if __name__ != '__main__':
    ## Bridge to call via Basic.createUnoService("...")
    class DocTemplImp(unohelper.Base, XJob):
        def __init__(self, ctx):
            self.ctx = ctx

        def execute(self, args):
            for prop in args:
                if prop.Name == 'formatDoc':
                    modpath, templ, idx, keyword = prop.Value
                    return formatDoc(modpath, templ, idx, keyword)
                if prop.Name == 'formatDocQA':
                    modpath, templ, idx, breadcrumb = prop.Value
                    return formatDocQA(modpath, templ, idx, breadcrumb)

    g_ImplementationHelper = unohelper.ImplementationHelper()
    g_ImplementationHelper.addImplementation(DocTemplImp,
                                             "ndc.DocTemplImp",
                                             ("com.sun.star.task.Job",),)
