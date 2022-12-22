# numerical tools
import numpy as np

# Data viz
import matplotlib.pyplot as plt

# Astropy
from astropy.io import fits
from astropy import units as u
from astropy.visualization import AsymmetricPercentileInterval, ImageNormalize, MinMaxInterval, SqrtStretch
from astropy.wcs import WCS

img_filename = "/var/RemoteObservatory/images/targets/HCG49/012345/20221222T070425/pointing00.new"
xy_filename = "/var/RemoteObservatory/images/targets/HCG49/012345/20221222T070425/pointing00.axy"

# Open image file
hdu = fits.open(img_filename)[0]
wcs = WCS(hdu.header)
data = hdu.data.astype(np.float32)

# Open star detection image file
detections = fits.open(xy_filename)[1].data

# detection data
px_centers = np.array([[x, y] for x,y,_,_ in detections])           # np.array of shape is (n, 2)
rd_centers = [wcs.pixel_to_world(*px.tolist()) for px in px_centers] # list of SkyCoord

#TODO TN CHANGE
rd_target_star_reference = rd_centers[0]
px_target_star_reference = wcs.world_to_pixel(rd_target_star_reference)
max_identification_error = 0.75*u.arcsec

rd_closest_detection = min(rd_centers, key=lambda x: x.separation(rd_target_star_reference))
closest_distance = rd_closest_detection.separation(rd_target_star_reference)
if closest_distance <= max_identification_error:
    px_candidate_star = wcs.world_to_pixel(rd_closest_detection)
else:
    px_candidate_star = None

# Show image
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
plt.show()