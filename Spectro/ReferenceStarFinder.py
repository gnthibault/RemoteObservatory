'''
Here is the original header from Serge Golovanow:
SpectroStars : Find reference stars for spectroscopy
https://github.com/serge-golovanow/SpectroStars
Copyright © 2019, Serge Golovanow

Based on an idea and the stars database from ReferenceStarFinder, made by François Teyssier

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
The Software is provided “as is”, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the Software.
v19-03-05
'''

# Generic stuff
import csv

# Numerical stuff
import numpy as np

# Astronomy stuff
from astropy import units as u
from astropy.coordinates import FK5
from astropy.coordinates import  SkyCoord, FK5, AltAz, Angle

# local defs
#Maximum Eb-v (0.1), or None
csvfilename='Spectro/spectral_references.csv'

def starload(star, target, altaz_frame, maxseparation, maxebv):
    """ Compute an OrderedDict : separation, alt, az
    """
    try:
        if (float(star['EB-V'])<0):
            star['EB-V'] = 0
        else:
            star['EB-V'] = float(star['EB-V'])
        if star['EB-V'] > maxebv:
            return None
        star['Sky'] = SkyCoord(ra=float(star['RA_dec'])*u.deg,
                               dec=float(star['de_dec'])*u.deg,
                               frame='icrs',
                               equinox='J2000.0')
        star['separation'] = target.coord.separation(star['Sky'])
        if star['separation']<5*u.arcsecond:
            return None # we don't want the same star
        if star['separation']>maxseparation:
            return None
        altaz = star['Sky'].transform_to(altaz_frame)
        star['Alt'] = altaz.alt
        star['Delta'] = star['Alt']-target.coord.transform_to(altaz_frame).alt
        star['secz'] = altaz.secz.value
    except Exception as e:
        print(f"Error while trying to load star from spectral reference "
              f"catalog: {e}")
        return None
    return star

def baseload(target, altaz_frame, maxseparation, maxebv):
    """ Read CSV database to put it in an OrderedDict
    """
    starbase = []
    with open(csvfilename, newline='\n') as csvfile:
        csvbase = csv.DictReader(csvfile, delimiter=',')

        #if parallelize:	#Joblib.Parallel : parallelise main loop        loky multiprocessing threading
        #    starbase = Parallel(n_jobs=-1,backend="multiprocessing",verbose=0)(delayed(starload)(star,target,maxseparation,altaz_frame) for star in csvbase)
        #else:
        starbase = [starload(star, target, altaz_frame, maxseparation, maxebv)
                    for star in csvbase]
        starbase = [s for s in starbase if s is not None]
    return starbase

def stardisplay(num,star): # display a star
    name = star["Name"]
    separation = str(round(star['Separation'],1))+"°"
    coords = star['Sky'].to_string(style='hmsdms',precision=0)
    alt = str(round(star['Alt'])).zfill(2)+'°'
    deltaalt = str(round(star['Delta'],1))+"°"
    Vmag = star['V']
    BV = star['B-V']
    if BV=='': BV = '    '
    EBV = star['EB-V']
    if EBV == '': EBV = '\t'
    sptype = star['Sp']
    if (star['Alt']>=1): 
        decimales = 2
        if (star['secz']>=100): decimales = 1
        airmass = str(round(star['secz'],decimales))
    else: airmass = '  '
    miles = star['Miles']
    starline = str(num).zfill(2)+'  '+name+'\t'+separation+"\t"+Vmag+'\t'+coords+'\t'+alt+', Δh='+deltaalt+'\t'+BV+'\t'+EBV+'\t'+sptype+'\t '+airmass+'\t'+miles

    return starline



def best_references(target, altaz_frame, maxseparation, maxebv):
    #Geting stars database, with separation and altaz computed :
    base = baseload(target=target,
                    altaz_frame=altaz_frame,
                    maxseparation=maxseparation,
                    maxebv=maxebv)
    if not base:
        raise RuntimeError(f"Error while loading database from csv or "
                           f"processing it")

    #Setting final stars array
    final = []  #will contain only nearest stars
    for num, star in enumerate(base):
        if (star is not None):
            final.append(star)

    #sorting stars by Δh :
    final = sorted(final, key=lambda item: np.abs(item['Delta'].to(u.deg).value))

    return final
