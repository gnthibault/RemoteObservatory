# Generic stuff
import logging
import os
import time
import traceback
import yaml

# FSM stuff
import pygraphviz
from transitions import State
from transitions.extensions import GraphMachine as Machine

# Local stuff
from Base.Base import Base
from utils import listify
from utils import load_module

class StateMachine(Machine, Base):
    """ A finite state machine class initially written by PANOPTES project
    members, the state machine guides the overall action of the unit.

    Why don't we use a separate model class to store the logic, but instead put
    everything into the statemachine ? Here is the answer in the relevant part
    of the documentation:

    Alternative initialization patterns
    In all of the examples so far, we've attached a new Machine instance to a
    separate model ( lump , an instance of class Matter ). While this
    separation keeps things tidy (because you don't have to monkey patch a
    whole bunch of new methods into the Matter class), it can also get annoying
    , since it requires you to keep track of which methods are called on the
    state machine, and which ones are called on the model that the state
    machine is bound to (e.g., lump.on_enter_StateA() vs.
                               machine.add_transition() ).
    Fortunately, Transitions is flexible, and supports two other initialization
    patterns.
    First, you can create a standalone state machine that doesn't require
    another model at all. Simply omit the model argument during initialization:

    machine = Machine(states=states, transitions=transitions, initial='solid')
    machine.melt()
    machine.state
    > liquid
    If you initialize the machine this way, you can then attach all triggering
    events (like evaporate() , sublimate() , etc.) and all callback functions
    directly to the Machine instance.
    This approach has the benefit of consolidating all of the state machine
    functionality in one place, but can feel a little bit unnatural if you
    think state logic should be contained within the model itself rather than
    in a separate controller.
    An alternative (potentially better) approach is to have the model inherit
    from the Machine class. Transitions is designed to support inheritance
    seamlessly. (just be sure to override class Machine 's __init__ method!)


    Here is a list of useful attributes / method that can be used in a derived
    class. along with some comments:

    ####### Control flow attributes #######
    self._connected: used in inherited, set to True in inherited __init__
        is called. It is actually the value returned by overriden connected()
        method. Set to false in inherited.power_down
    self.connected: @property defined in inherited, actually returns _connected
    self._initialized: used in inherited, set to False when inherited __init__
        is called. Set to tru in inherited.initialize. returned by overriden 
        property is_initialized in inherited. Set to False in
        inherited.power_down
    self._keep_running: used in inherited. Initialized to False in
        StateMachine.__init__, but initialized to True in
        inherited.__init__. Eventually set to false in inherited.power_down
    self._do_states: used in both StateMachine and inherited. Initialized to
        True in StateMachine.__init__, eventually set to
             -False in inherited.power_down.
             -True in StateMachine.__init__.
             -True in StateMachine.run
             -False in StateMachine.stop_states
        Mainly used in StateMachine, where it is initialize
    self.do_state: @property defined in StateMachine, simply returne _do_state
    self._retry_attempts: used in inherited, default retry number of retry, set
        to 3 by default in inherited.
    self._obs_run_retries: used in inherited, initialized at
        self._retry_attempts, whenever reset_observation_run is called.
        In the main run loop in StateMachine, this counter is decremented
        whenever an "Attempt" of the main FSM loop has run, most likely
        because of an exception somwhere in the state/trnsition
    self._interrupted: used in inherited. Initialized to False when inherited 
        __init__ is called. Set to true if _interrupt_and_park or
        _interrupt_and_shutdown is called. It is actually the value returned
        by overriden @interrupted property is called
    self.interrupted: @property defined in inherited, actually returns
        _interrupted. used in the following states:
        observing state:
        pointing state:

    ####### State/safety/info related attributes #######
    self._is_safe:
    self.state: mainly used in stateMachine, but also used in inherited
    self._next_state: mainly used in StateMachine 
    self.run_once: used in StateMachine.run (not used anymore)
        also used in:
        scheduling state: if run_once, then go park directly, do not check for
                          other possible observation (tracking if same of slew-
                          ing if another target is the next observation)
        parked state: if no valid observation and run_once, it means that
                      the run already took place, and that no additional check
                      for wake up should be performed.
    self.force_reschedule = used in inherited, initialized to False in
        inherited constructor. Might be used for instance if an error/data
        quality requirement is not met during the previous observation
        acquisition. Then we might force to reschedule. This value is for
        instance checked inside of the analyzing state.
    self.should_retry: @property that returns wether the self_obs_run_retries
        counter is >=0 or not. defined in inherited.
        used in states:
        -parked: like run_once, if should not retry, but observation list was 
                 not void, then go to housekeeping before sleeping
        -sleeping: if False, it means that something must have gone wrong, so
                   instead of going back to ready state after resetting the
                   observing run, and waiting for a timed transition
                   just triggers the stop_state method


    ####### Control flow method not related to state #######
    self.reset_observation_run: Defined in inherited, just reset
        the _obs_run_retry attribute to its default value: self._retry_attempts




    """

    def __init__(self, state_machine_table, **kwargs):

        Base.__init__(self)
        if isinstance(state_machine_table, str):
            self.logger.info("Loading state table: {}".format(
                state_machine_table))
            state_machine_table = StateMachine.load_state_table(
                state_table_name=state_machine_table)

        assert 'states' in state_machine_table, self.logger.warning(
            'states keyword required.')
        assert 'transitions' in state_machine_table, self.logger.warning(
            'transitions keyword required.')

        self._state_table_name = state_machine_table.get('name',
                                                         'default_name')
        self._states_location = state_machine_table.get('location',
                                                        'StateMachine/States')

        # Load transitions from config file
        transitions_list = [self._load_and_customize_transition(transition)
                           for transition in state_machine_table['transitions']]
        # Load states from config file
        states_list = [self._load_state(state) for state in
                       state_machine_table.get('states', [])]
        self.logger.debug('List of states loaded from {}: {}'.format(
                          state_machine_table, states_list))

        # About the send_event option: If you set send_event=True at Machine
        #initialization, all arguments to the triggers will be wrapped in an 
        #EventData instance and passed on to every callback. (The EventData
        #object also maintains internal references to the source state, model,
        #transition, machine, and trigger associated with the event, in case
        #you need to access these for anything.)
        # The auto_transitions=False disable automatic addition of
        #to_<statename> method to the machine/model, that otherwise would allow
        #to go from any other state to <statename> upon triggering
        super(StateMachine, self).__init__(
            states=states_list,
            transitions=transitions_list,
            initial=state_machine_table.get('initial'),
            send_event=True,
            before_state_change='before_state',
            after_state_change='after_state',
            auto_transitions=False,
            name="Remote Observatory State Machine"
        )

        self._state_machine_table = state_machine_table
        self._next_state = None
        self._keep_running = False
        self._do_states = True

        self.logger.debug("State machine created")

