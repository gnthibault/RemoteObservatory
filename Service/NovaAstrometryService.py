#Basic stuff
import json
import logging
from pathlib import Path

#webservice stuff

# Forging request
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.application  import MIMEApplication
from email.encoders import encode_noop

class NovaAstrometryService(object):
  """ Nova Astrometry Service """
  # API request engine
  defaultAPIURL = 'http://nova.astrometry.net/api/'

  def __init__(self, configFileName=None, logger=None, apiURL=defaultAPIURL):
    self.logger = logger or logging.getLogger(__name__)

    if configFileName is None:
      # Default file is ~/.nova.json
      home = Path.home()
      config = home / '.nova.json'
      self.configFileName = str(config)
    else:
      self.configFileName = configFileName

    # Now configuring
    self.logger.debug('Configuring Nova Astrometry Service with file %s',\
      self.configFileName)

    # Get key from json
    with open(self.configFileName) as jsonFile:  
      data = json.load(jsonFile)
      self.key = data['key']

    # Api URL
    self.apiURL=apiURL
    # Manage persistent session with cookie like ID
    self.session = None

    # Finished configuring
    self.logger.debug('Configured Nova Astrometry service successfully')

  def getAPIUrl(self, service):
    return self.apiURL + service

  def login(self):
    args = { 'apikey' : self.key }
    result = self.sendRequest('login', args)
    session = result.get('session')
    logger.debug('Nova Astrometry Service: Got session ', sess)
    if not sess:
      self.logger.error('Nova Astrometry Service: No session in result')
    self.session = session

  def sendRequest(self, service, args={}, fileArgs=None):
    '''
      service: string
      args: dict
      fileArgs: tuple with filename, data
    '''
    if self.session is not None:
      args['session']=self.session
    json = json.dumps(args)
    url = self.getAPIUrl(service)

    # If we're sending a file, format a multipart/form-data
    if fileArgs is not None:
      m1 = MIMEBase('text', 'plain')
      m1.add_header('Content-disposition', 'form-data; name="request-json"')
      m1.set_payload(json.dumps(args))

      m2 = MIMEApplication(fileArgs[1],'octet-stream',encode_noop)
      m2.add_header('Content-disposition',
                    'form-data; name="file"; filename="%s"' % fileArgs[0])
      mp = MIMEMultipart('form-data', None, [m1, m2])

      # Make a custom generator to format it the way we need.
      from cStringIO import StringIO
      from email.generator import Generator

      class MyGenerator(Generator):
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
            print(('%s: %s\r\n' % (h,v)), end='', file=self._fp)
          # A blank line always separates headers from body
            print('\r\n', end='', file=self._fp)

        # The _write_multipart method calls "clone" for the
        # subparts.  We hijack that, setting root=False
        def clone(self, fp):
          return MyGenerator(fp, root=False)

      fp = StringIO()
      g = MyGenerator(fp)
      g.flatten(mp)
      data = fp.getvalue()
      headers = {'Content-type': mp.get('Content-type')}
      self.logger.debug('Nova Astrometry Service, sending binary file data:')
 
    else:
      # Else send x-www-form-encoded
      data = {'request-json': json}
      data = urlencode(data)
      self.logger.debug('Nova Astrometry Service, sending text only data:'+\
        str(data)+' ,json version : '+str(json))
      headers = {}

    request = Request(url=url, headers=headers, data=data)

    try:
        f = urlopen(request)
        txt = f.read()
        self.logger.debug('Nova Astrometry Service, Got json:', txt)
        result = json2python(txt)
        self.logger.debug('Nova Astrometry Service, Got result:', result)
        stat = result.get('status')
        self.logger.debug('Nova Astrometry Service, Got status:', stat)
        if stat == 'error':
            errstr = result.get('errormessage', '(none)')
            raise RequestError('server error message: ' + errstr)
        return result
    except HTTPError as e:
        self.logger.debug('Nova Astrometry Service, HTTPError', e)
        txt = e.read()
        open('err.html', 'wb').write(txt)
        self.logger.debug('Nova Astrometry Service, Wrote error text to err.html')

  def _getUploadArgs(self, **kwargs):
    args = {}
    for key,default,typ in [('allow_commercial_use', 'd', str),
        ('allow_modifications', 'd', str),
        ('publicly_visible', 'y', str),
        ('scale_units', None, str),
        ('scale_type', None, str),
        ('scale_lower', None, float),
        ('scale_upper', None, float),
        ('scale_est', None, float),
        ('scale_err', None, float),
        ('center_ra', None, float),
        ('center_dec', None, float),
        ('radius', None, float),
        ('downsample_factor', None, int),
        ('tweak_order', None, int),
        ('crpix_center', None, bool),
        ('x', None, list),
        ('y', None, list)]:
        # image_width, image_height
      if key in kwargs:
        val = kwargs.pop(key)
        val = typ(val)
        args.update({key: val})
      elif default is not None:
        args.update({key: default})
    self.logger.debug('Nova Astrometry service: upload args are:', args)
    return args

    def urlUpload(self, url, **kwargs):
      args = dict(url=url)
      args.update(self._getUploadArgs(**kwargs))
      result = self.sendRequest('url_upload', args)
      return result

    def upload(self, fn=None, **kwargs):
      args = self._getUploadArgs(**kwargs)
      fileArgs = None
      if fn is not None:
        try:
          f = open(fn, 'rb')
          fileArgs = (fn, f.read())
        except IOError:
          self.logger.error('Nova Astrometry Service, File '+str(fn)+\
            ' does not exist')
          raise
        return self.sendRequest('upload', args, fileArgs)

    def submission_images(self, subid):
      result = self.sendRequest('submission_images', {'subid':subid})
      return result.get('image_ids')

    def overlay_plot(self, service, outfn, wcsfn, wcsext=0):
      from astrometry.util import util as anutil
      wcs = anutil.Tan(wcsfn, wcsext)
      params = dict(crval1 = wcs.crval[0], crval2 = wcs.crval[1],
        crpix1 = wcs.crpix[0], crpix2 = wcs.crpix[1],
        cd11 = wcs.cd[0], cd12 = wcs.cd[1],
        cd21 = wcs.cd[2], cd22 = wcs.cd[3],
        imagew = wcs.imagew, imageh = wcs.imageh)
      result = self.sendRequest(service, {'wcs':params})
      self.logger.debug('Nova Astrometry Service, Result status:',\
        result['status'])
      plotdata = result['plot']
      plotdata = base64.b64decode(plotdata)
      open(outfn, 'wb').write(plotdata)
      self.logger.debug('Nova Astrometry Service, Wrote', outfn)

    def sdss_plot(self, outfn, wcsfn, wcsext=0):
      return self.overlay_plot('sdss_image_for_wcs', outfn,
                                 wcsfn, wcsext)

    def galex_plot(self, outfn, wcsfn, wcsext=0):
      return self.overlay_plot('galex_image_for_wcs', outfn,
        wcsfn, wcsext)

    def myjobs(self):
      result = self.sendRequest('myjobs/')
      return result['jobs']

    def job_status(self, job_id, justdict=False):
      result = self.sendRequest('jobs/%s' % job_id)
      if justdict:
        return result
      stat = result.get('status')
      if stat == 'success':
        result = self.sendRequest('jobs/%s/calibration' % job_id)
        self.logger.debug('Nova Astrometry Service, Calibration result:',
          result)
        result = self.sendRequest('jobs/%s/tags' % job_id)
        self.logger.debug('Nova Astrometry Service, Tags:', result)
        result = self.sendRequest('jobs/%s/machine_tags' % job_id)
        self.logger.debug('Nova Astrometry Service, Machine Tags:', result)
        result = self.sendRequest('jobs/%s/objects_in_field' % job_id)
        self.logger.debug('Nova Astrometry Service, Objects in field:', result)
        result = self.sendRequest('jobs/%s/annotations' % job_id)
        self.logger.debug('Nova Astrometry Service, Annotations:', result)
        result = self.sendRequest('jobs/%s/info' % job_id)
        self.logger.debug('Nova Astrometry Service, Calibration:', result)
      return stat

    def annotateData(self,job_id):
      """
        :param job_id: id of job
        :return: return data for annotations
       """
      result = self.sendRequest('jobs/%s/annotations' % job_id)
      return result

    def sub_status(self, sub_id, justdict=False):
      result = self.sendRequest('submissions/%s' % sub_id)
      if justdict:
        return result
      return result.get('status')

    def jobs_by_tag(self, tag, exact):
      exact_option = 'exact=yes' if exact else ''
      result = self.sendRequest(
        'jobs_by_tag?query=%s&%s' % (quote(tag.strip()), exact_option),{}, )
      return result


