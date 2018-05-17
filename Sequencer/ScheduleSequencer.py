# Basic stuff
import logging

# Astropy stuff
import astropy.units as AU

# Local stuff: Sequencer
from Sequencer.SequenceBuilder import SequenceBuilder

class ScheduleSequencer:
    def __init__(self, camera, filter_wheel=None, observatory=None, mount=None,
                 focuser=None, logger=None, async_writer=None,
                 use_auto_dark=True, use_auto_flat=False):
        self.logger = logger or logging.getLogger(__name__)
        self.seq_builder = SequenceBuilder(camera=camera,
                                           filterWheel=filter_wheel,
                                           observatory=observatory,
                                           mount=mount,
                                           asyncWriter=async_writer,
                                           useAutoDark=use_auto_dark,
                                           useAutoFlat=use_auto_flat)

    def build_sequence(self, schedule):

        # Very first job will be to schedule startup routine of all devices
        #TODO TN URGENT: creer un dict de devices et tous les allumer/connecter
        def startup_device(dev):
            dev.indiClient.connect()
            dev.connect()
        
        # Start mount
        self.seq_builder.add_function(
            lambda : startup_device(self.seq_builder.mount))
        # Start camera
        self.seq_builder.add_function(
            lambda : startup_device(self.seq_builder.camera))
        # Start filter_wheel
        self.seq_builder.add_function(
            lambda : startup_device(self.seq_builder.filterWheel))

        # Then specific startup routine #TODO TN ISOLATE THOSE INSIDE CLASS
        self.seq_builder.add_function(
            lambda : self.seq_builder.mount.unPark())
        self.seq_builder.add_function(
            lambda : self.seq_builder.camera.prepareShoot())
        self.seq_builder.add_function(
            lambda : self.seq_builder.filterWheel.\
                     initFilterWheelConfiguration())

        curFilter = None
        for el in schedule.observing_blocks:
            print('Element in schedule: start at {}, target is {}, '
                  'filter is {}, count is {}, and duration is {}'.format(
                  el.start_time, el.target, el.configuration['filter'],
                  el.number_exposures, el.time_per_exposure))

            # deriving filter name and configuration
            filter_name = el.configuration['filter']
            if filter_name != curFilter:
                self.seq_builder.add_message_print(message='Target {}, setting filter '
                    '{}'.format(el.target,filter_name))
                self.seq_builder.add_filterwheel_step(filterName=filter_name)

            # deriving name for target
            if el.target.name is None:
                target_name = ('ra-'+str(el.target.coord.dec)+'_dec-'+
                               str(el.target.coord.dec))
            else:
                target_name = el.target.name
            seq_name = target_name+'-'+filter_name

            # deriving exposure time
            exp_time_sec = int((el.time_per_exposure/AU.s).value)

            # Now add the object shooting step
            self.seq_builder.add_object_shooting_sequence(
                target_name, seq_name=seq_name,
                exposure=exp_time_sec, count=el.number_exposures)

        # End of session, automatically computes count
        self.seq_builder.add_auto_dark(count=None)
        self.seq_builder.add_auto_flat(count=49, exposure=1)

    def start_sequence(self):
        self.seq_builder.start()

