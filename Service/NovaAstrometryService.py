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
    self.apiURL=apiRUL
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

    else:
      # Else send x-www-form-encoded
      data = {'request-json': json}
      print('Sending form data:', data)
      data = urlencode(data)
      print('Sending data:', data)
      headers = {}

    request = Request(url=url, headers=headers, data=data)

    try:
        f = urlopen(request)
        txt = f.read()
        print('Got json:', txt)
        result = json2python(txt)
        print('Got result:', result)
        stat = result.get('status')
        print('Got status:', stat)
        if stat == 'error':
            errstr = result.get('errormessage', '(none)')
            raise RequestError('server error message: ' + errstr)
        return result
    except HTTPError as e:
        print('HTTPError', e)
        txt = e.read()
        open('err.html', 'wb').write(txt)
        print('Wrote error text to err.html')

