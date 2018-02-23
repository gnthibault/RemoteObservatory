import json
import numpy as np


class TargetListDefinition:
    """ assign a list of acquisition parameter for each target
    """
    def __init__(self):
        self.targetList = dict()

    def addTarget(self, name, **kwargs):
        """ adds a Target
         
           A target is defined by its name and a dictionary where each key
           is a filterName, and each value is a tuple with nb of pose
           and duration of pose in seconds
           filters: Red Green Blue Luminance LPR OIII SII H_Alpha
        """
        self.targetList[name] = kwargs

# Define your own TargetList by adding targets
targetList = TargetListDefinition()
targetList.addTarget('M33',
                     Luminance=(3,2), #(count ,exposure time in seconde)
                     Red=(4,2),
                     Green=(4,2),
                     Blue=(4,2),)
targetList.addTarget('M51',
                     Luminance=(3,2),
                     Red=(4,2),
                     Green=(4,2),
                     Blue=(4,2),)

with open('TargetList.json', 'w') as fp:
    json.dump(targetList.targetList, fp)
