# Generic tools
import os

# numerical tools
import numpy as np

# Data viz
import matplotlib.pyplot as plt

# Astropy
from astropy.io import fits
from astropy import units as u
from astropy.visualization import AsymmetricPercentileInterval, ImageNormalize, MinMaxInterval, SqrtStretch
from astropy.wcs import WCS

def find_best_candidate_star(pointing_image,
                             target,
                             max_identification_error,
                             make_plots=True):
    """
    It is very important to read this page to understand how to preoperly use wcs:
    https://docs.astropy.org/en/stable/wcs/note_sip.html

    This has not been a strict convention in the past and the default in astropy.wcs is to always include the SIP
    distortion if the SIP coefficients are present, even if -SIP is not included in CTYPE. The presence of a -SIP
    suffix in CTYPE is not used as a trigger to initialize the SIP distortion.
    It is important that headers implement correctly the SIP convention. If the intention is to use the SIP distortion,
    a header should have the SIP coefficients and the -SIP suffix in CTYPE.
    astropy.wcs prints INFO messages when inconsistent headers are detected, for example when SIP coefficients are
    present but CTYPE is missing a -SIP suffix, see examples below. astropy.wcs will print a message about the
    inconsistent header but will create and use the SIP distortion and it will be used in calls to all_pix2world.
    If this was not the intended use (e.g. it’s a drizzled image and has no distortions) it is best to remove the SIP
    coefficients from the header. They can be removed temporarily from a WCS object by:
    >>> wcsobj.sip = None
    In addition, if SIP is the only distortion in the header, the two methods, wcs_pix2world and wcs_world2pix,
    may be used to transform from pixels to world coordinate system while omitting distortions. Another consequence
    of the inconsistent header is that if to_header() is called with relax=True it will return a header with SIP
    coefficients and a -SIP suffix in CTYPE and will not reproduce the original header.
    In conclusion, when astropy.wcs detects inconsistent headers, the recommendation is that the header is inspected
    and corrected to match the data. Below is an example of a header with SIP coefficients when -SIP is missing from
    CTYPE. The data is drizzled, i.e. distortion free, so the intention is not to include the SIP distortion.

    Now from: https://docs.astropy.org/en/stable/api/astropy.wcs.WCS.html#astropy.wcs.WCS.all_pix2world
    Transforms pixel coordinates to world coordinates. Performs all of the following in series:
        - Detector to image plane correction (if present in the FITS file)
        - SIP distortion correction (if present in the FITS file)
        - distortion paper table-lookup correction (if present in the FITS file)
        - wcslib “core” WCS transformation

    :param pointing_image:
    :param target:
    :param max_identification_error:
    :param make_plots:
    :return:
    """

    img_directory = os.path.dirname(pointing_image.fits_file)
    img_filename = pointing_image.fits_file
    xy_filename = os.path.splitext(img_filename)[0]+".axy"

    # Open image file
    hdu = fits.open(img_filename)[0]
    wcs = WCS(hdu.header)
    data = hdu.data.astype(np.float32)

    # Open star detection image file
    detections_data = fits.open(xy_filename)[1].data

    # detection data
    detections = [((x,y), flux) for x,y,flux,bkg in detections_data]
    #fluxes = np.array([flux for (x, y), flux in detections])
    px_centers = np.array([[x, y] for (x, y), flux in detections])            # np.array of shape is (n, 2)
    rd_centers = [wcs.pixel_to_world(*px.tolist()) for px in px_centers] # list of SkyCoord
    # rd_centers = list(map(
    #     lambda x: SkyCoord(x[0]*u.hourangle, x[1]*u.degree),
    #     wcs.all_pix2world(px_centers, 0).tolist()))
    # site-packages/astropy/wcs/wcsapi/fitswcs.py:347: UserWarning: 'WCS.all_world2pix' failed to converge to the requested accuracy.
    # After 20 iterations, the solution is diverging at least for one input point.

    rd_target_star_reference = target
    px_target_star_reference = wcs.world_to_pixel(rd_target_star_reference)

    i_closest = min(range(len(rd_centers)), key=lambda i: rd_centers[i].separation(rd_target_star_reference))
    rd_closest_detection = rd_centers[i_closest]
    closest_distance = rd_closest_detection.separation(rd_target_star_reference)
    if closest_distance <= max_identification_error:
        px_candidate_star = px_centers[i_closest] #wcs.world_to_pixel(rd_closest_detection)
    else:
        px_candidate_star = None
        rd_closest_detection = None

    if make_plots:
        ax = plt.subplot(projection=wcs, label='overlays')
        fig = ax.get_figure()
        norm = ImageNormalize(data, interval=MinMaxInterval(), stretch=SqrtStretch())
        ax.imshow(data, origin='lower', cmap='gray', norm=norm)

        # Show detected star in green, or theoretical star in red
        radius = max(3, int(np.ceil(min(data.shape)*0.005)))
        if px_candidate_star is not None:
            circle = plt.Circle(px_candidate_star, radius, color='g', fill=False)
        else:
            circle = plt.Circle(px_target_star_reference, radius, color='r', fill=False)
        ax.add_patch(circle)

        ra = ax.coords['ra']
        ra.set_ticks()
        #ra.set_ticks_position()
        ra.set_ticklabel(size=12)
        ra.set_ticklabel_position('l')
        ra.set_axislabel('RA', minpad=0.3)
        ra.set_axislabel_position('l')
        ra.grid(color='yellow', ls='-', alpha=0.3)
        ra.set_format_unit(u.hourangle)
        ra.set_major_formatter('hh:mm:ss')

        dec = ax.coords['dec']
        dec.set_ticks()
        #dec.set_ticks_position()
        dec.set_ticklabel(size=12)
        dec.set_ticklabel_position('b')
        dec.set_axislabel('DEC', minpad=0.3)
        dec.set_axislabel_position('b')
        dec.grid(color='yellow', ls='-', alpha=0.3)
        dec.set_format_unit(u.degree)
        dec.set_major_formatter('dd:mm:ss')

        fig.set_tight_layout(True)
        plot_path = f"{img_directory}/adjust_pointing_detection.jpg"
        fig.savefig(plot_path, transparent=False)

        # explicitly close and delete figure
        fig.clf()
        del fig
    return px_candidate_star

def get_brightest_detection(pointing_image):
    img_filename = pointing_image.fits_file
    xy_filename = os.path.splitext(img_filename)[0]+".axy"

    # Open star detection image file
    detections_data = fits.open(xy_filename)[1].data

    # detection data
    detections = [((x, y), flux) for x,y,flux,bkg in detections_data]
    fluxes = np.array([flux for (x, y), flux in detections])
    px_centers = np.array([[x, y] for (x, y), flux in detections])  # np.array of shape is (n, 2)
    max_flux_index = np.argmax(fluxes)
    return px_centers[max_flux_index]