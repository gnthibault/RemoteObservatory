# generic import
from collections import namedtuple
import datetime
import os

# Astropy
from astropy import units as u
from astropy import wcs
from astropy.coordinates import EarthLocation
from astropy.coordinates import FK5
from astropy.coordinates import ICRS
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time

# Local stuff
from Base.Base import Base
from Imaging import fits as fits_utils

OffsetError = namedtuple('OffsetError', ['delta_ra', 'delta_dec', 'magnitude'])
class OffsetError:
    def __init__(self, delta_ra, delta_dec, magnitude):
        self.delta_ra = delta_ra
        self.delta_dec = delta_dec
        self.magnitude = magnitude

    def __str__(self):
        return f"ra:{self.delta_ra}: ,dec:{self.delta_dec}, mag:{self.magnitude}"

    def __repr__(self):
        return f"ra:{self.delta_ra}: ,dec:{self.delta_dec}, mag:{self.magnitude}"


class Image(Base):

    def __init__(self, fits_file, wcs_file=None, location=None):
        """Object to represent a single image from a PANOPTES camera.

        Args:
            fits_file (str): Name of FITS file to be read (can be .fz)
            wcs_file (str, optional): Name of FITS file to use for WCS
        """
        super().__init__()
        assert os.path.exists(fits_file), f"File does not exist: {fits_file}"

        if fits_file.endswith('.fz'):
            fits_file = fits_utils.fpack(fits_file, unpack=True)

        assert fits_file.lower().endswith(('.fits')), \
            self.logger.warning('File must end with .fits')

        self.wcs = None
        self._wcs_file = None
        self.fits_file = fits_file

        if wcs_file is not None:
            self.wcs_file = wcs_file
        else:
            self.wcs_file = fits_file

        with fits.open(self.fits_file, 'readonly') as hdu:
            self.header = hdu[0].header

        assert 'DATE-OBS' in self.header, self.logger.warning(
            'FITS file must contain the DATE-OBS keyword')
        assert 'EXPTIME' in self.header, self.logger.warning(
            'FITS file must contain the EXPTIME keyword')

        # Location Information
        if location is None:
            cfg_loc = self.config['observatory']
            location = EarthLocation(lat=cfg_loc['latitude'],
                                     lon=cfg_loc['longitude'],
                                     height=cfg_loc['elevation'],
                                     )
        # Time Information
        self.starttime = Time(self.header['DATE-OBS'], location=location)
        self.exptime = float(self.header['EXPTIME']) * u.second
        self.midtime = self.starttime + (self.exptime / 2.0)
        self.sidereal = self.midtime.sidereal_time('apparent')
        self.FK5_Jnow = FK5(equinox=self.midtime)

        # Coordinates from header keywords
        self.header_pointing = None
        self.header_ra = None
        self.header_dec = None
        #self.header_ha = None

        # Coordinates from WCS written by astrometry
        self.pointing = None
        self.ra = None
        self.dec = None

        self.get_header_pointing()
        self.get_wcs_pointing()

        self._luminance = None
        self._pointing = None
        self._pointing_error = None

    @property
    def wcs_file(self):
        """WCS file name

        When setting the WCS file name, the WCS information will be read,
        setting the `wcs` property.
        """
        return self._wcs_file

    @wcs_file.setter
    def wcs_file(self, filename):
        if filename is not None:
            try:
                w = wcs.WCS(filename)
                assert w.is_celestial

                self.wcs = w
                self._wcs_file = filename
                self.logger.debug("WCS loaded from image")
            except Exception:
                pass

    def pointing_error(self, pointing_reference_coord=None):
        """Pointing error namedtuple (delta_ra, delta_dec, magnitude)

        Returns pointing error information. The first time this is accessed
        this will solve the field if not previously solved.

        Returns:
            namedtuple: Pointing error information
        """
        if (self._pointing_error is None) or not (pointing_reference_coord is None):
            assert self.pointing is not None, "No world coordinate system (WCS), can't get pointing_error"
            assert self.header_pointing is not None

            if self.wcs is None:
                self.solve_field()

            # TODO First, make sure both coordinates are in the same coordinate system
            if pointing_reference_coord is None:
                pointing_reference_coord = self.header_pointing

            ref_pointing = pointing_reference_coord.transform_to(self.pointing.frame)
            mag = self.pointing.separation(ref_pointing)
            d_ra = self.pointing.ra - ref_pointing.ra
            d_dec = self.pointing.dec - ref_pointing.dec

            self._pointing_error = OffsetError(
                d_ra.to(u.arcsec),
                d_dec.to(u.arcsec),
                mag.to(u.arcsec)
            )

        return self._pointing_error

    def get_center_coordinates(self):
        """
        Those are 0-based indexing, also from documentation:
        https://docs.astropy.org/en/stable/api/astropy.wcs.WCS.html#astropy.wcs.WCS.pixel_to_world_values
        Note that pixel coordinates are assumed to be 0 at the center of the first pixel in each dimension
        :return:
        """
        return (self.header["NAXIS1"]/2-0.5,
                self.header["NAXIS2"]/2-0.5)

    def get_header_pointing(self):
        """Get the pointing information from the header

        The header should contain the `RA-FIELD` and `DEC-FIELD` keywords, from
        which the header pointing coordinates are built. Those two entries are
        written by us as J2000 format, which might not be the expected format for the
        astrometric resolution
        """
        try:
            self.header_pointing = SkyCoord(
                ra=float(self.header['RA-FIELD']) * u.degree,
                dec=float(self.header['DEC-FIELD']) * u.degree,
                frame='icrs', equinox='J2000.0')

            self.header_ra = self.header_pointing.ra.to(u.hourangle)
            self.header_dec = self.header_pointing.dec.to(u.degree)
            # Precess to the current equinox otherwise the RA - LST method will
            # be off.
            #self.header_ha = self.header_pointing.transform_to(
            #    self.FK5_Jnow).ra.to(u.hourangle) - self.sidereal
        except Exception as e:
            msg = 'Cannot get header pointing information: {}'.format(e)
            self.logger.error(msg)
            raise RuntimeError(msg)

    def get_wcs_pointing(self):
        """Get the pointing information from the WCS
        Builds the pointing coordinates from the plate-solved WCS. These will be
        compared with the coordinates stored in the header.
        One should notice that Astrometry.net uses J2000 equinox in general,
        however, we assume the install related to Gaia DR2 + Tycho2 catalogs, which are J2015.5
        see https://portal.nersc.gov/project/cosmo/temp/dstn/index-5200/LITE/
        """
        if self.wcs is not None:
            # This was wrong because crval coord relates to crpix reference pixels
            # ra = self.wcs.celestial.wcs.crval[0]
            # dec = self.wcs.celestial.wcs.crval[1]

            # TODO TN trying alternative definition
            cx, cy = self.get_center_coordinates()
            radeg, decdeg = self.wcs.all_pix2world(
                cx,
                cy,
                0,  # 0-based indexing
                ra_dec_order=True)

            # fk5_J2015_5 = FK5(equinox=Time(datetime.datetime(year=2015, month=6, day=30)))
            # pointing = SkyCoord(ra=radeg*u.degree,
            #                     dec=decdeg*u.degree,
            #                     frame=fk5_J2015_5,
            #                     obstime=Time(datetime.datetime(year=2015, month=6, day=30)))
            # icrs_j2k = ICRS()
            # self.pointing = pointing.transform_to(icrs_j2k)

            icrs_j2k = ICRS()
            self.pointing = SkyCoord(ra=radeg*u.degree,
                                dec=decdeg*u.degree,
                                frame=icrs_j2k)

            self.ra = self.pointing.ra.to(u.hourangle)
            self.dec = self.pointing.dec.to(u.degree)
            # Precess to the current equinox otherwise the RA - LST method
            # will be off.
            #self.ha = self.pointing.transform_to(self.FK5_Jnow).ra.to(
            #    u.hourangle) - self.sidereal

    def all_pix2world(self, x, y):
        coord_ra, coord_dec = self.wcs.all_pix2world(
            x,
            y,
            0,  # 0-based indexing
            ra_dec_order=True)
        # fk5_J2015_5 = FK5(equinox=Time(datetime.datetime(year=2015, month=6, day=30)))
        # coord = SkyCoord(ra=coord_ra*u.deg,
        #                  dec=coord_dec*u.deg,
        #                  frame=fk5_J2015_5,
        #                  obstime=Time(datetime.datetime(year=2015, month=6, day=30)))
        # icrs_j2k = ICRS()
        icrs_j2k = ICRS()
        coord = SkyCoord(ra=coord_ra * u.deg,
                                 dec=coord_dec * u.deg,
                                 frame=icrs_j2k)

        return coord.transform_to(icrs_j2k)

    def solve_field(self, **kwargs):
        """ Solve field and populate WCS information
            If you use basic catalog for astrometry.net, it is J2K!
        Args:
            **kwargs (dict): Options to be passed to `get_solve_field`
        """
        if kwargs.get("use_header_position", False):
            kwargs.update(dict(
                ra=self.header_pointing.ra.value,
                dec=self.header_pointing.dec.value,
            ))
            if "radius" not in kwargs:
                kwargs["radius"] = 1
        solve_info = fits_utils.get_solve_field(
            self.fits_file,
            config=self.config,
            **kwargs)
        self.wcs_file = solve_info['solved_fits_file']
        self.get_wcs_pointing()

        # Remove some fields
        for header in ['COMMENT', 'HISTORY']:
            try:
                del solve_info[header]
            except KeyError:
                pass

        return solve_info

    def compute_offset(self, ref_image):
        assert isinstance(ref_image, Image), self.logger.warning(
            "Must pass an Image class for reference")

        # Make sure we are in the same frame/equinox
        ref_pointing = ref_image.pointing.transform_to(self.pointing.frame)
        mag = self.pointing.separation(ref_pointing)
        d_dec = self.pointing.dec - ref_pointing.dec
        d_ra = self.pointing.ra - ref_pointing.ra

        return OffsetError(d_ra.to(u.arcsec), d_dec.to(u.arcsec), mag.to(u.arcsec))


###############################################################################
# Private Methods
###############################################################################

    def __str__(self):
        return "{}: {}".format(self.fits_file, self.header_pointing)
