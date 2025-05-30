# Basic stuff
import logging
import logging.config
import threading
import time

# Miscellaneous
import io
from astropy.io import fits

# Local stuff : Observatory
from Observatory.VirtualObservatory import VirtualObservatory
from Observatory.Observatory import Observatory

# Local stuff : Service
from Service.WUGWeatherService import WUGWeatherService
from Service.NTPTimeService import NTPTimeService
from Service.NovaAstrometryService import NovaAstrometryService

# Local stuff : IndiClient
from helper.IndiClient import IndiClient
from helper.IndiDevice import IndiDevice

# Local stuff : Camera
from Camera.IndiVirtualCamera import IndiVirtualCamera
from Camera.IndiEos350DCamera import IndiEos350DCamera

# Local stuff : FilterWheel
from FilterWheel.IndiFilterWheel import IndiFilterWheel

# Local stuff : Mount
from Mount.IndiMount import IndiMount

# Local stuff : Imaging tools
from Imaging.AsyncWriter import AsyncWriter
from Imaging.FitsWriter import FitsWriter

# Local stuff: Sequencer
from Sequencer.ShootingSequence import ShootingSequence
from Sequencer.SequenceBuilder import SequenceBuilder
from Sequencer.AutoDarkStep import AutoDarkCalculator, AutoDarkSequence

# Target list
from ObservationPlanner.ObservationPlanner import ObservationPlanner

if __name__ == '__main__':

    # load the logging configuration
    logging.config.fileConfig('logging.ini')
    logger = logging.getLogger('mainLogger')

    # Instanciate object of interest
    obs = Observatory()

    #test ntp time server
    servTime = NTPTimeService()
    ntpTime = servTime.get_utc()
    #print('Current Time from NTP is : {}'.format(ntpTime))

    # test Weather service
    servWeather = WUGWeatherService()
    servWeather.setgps_coordinates(obs.get_gps_coordinates())
    #servWeather.printEverything()
    #print('Temperature is ',str(servWeather.getTemp_c()))
    #print('relative humidity is ',str(servWeather.getRelative_humidity()))
    #print('Wind is ',str(servWeather.getWind_kph()))
    #print('Wind gust is',str(servWeather.getWind_gust_kph()))
    #print('Pressure is ',str(servWeather.getPressure_mb()))
    #print('dewpoint is ',str(servWeather.getDewpoint_c()))
    #print('visibility is ',str(servWeather.getVisibility_km()))
    #print('Weather quality is ',str(servWeather.getWeatherQuality()))

    # ObservationPlanner
    obsPlanner = ObservationPlanner( ntpServ=servTime, obs=obs)

    # test indi client
    indiCli = IndiClient()
    indiCli.connect()

    # test indi Device
    indiDevice = IndiDevice(device_name='CCD Simulator',\
        indi_client=indiCli)

    # test indi virtual camera class
    cam = IndiVirtualCamera( indi_client=indiCli,\
        configFileName=None, connect_on_create=False)

    # test indi camera class on a old EOS350D
    #cam = IndiEos350DCamera( indi_client=indiCli,\
    #  configFileName='IndiEos350DCamera.json', connect_on_create=False)

    cam.connect()
    cam.prepare_shoot()
    cam.setExpTimeSec(10)
    #cam.shoot_async()
    #cam.synchronize_with_image_reception()
    #fits = cam.get_received_image()

    # Now test filterWheel
    filterWheel = IndiFilterWheel( indi_client=indiCli,
                                  configFileName=None,
                                  connect_on_create=True)
    filterWheel.initFilterWheelConfiguration()
    print('Filterwheel is {}'.format(filterWheel))

    # Now test Mount
    mount = IndiMount( indi_client=indiCli,
                      configFileName=None, connect_on_create=True)

    # test nova Astrometry service
    #nova = NovaAstrometryService(configFileName='local')
    #nova.login()
    #t=io.BytesIO()
    #fits.writeto(t)
    #astrometry = nova.solveImage(t.getvalue())
    #corrected = nova.getNewFits()
    #print('fits content is '+str(corrected))
    #wcs=nova.getWcs()
    #print('wcs content is '+str(wcs))
    #kml=nova.getKml()
    #print('kml content is '+str(kml))
    #nova.printRaDecWCSwithSIPCorrectedImage('radec.png')

    # Write fits file with all interesting metadata:
    #writer = FitsWriter( observatory=obs, servWeather=servWeather,
    #  servSun=servSun, servMoon=servMoon, servTime=servTime,
    #  servAstrometry=nova)
    writer = FitsWriter( observatory=obs, filterWheel=filterWheel)
   
    #Basic way to define async writing
    #hwriter = lambda f,i : writer.writeWithTag(f,i)
    #w = threading.Thread(target=hwriter, args=(fits,0))
    #w.start()

    #Second way to define async writing
    aWriter = AsyncWriter(writer)

    #Define an autoDarkCalculator
    autoDark = AutoDarkCalculator()

    # Test a Shooting Sequence
    #seq = ShootingSequence( camera=cam, target='M51', exposure=1,
    #    count=5,
    #    onStarted=[lambda x : print('On Started')],
    #    onEachStarted=[lambda x,i : print('On Each Started')],
    #    onEachFinished=[lambda x,i : print('On Each Finished'),
    #                    aWriter.AsyncWriteImage,
    #                    autoDark.onEachFinished],
    #    onFinished=[lambda x : print('On Finished'),])
    #seq.run()

    # Test a Dark sequence
    #darkSeq = AutoDarkSequence( camera=cam,
    #                           autoDarkCalculator=autoDark, count=5,
    #                           onEachFinished=[aWriter.AsyncWriteImage])
    #darkSeq.run()

    # More basic shooting sequence
    #seq2 = ShootingSequence( camera=cam, target='M51',
    #                        exposure=1,
    #    count=5,onEachFinished=[aWriter.AsyncWriteImage])

    # Sequence Builder
    seqB = SequenceBuilder( camera=cam, filterWheel=filterWheel,
                           observatory=obs, mount=mount, asyncWriter=aWriter,
                           useAutoDark=True, useAutoFlat=True)

    #seqB.addUserConfirmationPrompt('Please press enter if you wish to proceed')
    #Red Green Blue Luminance LPR OIII SII H_Alpha
    #seqB.add_filterwheel_step(filterName='Luminance')
    #seqB.add_shooting_sequence(target='M51', exposure=2, count=5)
    #seqB.add_filterwheel_step(filterName='H_Alpha')
    #seqB.add_shooting_sequence(target='M51', exposure=2, count=5)
    #seqB.add_message_print(message='Add Message')
    #seqB.add_shell_command(command='ls')
    #seqB.add_function(lambda : print("Add Function Step"))
    #seqB.add_auto_dark(count=5)
    #seqB.add_auto_flat(count=5, exposure=1)
    #seqB.start()

    #Sequence Builder along with target list, dark calculator, ...

    for target, config in obsPlanner.getTargetList().items():
        for filter_name, (count, expTimeSec) in config.items():
            seqB.add_message_print(message='Target {}, setting filter '
                                   '{}'.format(target,filter_name))
            seqB.add_filterwheel_step(filterName=filter_name)
            seq_name = target+'-'+filter_name
            seqB.add_object_shooting_sequence(target, seq_name=seq_name,
                                              exposure=expTimeSec, count=count)
    seqB.add_auto_dark(count=5)
    seqB.add_auto_flat(count=5, exposure=1)
    seqB.start()

