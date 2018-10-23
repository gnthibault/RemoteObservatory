import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

# time stuff
from dateutil.parser import parse
from datetime import datetime, date, time, timedelta



# First, define the base figure
fig=plt.figure()
ax=fig.add_subplot(311)
ax2=fig.add_subplot(312)
ax3=fig.add_subplot(313)

# Set title stuff
fig.suptitle('Sidereal tracking error on Losmandy G11, with NS kit', fontsize=16)
ax.set_title('Raw data')
ax.set_xlabel('Time Elapsed (sec)')
ax.set_ylabel('RA Error (arcsec)')
ax2.set_title('Sanitized data with up to first order drift removed')
ax2.set_xlabel('Time Elapsed (sec)')
ax2.set_ylabel('RA Error (arcsec)')
ax3.set_title('Error on Dec (raw data)')
ax3.set_xlabel('Time Elapsed (sec)')
ax3.set_ylabel('DE Error (arcsec)')


for filename in [f for f in os.listdir() if f.endswith('.csv')]:
    # load data
    print('loading {}'.format(filename))
    df=pd.read_csv(filename, index_col=False)
    x=df[' Time Elapsed (sec)'] #.apply(parse)
    #x=(x-x.min()).dt.total_seconds()
    y=df[' RA Error (arcsec)']
    ydec=df[' DE Error (arcsec)']

    # plot original data
    ax.plot(x,y, label=filename)

    # plot a version where first order polynomial has been removed
    pol = np.polyfit(x, y, deg=1)
    print('pol is {}'.format(pol))
    y2 = y-np.sum([pol[pol.size-1-i]*(x**i) for i in range(pol.size)], axis=0)
    ax2.plot(x, y2, label=filename)

    # plot dec error in original format
    ax3.plot(x,ydec, label=filename)

# Set ticks/cosmetic stuff
#ax.locator_params(which='x', tight=True, nbins=4)
#ax.set_ylim([-1.0, 1.0])
#ax.set_xlim([-1.0, 1.0])
fig.tight_layout()
ax.legend()
ax2.legend()
ax3.legend()
plt.show()


