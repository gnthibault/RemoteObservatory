# base stuff

# numerical stuff
import numpy as np

# Viz stuff
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

# image stuff
import rawpy

path='/home/gnthibault/Documents/Div/Astro/vignetting/DSC08056.ARW'
with rawpy.imread(path) as raw:
   rgb = raw.postprocess(gamma=(1,1), no_auto_bright=True, output_bps=16)
s = rgb.sum(axis=2)
s = s/s.max()

#def draw_gain_exp_heatmap(self, temperature, info_map, map_title, figname):
#    """ x-axis is time, y-axis is gain
#    """

fig, ax = plt.subplots()
heatmap = ax.imshow(s.T, cmap='jet')
plt.colorbar(heatmap, format=FormatStrFormatter('%.2e'))

# We want to show all ticks...
#ax.set_xticks(np.arange(len(self.exp_time_list)))
#ax.set_yticks(np.arange(len(self.gain_list)))
# ... and label them with the respective list entries
#formatter = lambda x: "{:.2E}".format(x)
#ax.set_xticklabels(map(formatter, self.exp_time_list))
#ax.set_yticklabels(map(formatter, self.gain_list))

# Rotate the tick labels and set their alignment.
#plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
#         rotation_mode="anchor")

# set infos about the plot
#ax.set_title(map_title+' - (camera: '+self.cam.name+')')
#ax.set_xlabel('Exposure time in s')
#ax.set_ylabel('Camera gain')

fig.tight_layout()
#if self.show_plot:
plt.show()
#fig.savefig(figname, dpi=fig.dpi)