###############################################################################
# Properties
###############################################################################

    @property
    def keep_running(self):
        return self._keep_running

    @property
    def do_states(self):
        return self._do_states

    @property
    def next_state(self):
        return self._next_state

    @next_state.setter
    def next_state(self, value):
        self._next_state = value

###############################################################################
# Properties to be overriden
###############################################################################

    @property
    def is_initialized(self):
        """ Indicates if remote observatory has been initalized or not """
        raise NotImplemented

    @property
    def interrupted(self):
        """If remote observatory has been interrupted

        Returns:
            bool: If an interrupt signal has been received
        """
        raise NotImplemented

    @property
    def connected(self):
        """ Indicates if remote observatory is connected """
        raise NotImplemented

###############################################################################
# Methods
###############################################################################

    def run(self, exit_when_done=False):
        """Runs the state machine loop

        This runs the state machine in a loop. Setting the machine property
        `is_running` to False will stop the loop.


        One might ask, but who is deciding the "scheduling", who performs the
        triggers, and who decides of what should be the next_state attribute ?
        -The run method here decide of the main "scheduling loop".
        -Basic schedule may be modified upon receipt of a zmq message if
         core does feature a messaging service (has_messaging)
        -But most of the logic is contained inside of the body of the on_enter
         function defined in each state module in StateMachine/States
         Those functions are defined the behaviour of the state, but more 
         importantly of next_state. See StateMachine/States/ready.py for a
         good example

         Are some services running asynchronously, like weather checking ?
         TODO TN: answer this question

        Args:
            exit_when_done (bool, optional): If True, the loop will exit when
                `do_states` has become False, otherwise will sleep (default)

            run_once (bool, optional): If the machine loop should only run one
                time, defaults to False to loop continuously. after run
                don't do state anymore but still read messages
        """
        assert self.is_initialized, self.logger.error("not initialized")

        self._keep_running = True
        self._do_states = True

        # Start with `get_ready`
        self.next_state = 'ready'

        _loop_iteration = 0

        while self.keep_running and self.connected:
            state_changed = False

            self.check_messages()

            # If we are processing the states
            if self.do_states:

                # If sleeping, wait until safe (or interrupt)
                if self.state == 'sleeping':
                    if self.is_safe() is not True:
                        self.wait_until_safe()
                try:
                    state_changed = self.goto_next_state()
                except Exception as e:
                    self.logger.warning('Problem going from {} to {}, exiting '
                        'loop: {}:{}'.format(self.state, self.next_state, e,
                        traceback.format_exc()))
                    self.stop_states()
                    #TODO TN URGENT DO SOME INTERNAL SIGNALING HERE !
                    break

                # If we didn't successfully transition, sleep a while then try
                # again
                if not state_changed:
                    if _loop_iteration > 5:
                        self.logger.warning('Stuck in current state for 5 '
                                            'iterations, parking')
                        self.next_state = 'parking'
                    else:
                        _loop_iteration = _loop_iteration + 1
                        self.sleep(with_status=False)
                else:
                    _loop_iteration = 0

                ########################################################
                # Note that `self.state` below has changed from above
                ########################################################

                # If we are in ready state then we are making one attempt
                if self.state == 'ready':
                    self._obs_run_retries -= 1

            elif exit_when_done:
                break
            elif not self.interrupted:
                # Sleep for one minute (can be interrupted via `check_messages`)
                self.sleep(60)

    def goto_next_state(self):
        state_changed = False

        # Get the next transition method based on `state` and `next_state`
        call_method = self._lookup_trigger()

        self.logger.debug("Transition method: {}".format(call_method))
        caller = getattr(self, call_method, self.park)
        state_changed = caller()
        self.db.insert_current('state', {"source": self.state,
                                         "dest": self.next_state})

        return state_changed

    def stop_states(self):
        """ Stops the machine loop on the next iteration """
        self.logger.info("Stopping states")
        self._do_states = False

