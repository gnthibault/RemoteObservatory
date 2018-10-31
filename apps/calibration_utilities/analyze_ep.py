import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import scipy.interpolate
import scipy.signal 
import scipy.optimize


# time stuff
from dateutil.parser import parse
from datetime import datetime, date, time, timedelta


def plot_data(data, basename, timestep, ax, ax2, ax3, filename):
    # plot raw data
    ax.plot(data['x'], data[basename], label=filename)

    # plot a version where first order polynomial has been removed, and content
    # has been resampled and aligned
    x = data['x_resampled_lag']
    y = data[basename+'_highpass_resampled']
    ax2.plot(x, y, label=filename)
    ax2.set_ylim(np.percentile(y,2)*2, np.percentile(y,98)*2)

    # plot fourier transform of the error in original format
    fourier = np.fft.rfft(y)
    n = y.size
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

    # first, build the dictionary of data
    datas = {}
    for filename in [f for f in os.listdir(directory) if f.endswith('.csv')]:
        # load data
        full_filename=os.path.join(directory, filename)
        print('loading {}'.format(full_filename))
        df=pd.read_csv(full_filename, index_col=False)
        x=df[' Time Elapsed (sec)'] #.apply(parse)
        #x=(x-x.min()).dt.total_seconds()
        ra_y=df[' RA Error (arcsec)']
        dec_y=df[' DE Error (arcsec)']
        #Add new entry
        datas[filename]={'x':x, 'y_ra':ra_y, 'y_dec':dec_y}
        #plot_data(x, ra_y, ra_ax, ra_ax2, ra_ax3, filename)
        #plot_data(x, dec_y, dec_ax, dec_ax2, dec_ax3, filename)

    # save a version where first order polynomial has been removed
    for key, data in datas.items():
        x = data['x']
        for dataname in ['y_ra', 'y_dec']:
            y = data[dataname]
            pol = np.polyfit(x, y, deg=1)
            pol = scipy.optimize.least_squares(lambda m, x, y: m[1]+m[0]*x-y,
                pol, loss='huber', args=(x, y))['x'] #loss='soft_l1'
            #print('pol is {}'.format(pol))
            y2 = y-np.sum([pol[len(pol)-1-i]*(x**i) for i in range(len(pol))],
                          axis=0)
            data[dataname+'_highpass'] = y2

    # Now try to find a common time step. Best policy is to select the timestep
    # that offers the best spectral resolution given some min/max constraints
    timesteps = []
    weights = []
    for key, data in datas.items():
        x = data['x']
        timesteps.append(np.mean(np.roll(x,-1)[:-1]-x[:-1]))
        weights.append(len(x))
    timestep = (np.array(timesteps)*np.array(weights)).sum()/sum(weights)

    # resample all signals exactly on the same regular grid
    for key, data in datas.items():
        x = data['x']
        new_x = np.arange(np.round((x.max()-x.min())/timestep)+1)*timestep
        for dataname in ['y_ra_highpass', 'y_dec_highpass']:
            y = data[dataname]
            interp = scipy.interpolate.interp1d(x, y, kind='cubic',
                                                fill_value='extrapolate')
            data[dataname+'_resampled'] = interp(new_x)
        data['x_resampled'] = new_x

    ###############################################################
    # Now we would like to register signals on y_ra reference     #
    ###############################################################
    # first, we choose the longest time serie as a reference
    longest_time_serie = max(datas, key=lambda k: len(datas[k]['x']))
    dataname = 'y_ra_highpass_resampled'
    ref_y = datas[longest_time_serie][dataname]

    # Now, find the lag with respect to reference(fp number)
    for key, data in datas.items():
        y = data[dataname]
        if key==longest_time_serie:
            lag = 0
        else:
            lag = np.argmax(np.convolve(y[::-1],ref_y,mode='valid')) * timestep
        #Now that lag is given, we may pad with nans ?
        data['lag'] = lag
        data['x_resampled_lag'] = data['x_resampled']+lag

    ###########################
    # Now plot everything     #
    ###########################
    for filename, data in datas.items():
        #Add new entry
        plot_data(data, 'y_ra', timestep, ra_ax, ra_ax2, ra_ax3, filename)
        plot_data(data, 'y_dec', timestep, dec_ax, dec_ax2, dec_ax3, filename)


    # Set ticks/cosmetic stuff
    #ax.locator_params(which='x', tight=True, nbins=4)
    #for fig in [ra_fig, dec_fig]:
        #fig.tight_layout()
    legend_fontsize=6
    for ax in [ra_ax, ra_ax2, ra_ax3, dec_ax, dec_ax2, dec_ax3]:
        ax.legend(fontsize=legend_fontsize)
    plt.show()



if __name__ == '__main__':

    # Get the command line option
    parser = argparse.ArgumentParser(
        description="Make a plot periodic error for all csv data of the directory")
    parser.add_argument('--directory', #mandatory=True,
        help="directory containing csv")
    args = parser.parse_args()
    analyze_ep(directory=args.directory)


