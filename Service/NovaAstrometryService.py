# Basic stuff
import json
import logging
from pathlib import Path
import time

# Webservice stuff
import urllib

# Handle fits file
import io
from astropy.io import fits
from astropy import wcs

# Correcting for optical distortions
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata

# Forging request
import base64
from io import BytesIO
from email.generator import Generator
from email.generator import BytesGenerator
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application  import MIMEApplication
from email.encoders import encode_noop

class NovaAstrometryService():
    """ Nova Astrometry Service """
    # API request engine
    defaultAPIURL = 'http://nova.astrometry.net/api/'
    defaultLocalAPIURL = 'http://localhost/api/'
    defaultLocalKey = 'XXXXXXXX'

    def __init__(self, configFileName=None, logger=None, apiURL=defaultAPIURL):
        self.logger = logger or logging.getLogger(__name__)

        if configFileName is 'local':
            apiURL=NovaAstrometryService.defaultLocalAPIURL
            self.key = NovaAstrometryService.defaultLocalKey
        else:
            if configFileName is None:
                # Default file is ~/.nova.json
                home = Path.home()
                config = home / '.nova.json'
                self.configFileName = str(config)
            else:
                self.configFileName = configFileName

            # Now configuring
            self.logger.debug('Configuring Nova Astrometry Service with '
                              'file {}'.format(self.configFileName))

            # Get key from json
            with open(self.configFileName) as jsonFile:  
                data = json.load(jsonFile)
                self.key = data['key']

        # Api URL
        self.apiURL=apiURL
        # Manage persistent session/submissions/jobs with cookie like ID
        self.session = None
        self.submissionId = None
        self.jobId = None
        self.solvedId = None

        # Keep solution objects
        self.calibration = None
        self.wcs = None

        # Finished configuring
        self.logger.debug('Configured Nova Astrometry service successfully')

    def getAPIUrl(self, service):
        return self.apiURL + service


    def login(self):
        args = { 'apikey' : self.key }
        result = self.sendRequest('login', args)
        if result is not None:
          try:
            session = result['session']
            self.logger.debug('Nova Astrometry Service: Got session '+str(session))
          except Exception as e:
            self.logger.error('Nova Astrometry Service: No session in result, '+\
              'error is: '+str(e))
            session = None
        else:
          session = None
        self.session = session

    def getSubmissionStatus(self, subId, justdict=False):
        result = self.sendRequest('submissions/%s' % subId)
        if justdict:
          return result
        try:
          res = result['status']
        except Exception as e:
          res = None
          self.logger.error('Nova Astrometry Service: impossible to get '+\
            'submission status, error is: '+str(e))
        return res

    def getJobStatus(self, job_id):
        result = self.sendRequest('jobs/%s' % job_id)
        try:
          stat = result['status']
          if stat == 'success':
            result = self.sendRequest('jobs/%s/calibration' % job_id)
            self.logger.debug('Nova Astrometry Service, Calibration result: '+\
              str(result))
          return stat, result
        except Exception as e:
          self.logger.error('Nova Astrometry Service: impossible to get '+\
            'job status, error is: '+str(e))
          return None, None


    def solveImage(self, fitsFile, coordSky=None, scale_est=None,
                   downsample_factor=4):
        '''Center (RA, Dec):  (179.769, 45.100)
        Center (RA, hms): 11h 59m 04.623s
        Center (Dec, dms):  +45° 06' 01.339"
        Size: 25.4 x 20.3 arcmin
        Radius: 0.271 deg
        Pixel scale:  1.19 arcsec/pixel
        Orientation:  Up is 90 degrees E of N
        '''

        args = dict(
          allow_commercial_use='d',   # license stuff
          allow_modifications='d',    # license stuff
          publicly_visible='y',       # other can see request and data
          #scale_units='arcsecperpix', # unit for field size estimation
          #scale_type='ev',            # from target value+error instead of bounds
          #scale_est=1.19, # estimated field scale TODO Get from camera+scope
          #scale_err=2,                #[0, 100] percentage of error on field
          #center_ra=coordSky['ra'],   #float [0, 360] coordinate of image center TODO
          #center_dec=coordSky['dec'], #float [-90, 90] coordinate of image center on
                                      #right ascencion TODO
          radius=1.0,    # float in degrees around center_[ra,dec] TODO confidence
          downsample_factor=downsample_factor, # Ease star detection on images
          tweak_order=2,        # use order-2 polynomial for distortion correction
          use_sextractor=False, # Alternative star extractor method
          parity=2,   #geometric indication that can make detection faster (unused)
          crpix_center=True)

        if not (scale_est is None):
            args['scale_units']='arcsecperpix'
            args['scale_type']='ev'
            args['scale_est']=scale_est
            args['scale_err']=5
        if not (coordSky is None):
            args['center_ra']=coordSky['ra']
            args['center_dec']=coordSky['dec']

        # Now upload image
        upres = self.sendRequest('upload', args, fitsFile)
        try:
          stat = upres['status']
          if stat != 'success':
            self.logger.error('Nova Astrometry Service, upload failed: status '+\
              str(stat)+' and server response: '+str(upres))

          self.submissionId = upres['subid']
          self.logger.debug('Nova Astrometry Service, uploaded file successfully '+\
            ', got status '+str(stat)+' submission ID: '+str(self.submissionId))
        except Exception as e:
          self.logger.error('Nova Astrometry Service, upload failed :'+str(e))
          return None

        if self.solvedId is None:
          if self.submissionId is None:
            self.logger.error('Nova Astrometry Service : Can\'t --wait without '+\
              'a submission id or job id!')
            return None
            
          while True:
            try:
              stat = self.getSubmissionStatus(self.submissionId, justdict=True)
              self.logger.debug('Nova Astrometry service, status update for '+\
                ' submission ID '+str(self.submissionId)+' : '+str(stat))
              jobs = stat.get('jobs', [])
              if len(jobs):
                for j in jobs:
                  if j is not None:
                    break
                if j is not None:
                  self.logger.debug('Nova Astrometry Service: got a solved job '\
                    'id : '+str(j))
                  self.solvedId = j
                  break
              time.sleep(5)
            except Exception as e:
              self.logger.error('Nova Astrometry Service, for some reason, failed '\
                'while waiting for sbumission status: '+str(e))
              return None

        while True:
          stat, solution = self.getJobStatus(self.solvedId)
          self.logger.debug('Nova Astrometry Service, status update for job ID '+\
            str(self.solvedId)+' : '+str(stat))
          if stat in ['success']:
            success = True
            self.logger.debug('Nova Astrometry Service: server successfully '+\
              'solved job ID '+str(self.solvedId))
            break
          elif stat in ['failure']:
            success = False
            self.logger.debug('Nova Astrometry Service: server failed to solve '+\
              'job ID '+str(self.solvedId))
            break
          elif stat is None:
            break
          time.sleep(5)

        if success and self.solvedId:
          self.logger.debug('Nova Astrometry Service: Image has been solved: '+\
            str(solution))
        else:
          self.solvedId = None
          self.logger.error('Nova Astrometry Service: Image solving failed')
     
        self.calibration = solution
        return solution

    def getCalib(self):
        if self.calibration:
          return self.calibration
        else:
          self.logger.error('Nova Astrometry Service: No actual calibration')
          return {'parity': 0.0, 'orientation': 0.0, 'pixscale': 0.0,
            'radius': 0.0, 'ra': 0.0, 'dec': 0.0}

    def sdssPlot(self, outfn, wcsfn, wcsext=0):
        return self.overlayPlot('sdss_image_for_wcs', outfn,
          wcsfn, wcsext)

    def galexPlot(self, outfn, wcsfn, wcsext=0):
        return self.overlayPlot('galex_image_for_wcs', outfn,
            wcsfn, wcsext)

    def getWcs(self):
        if self.solvedId:
            url = self.apiURL.replace('/api/', '/wcs_file/%i' % self.solvedId)
            return urllib.request.urlopen(url).read()
        else:
            self.logger.error('Nova Astrometry Service: can\'t get wcs, need to '+\
              'obtain solvedId from solveImage first')
            return None

    def getKml(self):
        if self.solvedId:
          url = self.apiURL.replace('/api/', '/kml_file/%i/' % self.solvedId)
          return urllib.request.urlopen(url).read()
        else:
          self.logger.error('Nova Astrometry Service: can\'t get kml, need to '+\
            'obtain solvedId from solveImage first')
          return None

    def getNewFits(self):
        if self.solvedId:
          url = self.apiURL.replace('/api/', '/new_fits_file/%i/' % self.solvedId)
          return fits.open(io.BytesIO(urllib.request.urlopen(url).read()))
        else:
          self.logger.error('Nova Astrometry Service: can\'t get new fit, need '+\
            'to obtain solvedId from solveImage first')
          return None

    def printRaDecWCSwithSIPCorrectedImage(self, savepath):
        '''
          see http://docs.astropy.org/en/stable/wcs/ for more
        '''
        fitsWithSIP = self.getNewFits()
        if fitsWithSIP is not None:
          # Getting Data
          header, im = fitsWithSIP[0].header, fitsWithSIP[0].data
          w = wcs.WCS(header) 
          # Making Indices
          xpx = np.arange(im.shape[1]+1)-0.5
          ypx = np.arange(im.shape[0]+1)-0.5
          xlist, ylist = np.meshgrid(xpx, ypx)
          ralist, declist = w.all_pix2world(xlist, ylist, 0)
          # Resampling to corrected grid
          plt.title('Field center: Ra:'+format(header['CRVAL1'],'.3f')+' , Dec: '+\
                    format(header['CRVAL2'],'.3f'))
          plt.xlabel('Ra axis (deg)')
          plt.ylabel('Dec axis (deg)')
          plt.pcolormesh(ralist,declist, im, vmin=im.min(), vmax=im.max())
          plt.savefig(savepath)
          self.logger.info('Nova Astrometry Service: writing ra/dec tagged image '\
            'to '+savepath)
        else:
          self.logger.error('Nova Astrometry Service: can\'t get new fit, need '+\
            'to obtain solvedId from solveImage first')

    def getSIPCorrectedImage(self):
        '''
          see http://docs.astropy.org/en/stable/wcs/ for more
        '''
        fitsWithSIP = self.getNewFits()
        if fitsWithSIP is not None:
          # Getting Data
          header, im = fitsWithSIP[0].header, fitsWithSIP[0].data
          w = wcs.WCS(header) 
          # Making Indices
          xpx = np.arange(im.shape[1])+0.5
          ypx = np.arange(im.shape[0])+0.5
          refx, refy = np.meshgrid(xpx, ypx)
          x_correction, y_correction = w.sip_pix2foc(refx, refy, 0)
          newx = refx + x_correction
          newy = refy + y_correction
          # Resampling to corrected grid
          corrected=griddata((refx.flatten(),refy.flatten()), im.flatten(),
            (newx,newy), method='cubic')
          self.logger.info('Nova Astrometry Service: Corrected for SIP')
          return None
        else:
          self.logger.error('Nova Astrometry Service: can\'t get new fit, need '+\
            'to obtain solvedId from solveImage first')
          return None
      


    def annotateData(self,job_id):
        """
          :param job_id: id of job
          :return: return data for annotations
        """
        result = self.sendRequest('jobs/%s/annotations' % job_id)
        return result

    def sendRequest(self, service, args={}, fileArgs=None):
        '''
          service: string
          args: dict
          fileArgs: tuple with filename, data
        '''
        if self.session is not None:
          args['session']=self.session
        argJson = json.dumps(args)
        url = self.getAPIUrl(service)
        self.logger.debug('Nova Astrometry Service, sending json: '+str(argJson)+\
          ' to url: '+str(url))

        # If we're sending a file, format a multipart/form-data
        if fileArgs is not None:
          m1 = MIMEBase('text', 'plain')
          m1.add_header('Content-disposition', 'form-data; name="request-json"')
          m1.set_payload(argJson)

          m2 = MIMEApplication(fileArgs,'octet-stream',encode_noop)
          m2.add_header('Content-disposition',
                        'form-data; name="file"; filename="frame.fits"')
          mp = MIMEMultipart('form-data', None, [m1, m2])

          # Make a custom generator to format it the way we need.
          class MyGenerator(BytesGenerator):
            def __init__(self, fp, root=True):
              Generator.__init__(self, fp, mangle_from_=False, maxheaderlen=0)
              self.root = root
            def _write_headers(self, msg):
              # We don't want to write the top-level headers;
              # they go into Request(headers) instead.
              if self.root:
                return
              # We need to use \r\n line-terminator, but Generator
              # doesn't provide the flexibility to override, so we
              # have to copy-n-paste-n-modify.
              for h, v in msg.items():
                  self._fp.write(('%s: %s\r\n' % (h,v)).encode())
              # A blank line always separates headers from body
              self._fp.write('\r\n'.encode())

            # The _write_multipart method calls "clone" for the
            # subparts.  We hijack that, setting root=False
            def clone(self, fp):
              return MyGenerator(fp, root=False)

          fp = BytesIO()
          g = MyGenerator(fp)
          g.flatten(mp)
          data = fp.getvalue()
          headers = {'Content-type': mp['Content-type']}
          self.logger.debug('Nova Astrometry Service, sending binary file data'+\
            ' with headers: '+str(headers))
        else:
          # Else send x-www-form-encoded
          data = {'request-json': argJson}
          self.logger.debug('Nova Astrometry Service, sending text only data:'+\
            ' ,json version : '+str(argJson))
          data = urllib.parse.urlencode(data).encode("utf-8")
          self.logger.debug('Nova Astrometry Service, sending text only data:'+\
            ' ,encoded version : '+str(data))
          headers = {}


        try:
          req = urllib.request.Request(url=url, headers=headers, data=data)
          with urllib.request.urlopen(req) as response:
            txt = response.read()
            self.logger.debug('Nova Astrometry Service, got response: '+str(txt))
            result = json.loads(txt)
            stat = result.get('status')
            if stat == 'error':
              errstr = result.get('errormessage', '(none)')
              self.logger.error('Nova Astrometry Service error message: ' + errstr)
            return result
        except urllib.error.HTTPError as e:
          self.logger.error('Nova Astrometry Service, HTTPError: '+str(e))
          txt = e.read()
          with open('err.html', 'wb') as fout:
            fout.write(txt)
          self.logger.error('Nova Astrometry Service, Wrote error text to err.html')
          return None
        except Exception  as e:
          self.logger.error('Nova Astrometry Service, Error in sendRequest: '+\
            str(e))
          return None
