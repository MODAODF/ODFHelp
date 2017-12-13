# -*- coding: utf-8 -*-
import os
import http.client
import json
import zipfile
import base64

if __name__ != '__main__':
    import uno
    import unohelper
    from com.sun.star.task import XJob

CONTENTZIP = 'contents.zip'  # index
IMAGEDIR = 'conpics'  # 圖檔目錄

HELP_HOST = '223.200.166.56'  # rest host
QA_HOST = '223.200.166.57'  # rest host
#QA_HOST = '192.168.1.60'  # rest host


## Switch to http connection(REST) or zipfile
#
#  kind='h': http
#  kind='z': zipfile
class TwowayConnector(object):
    ## The constructor.
    def __init__(self, kind):
        self.__conn = None
        self.__kind = kind
        if self.__kind == 'h':
            self.__conn = http.client.HTTPConnection(HELP_HOST)

    ## open zipfile connection
    #  @param modpath str module path
    def __conn_z_open(self, modpath):
        if self.__conn is not None:
            return

        if modpath.startswith('file:'):
            modpath = uno.fileUrlToSystemPath(modpath)
        self.__conn = zipfile.ZipFile(modpath + '/' + CONTENTZIP)

    ## getindex
    #  @see HelpObj
    #  @param idx int
    #  @param modpath str module path
    def getIndex(self, idx, modpath=''):
        if self.__kind == 'h':
            self.__conn.request('GET', '/getCategory')
            response = self.__conn.getresponse()
            jdatas = json.loads(response.read().decode())['aaData']
            return jdatas
        elif self.__kind == 'z':
            self.__conn_z_open(modpath)
            helplist = list()
            for info in self.__conn.infolist():
                helplist.append({'title': info.filename})

            return helplist

    ## getcontent
    #  @see HelpObj
    #  @param idx int
    #  @param keyword str
    #  @param modpath str module path
    def getContent(self, idx, keyword, modpath=''):
        if self.__kind == 'h':
            self.__conn.request('GET', '/getArticle/' +
                                 self.getIndex(idx, keyword))
            response = self.__conn.getresponse()
            return json.loads(response.read().decode())['content']
        elif self.__kind == 'z':
            self.__conn_z_open(modpath)

            if modpath.startswith('file:'):
                modpath = uno.fileUrlToSystemPath(modpath)

            buf = list()
            # 沒設關鍵字列全部
            data = TwowayConnector.getIndex(self, idx, modpath)
            if keyword != '':
                data = list()
                for buf in TwowayConnector.getIndex(self, idx, modpath):
                    if buf['title'].find(keyword) > -1:  # 有關鍵字
                        data.append(buf)

            data = data[idx]
            filename = data['title']
            return self.__conn.read(filename).decode('utf8')


## Object for request restful data: 說明
class HelpObj(TwowayConnector):
    ## The constructor.
    def __init__(self, kind='h'):
        TwowayConnector.__init__(self, kind)

    ## 說明列表
    #  @param idx int index
    #  @param keyword str 關鍵字：有符合才列
    #  @return idx/[title,...] int/list(str,...) index/titles
    def getIndex(self, idx=None, keyword='', modpath=''):
        jdatas = TwowayConnector.getIndex(self, idx, modpath)

        realindex = []
        for data in jdatas:  # 為了過濾 title, 必需先建立真正的列表...
            if data['title'] != 'Untitled':  # 好讓 listbox 對應到真正的 index
                if keyword == '':  # 沒設關鍵字列全部
                    realindex.append(data)
                elif data['title'].find(keyword) > -1:  # 有關鍵字
                    realindex.append(data)

        if idx is None:  # 列表
            idxs = []
            for data in realindex:
                idxs.append(data['title'])
            return idxs
        else:  # 單筆，傳回 id
            datas = []
            for data in realindex:
                datas.append(data['id'])
            return datas[idx]

    ## 說明內容
    #  @param idx int index
    #  @param keyword str 關鍵字 for getIndex()
    #  @return str content
    def getContent(self, idx, keyword, modpath=''):
        return TwowayConnector.getContent(self, idx, keyword, modpath)


