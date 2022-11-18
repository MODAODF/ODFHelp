# -*- coding: utf-8 -*-
import sys
import uno
import unohelper
from com.sun.star.task import XJob

from com.sun.star.beans import PropertyValue
from com.sun.star.embed.EmbedStates import UI_ACTIVE, ACTIVE, \
    INPLACE_ACTIVE, LOADED, RUNNING
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER


# ORE = OSSII URE
class ORE:
    '''Frequently used methods in office context'''
    def __init__(self, ctx=uno.getComponentContext()):
        self.ctx = ctx
        self.smgr = self.ctx.ServiceManager

    def createUnoService(self, service):
        return self.smgr.createInstance(service)

    def getCoreReflection(self):
        sService = 'com.sun.star.reflection.CoreReflection'
        return self.createUnoService(sService)

    def createUnoStruct(self, cTypeName):
        """Create a UNO struct and return it.
        Similar to the function of the same name in OOo Basic.
        """
        oCoreReflection = self.getCoreReflection()
        if oCoreReflection is None:
            return None
        # Get the IDL class for the type name
        oXIdlClass = oCoreReflection.forName(cTypeName)
        if oXIdlClass is None:
            return None
        # Create the struct.
        oReturnValue, oStruct = oXIdlClass.createObject(None)
        return oStruct

    def getDesktop(self):
        sService = 'com.sun.star.frame.Desktop'
        return self.smgr.createInstanceWithContext(sService, self.ctx)

    def getCurrentComponent(self):
        return self.getDesktop().getCurrentComponent()

    def getCurrentFrame(self):
        return self.getDesktop().getCurrentFrame()

    ## create/open document
    #  @param string doc location
    #  @param bool hide/show doc after open doc
    #  @return object
    def createNewDoc(self, docLoc=None, hidden=False):
        sDocLoc = docLoc
        if docLoc is None:
            sDocLoc = 'private:factory/swriter'
        p1 = PropertyValue()
        p1.Name, p1.Value = 'Hidden', hidden

        return self.getDesktop().\
                loadComponentFromURL(sDocLoc, '_blank', 0, (p1,))

    # Insert the picture object into the text, at current cursor position.
    def createNewPicObj(self, picFile, doc, cur, text, w, h):
        oGraphic = doc.createInstance('com.sun.star.text.GraphicObject')

        oGraphic.AnchorType = AS_CHARACTER
        oGraphic.GraphicURL = picFile
        #oCur.gotoEnd( False )

        if w == -1 and h == -1:
            text.insertTextContent(cur, oGraphic, False)
            oSize = oGraphic.ActualSize
            oGraphic.Width, oGraphic.Height = oSize.Width, oSize.Height
        else:
            oGraphic.Width, oGraphic.Height = w, h
            text.insertTextContent(cur, oGraphic, False)


## 關閉文件上不必要的 window
#  使文件視窗看起來只有一個視窗
#  @param frame object
def hideAllUI(frame):
    layoutMgr = frame.LayoutManager

    # 關閉浮動工具列
    for elm in layoutMgr.getElements():
        resURL = elm.ResourceURL
        layoutMgr.hideElement(resURL)
    layoutMgr.HideCurrentUI = True

    # 關閉表單設計模式
    frame.Controller.FormDesignMode = False
    try:  # for writer
        # 不顯示非列印字元
        frame.Controller.ViewSettings.ShowNonprintingCharacters = False
        # 不顯示水平線
        frame.Controller.ViewSettings.ShowHoriRuler = False
        # 不顯示文字邊界框
        frame.Controller.ViewSettings.ShowTextBoundaries = False
    except:
        pass
    try:  # for calc
        frame.Controller.SheetTabs = False
        frame.Controller.ShowNotes = False
        frame.Controller.ColumnRowHeaders = False
    except:
        pass


## Bridge to call via Basic.createUnoService("...")
class UtilsImp(unohelper.Base, XJob):
    def __init__(self, ctx):
        self.ctx = ctx

    def execute(self, args):
        for prop in args:
            if prop.Name == 'createNewDoc':
                docLoc, hidden = prop.Value
                return ORE().createNewDoc(docLoc, hidden)
            if prop.Name == 'hideAllUI':
                hideAllUI(frame=prop.Value)
                return

            ## link to ORE().createNewPicObj()
            #  used by bridge from Basic
            #  @param picFile string
            #  @param doc object
            #  @param cur object
            #  @param text object
            if prop.Name == 'createNewPicObj':
                picFile, doc, cur, text, w, h = prop.Value
                ORE().createNewPicObj(picFile, doc,
                                             cur, text, w, h)
            ## get windows version string
            #  @return str
            if prop.Name == 'getWindowsVer':
                import platform
                bit = platform.architecture()[0]
                major = sys.getwindowsversion().major
                minor = sys.getwindowsversion().minor
                product_type = sys.getwindowsversion().product_type
                buf = platform.platform().split('-')
                return "%s %s %s" % (buf[0], buf[1], bit)


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(UtilsImp,
                                         "moda.UtilsImp",
                                         ("com.sun.star.task.Job",),)
