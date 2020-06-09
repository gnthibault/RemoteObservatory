# Basic stuff
import argparse
import logging
import os

# Numerical stuff
import numpy as np
import scipy.stats as sist


# Viz stuff
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Miscellaneous ios
from astropy.io import fits

# Astropy
import astropy.units as u


def spliti(size):
    """
        returns split index given a size
    """
    return size//2

def dyadic_index_generator(start_index, end_index, min_ok_size):
    size = end_index-start_index
    if size<2*min_ok_size:
        yield [start_index, end_index]
    else:
        yield from dyadic_index_generator(start_index, start_index+spliti(size),
                                   min_ok_size)
        yield from dyadic_index_generator(start_index+spliti(size), end_index,
                                   min_ok_size)

def patch_index_generator(shape, min_ok_size):
    #Iterate over x axis
    for start_x, end_x in dyadic_index_generator(0, shape[0], min_ok_size):
        # iterate over y axis
        for start_y, end_y in dyadic_index_generator(0, shape[1], min_ok_size):
            yield [start_x, end_x, start_y, end_y]

def variance_test(global_variance, local_vector):
    n = len(local_vector)
    q_value = ((n-1)*local_vector.var())/global_variance
    return sist.chi2.sf(q_value, n-1)

def multiscale_variance_analysis(image):
    # The very first task is to check the global image variance
    global_variance = image.var()

    # Next task is to decompose the image in dyadic scale
    # We want to perform the analysis until we reach a patch size of minimum
    # 4x4 pixels
    shape = image.shape
    histogram_patch_size = []
    histogram_freq_problem = []
    max_freq = 0
    max_freq_image = np.zeros_like(image, dtype=np.float32)
    total_nb_image = 0
    while min(shape)>=4:
        image_to_show = image.astype(np.float32)
        min_ok_size = min(shape)
        histogram_patch_size.append(min_ok_size)
        histogram_freq_problem.append(0)
        total_nb_patch = 0
        for idx in patch_index_generator(image.shape, min_ok_size):
            patch = image[idx[0]:idx[1],idx[2]:idx[3]]
            p_value = variance_test(global_variance, patch.flatten())
            #image_to_show[idx[0]:idx[1],idx[2]:idx[3]] *= max(0.5, p_value>0.05)
            #image_to_show[idx[0]:idx[1],idx[2]:idx[3]] *= (1.5-p_value)
            max_freq_image[idx[0]:idx[1],idx[2]:idx[3]] += p_value
            if p_value < 0.05:
                histogram_freq_problem[-1]+=1
            total_nb_patch += 1
        histogram_freq_problem[-1]/=total_nb_patch
        if histogram_freq_problem[-1]>max_freq:
            max_freq=histogram_freq_problem[-1]
            #max_freq_image = image_to_show
        shape = tuple(np.array(shape)//2)
        total_nb_image += 1

    fig, ax = plt.subplots(1,2, figsize=(16,9))
    ax[0].imshow((1.25-(max_freq_image/total_nb_image))*image)
    ax[0].axis('off')
    heatmap = ax[1].imshow(max_freq_image/total_nb_image, cmap='jet')
    divider = make_axes_locatable(ax[1])
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(heatmap, format=FormatStrFormatter('%.2e'), cax=cax)
    ax[1].axis('off')
    plt.show()

def main(input_file, show_plot=False):

    f = fits.open(input_file)
    header, im = f[0].header, f[0].data
    #import scipy.misc as misc
    #im = misc.face()[:,:,0]
    multiscale_variance_analysis(im)

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', '-i', help='Path to the image file')
    parser.add_argument('--show_plot', '-s', dest='show_plot', action='store_true',
        help='Whether to interactively show the plots or not', default=False)
    args = parser.parse_args()
    main(args.input_file, args.show_plot)