## Object for request restful data:QA
class QAObj:
    ## The constructor.
    def __init__(self):
        self.__conn = http.client.HTTPConnection(QA_HOST)

    def secureKey(self):
        return {'authKey': 'fewlkqgtj43pt834mjpc3nu5019x'}

    ## 分類列表 一
    #
    #  有指定 idx: 傳回該分類 id
    #  沒指定 idx: 傳回列表
    #  @param idx int index
    #  @return idx/[title,...] int/list(str,...) index/titles
    def getCateList(self, idx=None):
        uri = '/FluxBB/router/index.php/getdata/getcategorylist'
        self.__conn.request('GET', uri)
        response = self.__conn.getresponse()
        jdatas = json.loads(response.read().decode())['aaData']
        realindex = []
        for data in jdatas:  # 建立真正的列表...
            realindex.append(data)

        if idx is None:  # 列表
            idxs = []
            for data in realindex:
                idxs.append(data[1])
            return idxs
        else:  # 單筆，傳回 id
            datas = []
            for data in realindex:
                datas.append(data[0])
            return datas[idx]

    ## 分類列表 二
    #
    #  cateid <> -1, getid = -1: 傳回列表
    #  cateid <> -1, getid <> -1: 傳回該分類 id
    #  @param cateid int 列表一的 index
    #  @param getid int 列表二的 index
    #  @return idx/[title,...] int/list(str,...) index/titles
    def getForumList(self, cateid=-1, getid=-1):
        uri = '/FluxBB/router/index.php/getdata/getforumlist/'
        self.__conn.request('GET', uri + self.getCateList(cateid))
        response = self.__conn.getresponse()
        jdatas = json.loads(response.read().decode())['aaData']
        realindex = []
        for data in jdatas:  # 建立真正的列表...
            realindex.append(data)

        if cateid > -1 and -1 == getid:  # 列表
            idxs = []
            for data in realindex:
                idxs.append(data[1])
            return idxs
        if getid > -1:  # 單筆，傳回 id
            datas = []
            for data in realindex:
                datas.append(data[0])
            return datas[getid]

    ## submit: 送出資訊
    #  @param cateid int
    #  @param forumid int
    #  @param uname str username
    #  @param email str
    #  @param depart str
    #  @param subject str
    #  @param message str
    #  @param afile str attach file for upload
    #  @param unlock str
    #  @return bool
    def submit(self, cateid, forumid, uname, email, depart,
               subject, message, afile, unlock='0400511'):
        import urllib.parse

        afile_b64 = ''
        afilename = ''
        if afile != '':
            with open(afile, "rb") as afile_buf:
                afile_b64 = base64.b64encode(afile_buf.read())
                afilename = os.path.basename(afile)

        params = {'username': uname,
                  'email': email,
                  'department': depart,
                  'subject': subject,
                  'message': message,
                  'forum_id': self.getForumList(cateid, forumid),
                  'afile': afile_b64,
                  'afilename': afilename,
                  'unlock': unlock}
        params = urllib.parse.urlencode(params)

        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        headers.update(self.secureKey())
        self.__conn.request('POST', '/FluxBB/receive.php',
                             params, headers)
        response = self.__conn.getresponse()
        return 200 == response.status

    ## 取得題目審核狀態列表
    #  @param uname str
    #  @param depart str
    #  @param email str
    #  @return [str, str, int, int] [title, 已/未審核 title, topic_id, 已/未審核 id, timestamp]
    def getTopicStatusList(self, uname, depart, email):
        import uno
        uri = "/FluxBB/router/index.php/getdata/gettopicofuser/%s/%s/%s"
        uri = uri % (uname.strip(), email.strip(), depart.strip())
        uri = uno.systemPathToFileUrl(uri)
        self.__conn.request('GET', uri)
        response = self.__conn.getresponse()

        jdatas = json.loads(response.read().decode('utf-8'))['aaData']

        lsts = list()
        for data in jdatas:
            data[2] = int(data[2])
            data[3] = int(data[3])
            title = '錯誤！'
            # @TODO: 以實際 post 數量代替 num_replies
            # creator = 0 AND num_replies=0 LEVEL_CREATE
            if data[2] == 0:  # and data[3] == 0:
                title = '已收到'
            # creator>1 AND num_replies=0 LEVEL_ASSIGN
            if data[2] > 1 and data[3] == 0:
                title = '處理中'
            # creator>1 AND num_replies>0 LEVEL_REPLY
            if data[2] > 1 and data[3] > 0:
                title = '處理中'
            if data[2] == 1:  # LEVEL_DONE
                title = '已審核'
            lsts.append([data[1], title, data[0], data[2], data[4]])
        return lsts

    ## QA 搜尋：取得列表
    #  @param keyword str
    #  @return []
    def getSearchList(self, keyword):
        import uno
        uri = "/FluxBB/router/index.php/getdata/search_qa/" + keyword
        uri = uno.systemPathToFileUrl(uri)
        self.__conn.request('GET', uri)
        response = self.__conn.getresponse()
        jdatas = json.loads(response.read().decode())

        if type(jdatas) is list:
            return list()

        # 將來源重組成 [forum set][subject set][...][...]
        forums = list()
        for idx in jdatas.keys():
            data = jdatas[str(idx)]
            forums.append([data[0]['forum_name'], 0, data[0]['forum_id']])
            for topic in data:
                forums.append([topic['subject'], topic['topic_id'], 0])

        return forums

    ## QA　搜尋後：取得 topic titles
    #  @param id int topic_id
    #  @return [str,...]
    def getSearchTopic(self, id):
        uri = "/FluxBB/router/index.php/getdata/search_gettopic/" + str(id)
        self.__conn.request('GET', uri)
        response = self.__conn.getresponse()
        jdatas = json.loads(response.read().decode())

        messages = list()
        for mes in jdatas:
            messages.append(mes['message'])

        return messages

    ## 建立使用者帳號
    #  @param username str
    #  @param partid int
    #  @param email str
    #  @return bool
    def addNewUser(self, username, partid, email):
        uri = "/FluxBB/router/index.php/getdata/addnewndcuser/%s/%s/%s"
        uri = uri % (username, partid, email)
        uri = uno.systemPathToFileUrl(uri)
        self.__conn.request('GET', uri, None, self.secureKey())
        response = self.__conn.getresponse()
        return response.status == 200

    ## 使用者帳號是否存在
    #  @param username str
    #  @param partid int
    #  @param email str
    #  @return uid int
    def userExist(self, username, partid, email):
        uri = "/FluxBB/router/index.php/getdata/checkifuserexist/%s/%s/%s"
        uri = uri % (username, partid, email)
        uri = uno.systemPathToFileUrl(uri)
        self.__conn.request('GET', uri)
        response = self.__conn.getresponse()
        return json.loads(response.read().decode())

    ## 紀錄 uid, mac address
    #  @param uid int
    #  @return bool
    def logUserMeta(self, uid):
        import uuid
        meta = str(hex(uuid.getnode())).replace('0x', '')
        uri = "/FluxBB/router/index.php/getdata/logusermeta/%s/%s"
        uri = uri % (uid, meta)
        self.__conn.request('GET', uri, None, self.secureKey())
        response = self.__conn.getresponse()
        return response.status == 200