###############################################################################
# Methods to be overriden
###############################################################################
    def status(self):
        """Computes status, a dict, of whole observatory."""
        return NotImplemented

    def wait_until_safe(self):
        """ Waits until all safety flags are set 
        """
        while not self.is_safe(no_warning=True):
            self.sleep(30)

    def sleep(self, delay=2.5, with_status=True):
        time.sleep(delay)

    def check_messages(self):
        """
            In charge of monitoring external order/commands
        """
        pass
###############################################################################
# State Conditions
###############################################################################

    def check_safety(self, event_data=None):
        """ Checks the safety flag of the system to determine if safe.

        This will check the weather station as well as various other
        environmental aspects of the system in order to determine if conditions
        are safe for operation.

        Note:
            This condition is called by the state machine during each transition

        Args:
            event_data(transitions.EventData): carries information about the
            event if called from the state machine.

        Returns:
            bool:   Latest safety flag
        """

        self.logger.debug("Checking safety for {}".format(
                          event_data.event.name))

        # It's always safe to be in some states
        if event_data and event_data.event.name in [
                'park', 'set_park', 'clean_up', 'goto_sleep', 'get_ready']:
            self.logger.debug("Always safe to move to {}".format(
                              event_data.event.name))
            is_safe = True
        else:
            is_safe = self.is_safe()

        return is_safe

    def mount_is_tracking(self, event_data):
        """ Transitional check for mount.

        This is used as a conditional check when transitioning between certain
        states.
        """
        return self.manager.mount.is_tracking

    def mount_is_initialized(self, event_data):
        """ Transitional check for mount.

        This is used as a conditional check when transitioning between certain
        states.
        """
        return self.manager.mount.is_initialized

###############################################################################
# Callback Methods
###############################################################################

    def before_state(self, event_data):
        """ Called before each state.

        Starts collecting stats on this particular state, which are saved during
        the call to `after_state`.

        Args:
            event_data(transitions.EventData):  Contains informaton about the
                event
         """
        self.logger.debug(
            "Before calling {} from {} state".format(event_data.event.name,
                                                     event_data.state.name))

    def after_state(self, event_data):
        """ Called after each state.

        Updates the mongodb collection for state stats.

        Args:
            event_data(transitions.EventData):  Contains informaton about the
                event
        """

        self.logger.debug(
            "After calling {}. Now in {} state".format(event_data.event.name,
                                                       event_data.state.name))


###############################################################################
# Class Methods
###############################################################################

    @classmethod
    def load_state_table(cls, state_table_name='simple_state_table'):
        """ Loads the state table

        Args:
            state_table_name(str):  Name of state table. Corresponds to file
                name in  directory or to absolute path if
                starts with "/". Default 'simple_state_table'.

        Returns:
            dict:   Dictionary with `states` and `transitions` keys.
        """

        state_table_file = state_table_name
        state_table = {'states': [], 'transitions': []}

        try:
            with open(state_table_file, 'r') as f:
                state_table = yaml.load(f.read())
        except Exception as err:
            raise RuntimeError('Problem loading state table yaml file: '
                                '{} {}'.format(err, state_table_file))

        return state_table

