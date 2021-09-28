#Basic stuff
import datetime
import io
import logging
import os
import threading
import traceback

# Astropy for handling FITS
from astropy.io import fits

# Local stuff
from Base.Base import Base

class FitsWriter(Base):
    """
      Check FITS manipulation with astropy:
      http://docs.astropy.org/en/stable/io/fits/
    """

    def __init__(self, observatory=None, servWeather=None, servTime=None,
                 servAstrometry=None, filterWheel=None, telescope=None,
                 camera=None, path='./images'):
        self.logger.debug('Configuring FitsWriter')
        self.imgIdx = 0
        self.observatory = observatory
        self.servWeather = servWeather
        self.servTime = servTime
        self.servAstrometry = servAstrometry
        self.filterWheel = filterWheel
        self.telescope = telescope
        self.camera = camera
        self.ephem = None #TODO TN to be improved

        path_idx = 0

        #Create a new path, whatever the input is
        path = os.path.realpath(path)
        test_path = path
        while os.path.exists(test_path):
            test_path = (path+'-'+str(datetime.datetime.now().date())+'-'+
                         str(path_idx))
            path_idx += 1
        os.makedirs(test_path, exist_ok=False)
        self.path = test_path

        self.threadLock = threading.Lock()

        self.logger.debug('FitsWriter configured successfully')

    def writeWithTag(self, fits, targetName='frame'):
        '''
          First step: tag with every possible information
          Seconnd step: Write fits to disk
        '''
        try:
            try:
                hdr = fits.header
            except:
                hdr = fits[0].header
            
            if self.servTime is not None:
                hdr['UTCTIME'] = (str(self.servTime.get_utc()), 'NC')
            if self.filterWheel is not None:
                filterName = self.filterWheel.currentFilter()[1]
                hdr['FILTER'] = (filterName, 'NC')
            if self.camera is not None:
                hdr['EXPOSURETIMESEC'] = (str(self.camera.getExposureTimeSec()),
                                          'NC')
                hdr['GAIN'] = (str(self.camera.getGain()), 'NC')
            if self.observatory is not None:
                hdr['OBSERVER'] = (self.observatory.getOwnerName(), 'NC')
                hdr['GPSCOORD'] = (str(self.observatory.get_gps_coordinates()),
                                   'NC')
                hdr['ALTITUDEMETER'] = (str(self.observatory.get_altitude_meter()
                                        ), 'NC')
            if self.servWeather is not None:
                hdr['TEMPERATUREC'] = (str(self.servWeather.getTemp_c()), 'NC')
                hdr['RELATIVEHUMIDITY'] = (str(self.servWeather.
                                               getRelative_humidity()), 'NC')
                hdr['WINDKPH'] = (str(self.servWeather.getWind_kph()), 'NC')
                hdr['WINDGUSTKPH'] = (str(self.servWeather.getWind_gust_kph()),
                                      'NC')
                hdr['PRESSUREMB'] = (str(self.servWeather.getPressure_mb()),
                                     'NC')
                hdr['DEWPOINTC'] = (str(self.servWeather.getDewpoint_c()),
                                    'NC')
                hdr['VISIBILITYKM'] = (str(self.servWeather.getVisibility_km()),
                                       'NC')
                hdr['WEATHER'] = (self.servWeather.getWeatherQuality(), 'NC')
            if self.ephem is not None:
                hdr['SUNSEPARATION'] = (str(self.ephem.getSunSeparation(
                    target_name)), 'NC')
                hdr['MOONSEPARATION'] = (str(self.ephem.getMoonSeparation(
                    target_name)), 'NC')
                hdr['MOONILLUMINATEDPERC'] = (str(
                    self.ephem.getMoonPercentIlluminated()), 'NC')
                hdr['AIRMASS'] = (str(
                    self.ephem.getAirMass(target_name)), 'NC')
            if self.servAstrometry is not None:
                t=io.BytesIO()
                fits.writeto(t)
                #TODO TN try to input some more informations for solving
                self.servAstrometry.solveImage(t.getvalue())
                hdr['PARITY'] = (str(self.servAstrometry.getCalib()['parity']),
                                 'NC')
                hdr['ORIENTATION'] = (str(self.servAstrometry.getCalib()[
                                          'orientation']), 'NC')
                hdr['PIXSCALE'] = (str(self.servAstrometry.getCalib()[
                                       'pixscale']), 'NC')
                hdr['RADIUS'] = (str(self.servAstrometry.getCalib()['radius']),
                                 'NC')
                hdr['RA'] = (str(self.servAstrometry.getCalib()['ra']), 'NC')
                hdr['DEC'] = (str(self.servAstrometry.getCalib()['dec']), 'NC')
            if self.telescope is not None:
                hdr['TELESCOPE'] = (str(self.telescope.getName()), 'NC')
                hdr['FOCALLENGHT'] = (str(self.telescope.getFocale()), 'NC')
                hdr['DIAMETER'] = (str(self.telescope.getDiameter()), 'NC')
                hdr['TELESCOPERA'] = (str(self.telescope.getCurrentSkyCoord()[
                                          'RA']), 'NC')
                hdr['TELESCOPEDEC'] = (str(self.telescope.getCurrentSkyCoord()[
                                           'DEC']), 'NC')
            if targetName is not None:
                hdr['TARGETNAME'] = (targetName, 'NC')

            # Last comment then write everything to disk
            hdr['COMMENT'] = 'No generic comment, life is beautiful'
        except Exception as e:
            self.logger.error('FitsWriter error while tagging fit with index '
                              ' {} : {}'.format(self.imgIdx,e))

        filename='{}-{}.fits'.format(targetName,self.imgIdx)
        try:
            with open(os.path.join(self.path,filename), "wb") as f:
                fits.writeto(f, overwrite=True)
                with self.threadLock:
                    self.imgIdx += 1
        except Exception as e:
            self.logger.error('FitsWriter error while writing file {} : {}'
                              ''.format(filename,e))

