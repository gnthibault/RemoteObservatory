# bug setBuffer const void *, use a temp file
import os
import tempfile

# 3D stuff
import pivy.sogui
import pivy.coin

class Render:

    def __init__(self):
        self.defaultmaterial = pivy.coin.SoBaseColor()
        self.defaultmaterial.rgb=(1,1,1)
        self.defaulttextcolor = pivy.coin.SoBaseColor()
        self.defaulttextcolor.rgb=(1,1,1)
        
    @staticmethod
    def draw(shape, mat):
        in_data = pivy.coin.SoInput()
        shapeinventor = shape.writeInventor()
        # bug setBuffer const void *, use a temp file
        fd, path = tempfile.mkstemp()
        try:
            tf = open(fd, 'w')
            tf.write(shapeinventor)
            #Create default rootnode and attach current shape as child
            rootnode=pivy.coin.SoSeparator()
            if (in_data.openFile(path)):
                objnode = pivy.coin.SoDB.readAll(in_data)
            rootnode.addChild(mat)
            rootnode.addChild(objnode)
            tf.close()
        finally:
            os.remove(path)
        return rootnode

    @staticmethod
    def drawdefault(shape):
        return self.draw(obj, Render.defaultmaterial)

    @staticmethod
    def drawtext(self, text, posx, posy, posz, color):
        textnode=SoText2()
        textnode.string="Focus: 89.612 mm"
        texttr=SoTranslation()
        texttr.translation.setValue(posx, posy, posz)
        roottext=SoSeparator()
        roottext.addChild(color)
        roottext.addChild(texttr)
        roottext.addChild(textnode)
        return roottext

    @staticmethod
    def drawtextdefault(self, text, posx, posy, posz):
        return self.drawtext(text, posx, posy, posz, self.defaulttextcolor)
