import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

# time stuff
from dateutil.parser import parse
from datetime import datetime, date, time, timedelta


def plot_data(x, y, ax, ax2, ax3, filename):
    # plot raw data
    ax.plot(x, y, label=filename)

    # plot a version where first order polynomial has been removed
    pol = np.polyfit(x, y, deg=1)
    y2 = y-np.sum([pol[pol.size-1-i]*(x**i) for i in range(pol.size)], axis=0)
    ax2.plot(x, y2, label=filename)
    ax2.set_ylim(np.percentile(y2,2)*2, np.percentile(y2,98)*2)

    # plot fourier transform of the error in original format
    fourier = np.fft.rfft(y2)
    n = y2.size
    timestep = np.mean(np.roll(x,-1)[:-1]-x[:-1])
    freq = np.fft.rfftfreq(n, d=timestep)
    # assume max period of 10 minutes
    period=(1/freq)[::-1]
    newfourier=np.abs(fourier)[::-1]
    cut = period<10*60
    ax3.plot(period[cut], newfourier[cut], label=filename)
    #ax3.set_xlabel(1/freq, )

    for ax in [ax, ax2, ax3]:
        ax.yaxis.grid(True)
        ax.locator_params(nbins=19, axis='x')
        ax.locator_params(nbins=9, axis='y')

def analyze_ep(directory):
    # Set title stuff for RA axis
    ra_fig=plt.figure()
    ra_ax=ra_fig.add_subplot(311)
    ra_ax2=ra_fig.add_subplot(312)
    ra_ax3=ra_fig.add_subplot(313)
    ra_fig.suptitle('Sidereal tracking error on Losmandy G11, with NS kit: RA',
                 fontsize=16)
    ra_ax.set_title('Raw data')
    ra_ax.set_xlabel('Time Elapsed (sec)')
    ra_ax.set_ylabel('RA Error (arcsec)')
    ra_ax2.set_title('Sanitized data with up to first order drift removed')
    ra_ax2.set_xlabel('Time Elapsed (sec)')
    ra_ax2.set_ylabel('RA Error (arcsec)')
    ra_ax3.set_title('Fourier transform of RA errors')
    ra_ax3.set_xlabel('Time Period (in sec)')
    ra_ax3.set_ylabel('Magnitude')

    # Set title stuff for DEC axis
    dec_fig=plt.figure()
    dec_ax=dec_fig.add_subplot(311)
    dec_ax2=dec_fig.add_subplot(312)
    dec_ax3=dec_fig.add_subplot(313)
    dec_fig.suptitle('Sidereal tracking error on Losmandy G11, with NS kit: DEC',
                 fontsize=16)
    dec_ax.set_title('Raw data')
    dec_ax.set_xlabel('Time Elapsed (sec)')
    dec_ax.set_ylabel('DEC Error (arcsec)')
    dec_ax2.set_title('Sanitized data with up to first order drift removed')
    dec_ax2.set_xlabel('Time Elapsed (sec)')
    dec_ax2.set_ylabel('DEC Error (arcsec)')
    dec_ax3.set_title('Fourier transform of DEC errors')
    dec_ax3.set_xlabel('Time Period (in sec)')
    dec_ax3.set_ylabel('Magnitude')

    for filename in [f for f in os.listdir(directory) if f.endswith('.csv')]:
        # load data
        full_filename=os.path.join(directory, filename)
        print('loading {}'.format(full_filename))
        df=pd.read_csv(full_filename, index_col=False)
        x=df[' Time Elapsed (sec)'] #.apply(parse)
        #x=(x-x.min()).dt.total_seconds()
        ra_y=df[' RA Error (arcsec)']
        dec_y=df[' DE Error (arcsec)']
        plot_data(x, ra_y, ra_ax, ra_ax2, ra_ax3, filename)
        plot_data(x, dec_y, dec_ax, dec_ax2, dec_ax3, filename)


    # Set ticks/cosmetic stuff
    #ax.locator_params(which='x', tight=True, nbins=4)
    for fig in [ra_fig, dec_fig]:
        fig.tight_layout()
    legend_fontsize=6
    for ax in [ra_ax, ra_ax2, ra_ax3, dec_ax, dec_ax2, dec_ax3]:
        ax.legend(fontsize=legend_fontsize)
    plt.show()

if __name__ == '__main__':

    # Get the command line option
    parser = argparse.ArgumentParser(
        description="Make a plot periodic error for all csv data of the directory")
    parser.add_argument('--directory', default='.',
        help="directory containing csv")
    args = parser.parse_args()
    analyze_ep(directory=args.directory)