################################################################################
# Private Methods
################################################################################

    def _lookup_trigger(self):
        """ returns name of trigger method based on state and next_state

        """
        self.logger.debug("Source: {}\t Dest: {}".format(self.state,
                          self.next_state))
        if self.state == 'parking' and self.next_state == 'parking':
            return 'set_park'
        else:
            for state_info in self._state_machine_table['transitions']:
                if self.state in state_info['source'] and (state_info['dest']
                                                           == self.next_state):
                    return state_info['trigger']

        # Return park transition if we don't find existing transition in
        # between self.state and self.next_state. This is a security check
        return 'park'

    def _update_status(self, event_data):
        self.status()

    def _update_graph(self, event_data, ext=['png', 'svg']): # pragma: no cover
        model = event_data.model

        try:
            state_id = 'state_{}_{}'.format(event_data.event.name,
                                            event_data.state.name)

            image_dir = self.config['directories']['images']
            os.makedirs('{}/state_images/'.format(image_dir), exist_ok=True)

            for fext in ext:
                fn = '{}/state_images/{}.{}'.format(image_dir, state_id, fext)
                ln_fn = '{}/state.{}'.format(image_dir, fext)

                # Only make the file once
                if not os.path.exists(fn):
                    model.get_graph().draw(fn, prog='dot')

                # Link current image
                if os.path.exists(ln_fn):
                    os.remove(ln_fn)

                os.symlink(fn, ln_fn)

        except Exception as e:
            self.logger.warning("Can't generate state graph: {}".format(e))

    def _load_state(self, state):
        """
           load and customize the "state" state
           It must be noticed that state_module here DO NOT DEFINE A FULL STATE
           instead, they only define an on_enter function that is supposed to
           be used inside of this (StateMachine) class. When named accordingly
           transition mechanism takes care of call on_enter_<statename> whenever
           the transition to <statename> is triggered

           What we load is actually only a generic state, on which we add some
           callback that will for instance log some data or update the model
           object with informations we need.

           Here is the relevant extract from the documentation:
           A State can also be associated with a list of enter and exit
           callbacks, which are called whenever the state machine enters or
           leaves that state. You can specify callbacks during initialization,
           or add them later.
           For convenience, whenever a new State is added to a Machine , the
           methods on_enter_«state name» and on_exit_«state name» are
           dynamically created on the Machine (not on the model), which allow
           you to dynamically add new enter and exit callbacks later if you
           need them.
        """
        self.logger.debug("Loading state: {}".format(state))
        s = None
        try:
            state_module = load_module('{}.{}'.format(
                self._states_location.replace("/", "."),
                state
            ))
            # Get the `on_enter` method
            self.logger.debug("Checking {}".format(state_module))
            on_enter_method = getattr(state_module, 'on_enter')
            setattr(self, 'on_enter_{}'.format(state), on_enter_method)
            self.logger.debug(
                "Added `on_enter` method from {} {}".format(
                state_module, on_enter_method))

            self.logger.debug("Created state")
            s = State(name=state)
            s.add_callback('enter', '_update_status')
            s.add_callback('enter', '_update_graph')
            s.add_callback('enter', 'on_enter_{}'.format(state))

        except Exception as e:
            raise RuntimeError("Can't load state modules: {}\t{}".format(
                               state, e))

        return s

    def _load_and_customize_transition(self, transition):
        """ Relevant extract from the documentation for conditional transitions:
            Sometimes you only want a particular transition to execute if a
            specific condition occurs. You can do this by passing a method, or
            list of methods, in the conditions argument.
            It should be noticed that the method refers here to model method by
            default, or statemachine in case there is no model.
            Note that condition-checking methods will passively receive optional
            arguments and/or data objects passed to triggering methods. For
            instance, the following call:
           
            statemachine.heatsystem(temp=74)
            # equivalent to statemachine.trigger('heatsystem', temp=74)

            would pass the temp=74 optional kwarg to the is_flammable() check
            (possibly wrapped in an EventData instance).

            Another extract from the documentation:
            You can attach callbacks to transitions as well as states. Every
            transition has 'before' and 'after' attributes that contain
            a list of methods to call before and after the transition executes.
            Those method also refers to model by default, but can be part of
            statemachine if there is no model
        """

        self.logger.debug('Loading transition: {}'.format(transition))

        # Add `check_safety` as the first transition for all states
        conditions = listify(transition.get('conditions', []))
        conditions.insert(0, 'check_safety')
        transition['conditions'] = conditions

        self.logger.debug("Returning transition: {}".format(transition))
        return transition
