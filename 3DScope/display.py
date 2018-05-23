from pivy.sogui import *
from pivy.coin import *
import sys

import Telescope
import EqMount
import FreeCAD
import math

# useful ??SoDB.init()

scene=SoSeparator()
#Materials
white=SoBaseColor()
white.rgb=(1,1,1)
blue=SoBaseColor()
blue.rgb=(0,0,1)
red=SoBaseColor()
red.rgb=(1,0,0)
green=SoBaseColor()
green.rgb=(0,1,0)
gray50=SoBaseColor()
gray50.rgb=(0.5,0.5,0.5)
gray70=SoBaseColor()
gray50.rgb=(0.7,0.7,0.7)
lensmaterial=SoMaterial()
lensmaterial.diffusecolor=(0, 0, 0.7)
lensmaterial.shininess=0.8
lensmaterial.transparency=0.9

#Mount
bh=EqMount.Baseholder(None)
rh=EqMount.Rahousing(None)
ra=EqMount.Raaxis(None)
dh=EqMount.Dehousing(None)
da=EqMount.Deaxis(None)
bh.origin=FreeCAD.Vector(0,0,0)
rh.origin=bh.origin + FreeCAD.Vector(bh.holderxshift+(bh.holderwidth/2),
                        0,
                        bh.baseheight + bh.holderheight - (bh.holderwidth/2))
ra.origin=rh.origin + FreeCAD.Vector(rh.rahousingxshift + rh.rahousinglength,
                           0, rh.raaxisshift)
dh.origin=ra.origin + FreeCAD.Vector(ra.racylinderlength, 0, 0)
deaxiszshift=dh.deboxheight + dh.deboxzshift + \
        dh.deconelength + dh.decylinderlength
da.origin=dh.origin + FreeCAD.Vector(dh.deaxisxshift, 0, deaxiszshift)

bh.MakeBaseholder()
rootbaseholder=bh.draw(gray50)
rh.MakeRahousing()
rootrahousing=rh.draw(gray50)
ra.MakeRaaxis()
rootraaxis=ra.draw(gray50, white)
dh.MakeDehousing()
rootdehousing=dh.draw(gray50)
da.MakeDeaxis()
rootdeaxis=da.draw(gray50, white, gray70)

#Scope
d=Telescope.Dovetail(None)
r=Telescope.Refractor(None)
c=Telescope.Crayford(None)
d.origin=da.origin + FreeCAD.Vector(0,0,da.decylinderlength)
r.origin=d.origin+FreeCAD.Vector(0,0,d.baseheight + d.coilradius)
c.origin=r.origin+FreeCAD.Vector(-r.tubelength / 2)

d.MakeDovetail()
rootdovetail=d.draw(green, gray50)
r.MakeRefractor()
rootrefractor=r.draw(white, white, lensmaterial)
c.MakeCrayford()
rootcrayford=c.draw(gray50, red, white)

#focus=SoText2()
#focus.string="Focus: 89.612 mm"
#focustr=SoTranslation()
#focustr.translation.setValue(200, 300, -300)
#roottext=SoSeparator()
#roottext.addChild(focustr)
#roottext.addChild(focus)
#rootc.addChild(roottext)


scene=SoSeparator()
scene.addChild(rootbaseholder)
rotationlatitude=SoTransform()
rotationlatitude.rotation.setValue(SbVec3f(0,1,0), math.radians(49.29))
rotationlatitude.center=rh.origin
latitudenode=SoSeparator()
latitudenode.addChild(rotationlatitude)
scene.addChild(latitudenode)

latitudenode.addChild(rootrahousing)
rotationra=SoTransform()
rotationra.rotation.setValue(SbVec3f(1,0,0), math.radians(0))
rotationra.center=ra.origin
ranode=SoSeparator()
ranode.addChild(rotationra)
latitudenode.addChild(ranode)

ranode.addChild(rootraaxis)
ranode.addChild(rootdehousing)
rotationde=SoTransform()
rotationde.rotation.setValue(SbVec3f(0,0,1), math.radians(0))
rotationde.center=da.origin
denode=SoSeparator()
denode.addChild(rotationde)
ranode.addChild(denode)

denode.addChild(rootdeaxis)

denode.addChild(rootdovetail)
denode.addChild(rootrefractor)
denode.addChild(rootcrayford)


myWindow=SoGui.init("EQ Simulator")
if myWindow == None: sys.exit(1)

viewer=SoGuiExaminerViewer(myWindow)
viewer.setTitle("EQ Simulator")
viewer.setSceneGraph(scene)
#viewer.setSize((800,600))
viewer.show()
SoGui.show(myWindow)

#rotationz=SoRotationXYZ()
#rotationz.axis=SoRotationXYZ.Z
#rotationz.angle=radians(30)
#scene.insertChild(rotationz,0)
#rotationz.angle=radians(80)
# set latitude
# rotationlatitude.rotation.setValue(SbVec3f(0,1,0), math.radians(-49.29))
