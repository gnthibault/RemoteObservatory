#!/usr/bin/FreeCADcmd

# Main stuff
import math
import sys

# 3D stuff (FreeCAD + Coin3d + Pivy (python bindings for Coin3d))
import FreeCAD
from pivy.sogui import *
from pivy.coin import *

# Local stuff, helper, represented class
import Telescope
import EqMount

class Simulator:

    southern_hemisphere=False

    def Build(self):
        #Materials
        self.white=SoBaseColor()
        self.white.rgb=(1,1,1)
        self.blue=SoBaseColor()
        self.blue.rgb=(0,0,1)
        self.red=SoBaseColor()
        self.red.rgb=(1,0,0)
        self.green=SoBaseColor()
        self.green.rgb=(0,1,0)
        self.gray50=SoBaseColor()
        self.gray50.rgb=(0.5,0.5,0.5)
        self.gray70=SoBaseColor()
        self.gray70.rgb=(0.7,0.7,0.7)
        self.lensmaterial=SoMaterial()
        self.lensmaterial.diffusecolor=(0, 0, 0.5)
        self.lensmaterial.shininess=0.8
        self.lensmaterial.transparency=0.

        #Mount
        self.bh=EqMount.Baseholder(None)
        self.rh=EqMount.Rahousing(None)
        self.ra=EqMount.Raaxis(None)
        self.dh=EqMount.Dehousing(None)
        self.da=EqMount.Deaxis(None)
        self.bh.origin = FreeCAD.Vector(0,0,0)
        self.rh.origin = self.bh.origin + FreeCAD.Vector(
            self.bh.holderxshift + (self.bh.holderwidth/2),
            0, self.bh.baseheight + self.bh.holderheight -
            (self.bh.holderwidth/2))
        self.ra.origin = self.rh.origin + FreeCAD.Vector(
            self.rh.rahousingxshift + self.rh.rahousinglength, 0,
            self.rh.raaxisshift)
        self.dh.origin = self.ra.origin + FreeCAD.Vector(
            self.ra.racylinderlength, 0, 0)
        self.deaxiszshift = (self.dh.deboxheight + self.dh.deboxzshift +
            self.dh.deconelength + self.dh.decylinderlength)
        self.da.origin = self.dh.origin + FreeCAD.Vector(
            self.dh.deaxisxshift, 0, self.deaxiszshift)

        self.bh.MakeBaseholder()
        self.rootbaseholder=self.bh.draw(self.gray50)
        self.rh.MakeRahousing()
        self.rootrahousing=self.rh.draw(self.gray50)
        self.ra.MakeRaaxis()
        self.rootraaxis=self.ra.draw(self.gray50, self.white)
        self.dh.MakeDehousing()
        self.rootdehousing=self.dh.draw(self.gray50)
        self.da.MakeDeaxis()
        self.rootdeaxis=self.da.draw(self.gray50, self.white, self.gray70)
        
        #Scope
        self.d=Telescope.Dovetail(None)
        self.r=Telescope.Refractor(None)
        self.c=Telescope.Crayford(None)
        self.d.origin = self.da.origin + FreeCAD.Vector(
            0,0,self.da.decylinderlength)
        self.r.origin = self.d.origin+FreeCAD.Vector(
            0,0,self.d.baseheight + self.d.coilradius)
        self.c.origin=self.r.origin+FreeCAD.Vector(-self.r.tubelength / 2)

        self.d.MakeDovetail()
        self.rootdovetail=self.d.draw(self.green, self.gray50)
        self.r.MakeRefractor()
        self.rootrefractor=self.r.draw(self.white, self.white, self.lensmaterial)
        self.c.MakeCrayford()
        self.rootcrayford=self.c.draw(self.gray50, self.red, self.white)

        # Assemble part components including rotation/transform nodes
        self.scene=SoSeparator()
        self.scene.addChild(self.rootbaseholder)
        self.rotationlatitude=SoTransform()
        self.rotationlatitude.rotation.setValue(SbVec3f(0,1,0),
            math.radians(0.0))
        self.rotationlatitude.center=self.rh.origin
        self.latitudenode=SoSeparator()
        self.latitudenode.addChild(self.rotationlatitude)
        self.scene.addChild(self.latitudenode)

        self.latitudenode.addChild(self.rootrahousing)
        self.rotationra=SoTransform()
        self.rotationra.rotation.setValue(SbVec3f(1,0,0), math.radians(0))
        self.rotationra.center=self.ra.origin
        self.ranode=SoSeparator()
        self.ranode.addChild(self.rotationra)
        self.latitudenode.addChild(self.ranode)

        self.ranode.addChild(self.rootraaxis)
        self.ranode.addChild(self.rootdehousing)
        self.rotationde=SoTransform()
        self.rotationde.rotation.setValue(SbVec3f(0,0,1), math.radians(0))
        self.rotationde.center=self.da.origin
        self.denode=SoSeparator()
        self.denode.addChild(self.rotationde)
        self.ranode.addChild(self.denode)

        self.denode.addChild(self.rootdeaxis)

        self.denode.addChild(self.rootdovetail)
        self.denode.addChild(self.rootrefractor)
        self.denode.addChild(self.rootcrayford)

#focus=SoText2()
#focus.string="Focus: 89.612 mm"
#focustr=SoTranslation()
#focustr.translation.setValue(200, 300, -300)
#roottext=SoSeparator()
#roottext.addChild(focustr)
#roottext.addChild(focus)
#rootc.addChild(roottext)


        # All angles in degrees
    def setLatitude(self, latitude):
        self.latitude=latitude
        self.rotationlatitude.rotation.setValue(SbVec3f(0,1,0),
            math.radians(-abs(latitude)))
        if (latitude >= 0.0): 
            self.southern_hemisphere=False 
        else: 
            self.southern_hemisphere=True
            
    def setRAangle(self, raangle):
        self.rotationra.rotation.setValue(SbVec3f(1,0,0),
            math.radians(raangle))

    def setDEangle(self, deangle):
        self.rotationde.rotation.setValue(SbVec3f(0,0,1),
            math.radians(deangle))

    def setFocuserangle(self, focangle):
        self.c.rotationcrayford.rotation.setValue(
            SbVec3f(1,0,0), math.radians(focangle))

    def setFocuserposition(self, position):
        #self.c.translationfocus.translation=FreeCAD.Vector(-position, 0, 0)
        self.c.translationfocus.translation.setValue([-position, 0, 0])

    def Show(self):
        # 3D Window
        self.myWindow=SoGui.init("EQ Simulator")
        if self.myWindow == None: sys.exit(1)
        
        self.viewer=SoGuiExaminerViewer(self.myWindow)
        self.viewer.setTitle("EQ Simulator")
        self.viewer.setSceneGraph(self.scene)
        #viewer.setSize((800,600))
        self.viewer.show()
        SoGui.show(self.myWindow)

    def Embed(self, widget):
         self.viewer=SoGuiExaminerViewer(widget)
         self.viewer.setSceneGraph(self.scene)
         #viewer.setSize((800,600))

