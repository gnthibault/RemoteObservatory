# Basic stuff
import io
import logging
import logging.config
import sys

#For test purpose
import matplotlib.pyplot as plt

#Astropy stuff
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits

#Astroquery stuff
from astroquery.skyview import SkyView

sys.path.append('.')

# Local stuff : Astrometry server
from Service.NovaAstrometryService import NovaAstrometryService

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger('mainLogger')

    # First get a sky image from astropy
    coord = SkyCoord.from_name("M1")
    coord_dict = {'ra':coord.ra.degree, 'dec':coord.dec.degree}
    position = coord.icrs
    coordinates = 'icrs'
    hdu = SkyView.get_images(position=position, coordinates=coordinates,
                             survey='DSS', radius=100*u.arcmin,
                             grid=False)[0][0]
    f = fits.HDUList(hdu)
    #plt.imshow(hdu.data)
    #plt.axis('off')
    #plt.show()

    nova = NovaAstrometryService(logger=logger,configFileName='local')
    nova.login()
    t=io.BytesIO()
    f.writeto(t)
    astrometry = nova.solveImage(t.getvalue(), coordSky=coord_dict,
                                 downsample_factor=1)
    print('Found RA of {} instead of ground truth: {}'.format(
          astrometry['ra'], coord_dict['ra']))
    print('Found DEC of {} instead of ground truth: {}'.format(
          astrometry['dec'], coord_dict['dec']))