if __name__ != '__main__':
    ## Bridge to call via Basic.createUnoService("...")
    class QAImp(unohelper.Base, XJob):
        def __init__(self, ctx):
            self.ctx = ctx

        def execute(self, args):
            for prop in args:
                if prop.Name == 'helpIndex':
                    modpath, keyword = prop.Value
                    return HelpObj('z').getIndex(modpath=modpath,
                                                 keyword=keyword,
                                                 idx=None)
                if prop.Name == 'getQACateList':
                    return QAObj().getCateList()
                if prop.Name == 'getQAForumList':
                    cateid, getid = prop.Value
                    return QAObj().getForumList(cateid, getid)
                if prop.Name == 'submitForum':
                    pvalue = prop.Value
                    cateid, forumid = pvalue[0], pvalue[1]
                    uname, email = pvalue[2], pvalue[3]
                    depart, subject, message = pvalue[4], pvalue[5], pvalue[6]
                    afile = pvalue[7]

                    return QAObj().submit(cateid, forumid, uname, email,
                                          depart, subject, message, afile)
                if prop.Name == 'getQATopicStatusList':
                    uname, depart, email = prop.Value
                    return QAObj().getTopicStatusList(uname, depart, email)
                if prop.Name == 'getSearchList':
                    return QAObj().getSearchList(prop.Value[0])
                if prop.Name == 'addNewUser':
                    username, partid, email = prop.Value
                    return QAObj().addNewUser(username, partid, email)
                if prop.Name == 'userExist':
                    username, partid, email = prop.Value
                    return QAObj().userExist(username, partid, email)
                if prop.Name == 'logUserMeta':
                    return QAObj().logUserMeta(prop.Value)

    g_ImplementationHelper = unohelper.ImplementationHelper()
    g_ImplementationHelper.addImplementation(QAImp,
                                             "ndc.QAImp",
                                             ("com.sun.star.task.Job",),)
