from pivy.sogui import *
from pivy.coin import *
import sys


def draw(obj, viewer):
    input=SoInput()
    input.setBuffer(obj.shape.writeInventor())
    # SoNode is abstract, so what to use ?
    #rootnode=SoNode()
    #SoDB.read(input, rootnode)
    rootnode=SoSeparator()
    rootnode=SoDB.readAll(input)
    return rootnode

def ChangeScene(shape, viewer,scene):
    input=SoInput()
    input.setBuffer(shape.writeInventor())
    scene = SoDB.readAll(input)
    viewer.setSceneGraph(scene)

myWindow=SoGui.init("EQ Simulator")
if myWindow == None: sys.exit(1)
scene=SoSeparator()
viewer=SoGuiExaminerViewer(myWindow)
viewer.setTitle("EQ Simulator")
viewer.show()
SoGui.show(myWindow)

import Telescope
c=Telescope.Crayford(None)
c.MakeCrayford()
SoDB.init()
rootc=draw(c, viewer)
col = SoBaseColor()
col.rgb=(1,0,0)
rootc.insertChild(col, 0)
viewer.setSceneGraph(rootc)
focus=SoText2()
focus.string="Focus: 89.612 mm"
focustr=SoTranslation()
focustr.translation.setValue(200, 300, -300)
roottext=SoSeparator()
roottext.addChild(focustr)
roottext.addChild(focus)

rootc.addChild(roottext)
