# -*- coding: utf-8 -*-
"""
Created on Sun Jun  9 19:29:00 2019

@author: Vincent Lecocq
"""

from astropy.io import fits
from astropy.io.fits import getdata
from matplotlib import pyplot as plt
import tkinter as TK
import tkinter.filedialog as FD
from tkinter import ttk
from numpy import exp, pi, sqrt
import numpy as np
from lmfit import Model
import pandas as pd

#série de balmer
x1=6562.8
x2=4861.32
x3=4340.46
x4=4101.73
x5=3970.07

#permet de trouver la position des raies de Balmer dans un array 
#(value correspond à la longeur d'onde theorique de la raie +- 40A)
def find_nearest(array,value):
    idx_min = (np.abs(array[:,0]-(value-40))).argmin()
    idx_max = (np.abs(array[:,0]-(value+40))).argmin()
    return idx_min, idx_max


#extraction des infos necessaires dans l'en tete fits et on trace
def plot_spectrum():
    global filepath_spectre, data
    filepath_spectre = fileentry_spectre.get_path()
    spectre=fits.open(filepath_spectre)
    CRVAL1=spectre[0].header['CRVAL1']
    CDELT1=spectre[0].header['CDELT1']
    IR=getdata(filepath_spectre)
    IR=IR.tolist()
    x0=CRVAL1
    x=x0
    objet=spectre[0].header['OBJNAME']
    exptime=spectre[0].header['EXPTIME2']
    nom=spectre[0].header['OBSERVER']
    instru=spectre[0].header['BSS_INST']
    date=spectre[0].header['DATE-OBS']
    titre=objet+ ' ,' + exptime + ' ,' + nom + ' ,' + instru + ' ,' + date
    lambdas=[x0]
    delta=CDELT1
    for i in range(len(IR)-1):
        x=x+delta
        lambdas.append(x)
        
   
    data={'lambdas':lambdas,'IR':IR}
    data=pd.DataFrame(data)
    data=data.to_numpy()
    
    plt.figure(1)
    plt.title(titre)
    plt.xlabel('Wavelength (A)')
    plt.ylabel('Relative Intensity')
    plt.plot(lambdas, IR, lw=0.5)
    
    
#si les options sont cochées, on traces les raies de balmer ou on fit    
    if checkvar1.get()==1 :
        plt.figure(1)
        plt.plot([x1,x1],[0,max(IR)], '--', lw=0.3)
        plt.plot([x2,x2],[0,max(IR)], '--', lw=0.3)
        plt.plot([x3,x3],[0,max(IR)], '--', lw=0.3)
        plt.plot([x4,x4],[0,max(IR)], '--', lw=0.3)
        plt.plot([x5,x5],[0,max(IR)], '--', lw=0.3)
        
    if checkvar2.get()==1:
        fit_H('H alpha', 6562.8,2)
        fit_H('H beta',4861 ,3)
        fit_H('H gamma', 4340.5,4)
        fit_H('H delta', 4101.7,5)


def fit_H(name, center, num_fig):
    idx=find_nearest(data,center)
    x=data[idx[0]:idx[1],0]
    y=data[idx[0]:idx[1],1]
    
    def gaussian(x, amp, cen, wid):
        return (amp / (sqrt(2*pi) * wid)) * exp(-(x-cen)**2 / (2*wid**2))

    def line(x, slope, intercept):
        return slope*x + intercept

    mod = Model(gaussian) + Model(line)
    pars = mod.make_params(amp=2, cen=center, wid=2, slope=0, intercept=1)
    result = mod.fit(y, pars, x=x)
    plt.figure(num_fig)
    plt.title(name)
    plt.plot(x, y, 'bo', markersize=4)
    plt.plot(x, result.best_fit, 'r-', linewidth=3)
#    print(result.fit_report())
    A=result.fit_report()
    A=A.split()
    print('position de ',name, '= ', round(float(A[52]),1), 'A ','(',center,' A)\t', 'FWHM= ', abs(round(float(A[60])*2.3548,0)))

    
    
#========================GUI==================================================
class FileEntry (ttk.Frame):
 
    def __init__ (self, master=None, **kw):
        ttk.Frame.__init__(self, master)
        self.init_widget(**kw)

    def init_widget (self, **kw):
 
        self.label = ttk.Label(self,text=kw.get("label","Veuillez sélectionner un fichier, SVP:"))
        self.file_path = TK.StringVar()
        self.entry = ttk.Entry(self,textvariable=self.file_path)
        self.button1 = ttk.Button(self,text="Parcourir",command=self.slot_browse,underline=0,)
        self.button2 = ttk.Button(self, text="Plot Spectrum", command=plot_spectrum, underline=0,)
        
        # layout inits
        self.label.pack(side=TK.TOP, expand=0, fill=TK.X)
        self.entry.pack(side=TK.LEFT, expand=1, fill=TK.X)
        self.button1.pack(side=TK.LEFT, expand=0, fill=TK.NONE, padx=5)
        self.button2.pack(side=TK.RIGHT, expand=0, fill=TK.NONE, padx=5)

    def slot_browse (self, tk_event=None, *args, **kw):
        # browse file path
        _fpath = FD.askopenfilename()
        # set entry's contents with file_path control variable
        self.file_path.set(_fpath)
        print(_fpath)
        return _fpath
 
    def get_path (self):
        return self.file_path.get()
# end class FileEntry
 
 
root = TK.Tk()
root.title("Fits_plot")
labelframe = ttk.LabelFrame(root,text="FITS_plot",padding="5px",)
btn_quit = ttk.Button(root,text="quit",command=root.destroy,underline=0,)
# FileEntry subcomponents
 
fileentry_spectre = FileEntry(labelframe, label="spectre  :")

# fileentry layout inits
fileentry_spectre.pack(expand=0, fill=TK.X)

# labelframe layout inits
labelframe.pack(side=TK.TOP, expand=1, fill=TK.BOTH, padx=5, pady=5)
# petit extra
ttk.Sizegrip(root).pack(side=TK.RIGHT, expand=0, fill=TK.Y, padx=5, pady=5,)
# bouton quitter
btn_quit.pack(side=TK.RIGHT, padx=0, pady=5)

checkvar1=TK.IntVar()
balmer = ttk.Checkbutton(root, text='Balmer Lines ?', variable=checkvar1, onvalue = 1, offvalue = 0)
balmer.pack()

checkvar2=TK.IntVar()
gauss=ttk.Checkbutton(root, text='Balmer gaussian fit ?', variable=checkvar2, onvalue = 1, offvalue = 0)
gauss.pack()


#canvas = FigureCanvasTkAgg(fig, master=root)
#canvas._tkcanvas.pack()


root.mainloop()
 

#=========================END GUI====================================================================================




