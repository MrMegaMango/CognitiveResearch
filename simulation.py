import simpy

import utilities as utilities
import vision as vision
import chunks as chunks


class Simulation(object):
    """
    ACT-R simulations.
    """

    _UNKNOWN = utilities._UNKNOWN

    def __init__(self, environment, realtime, trace, gui, buffers, used_productions, initial_time=0,
                 environment_process=None, **kwargs):

        self.gui = environment and gui and GUI

        self.__simulation = simpy.Environment(initial_time=round(initial_time, 4))

        self.__env = environment
        if self.__env:
            self.__env.gui = gui and GUI  # set the gui of the environment in the same way as this one; it is used so that Environment prints its output directly in simpy simulation

        self.__realtime = realtime

        if not self.gui and realtime:
            self.__simulation = simpy.RealtimeEnvironment()

        self.__trace = trace

        self.__dict_extra_proc = {key: None for key in buffers}

        self.__buffers = buffers

        self.__pr = used_productions

        self.__simulation.process(self.__procprocessGenerator__())

        self.__interruptibles = {}  # interruptible processes

        self.__dict_extra_proc_activate = {}

        for each in self.__dict_extra_proc:
            if each != self.__pr._PROCEDURAL:
                self.__dict_extra_proc[each] = self.__simulation.process(self.__extraprocessGenerator__(
                    each))  # create simulation processes for all buffers, store them in dict_extra_proc
                self.__dict_extra_proc_activate[
                    each] = self.__simulation.event()  # create simulation events for all buffers that control simulation flow (they work as locks)

        self.__proc_activate = self.__simulation.event()  # special event (lock) for procedural module

        self.__procs_started = []  # list of processes that are started as a result of production rules

        # activate environment process, if environment present
        if self.__env:
            self.__proc_environment = self.__simulation.process(self.__envGenerator__(ep=environment_process, **kwargs))
            self.__environment_activate = self.__simulation.event()

        self.__last_event = None  # used when stepping thru simulation

        # here below -- simulation values, accesible by user
        self.current_event = None
        self.now = self.__simulation.now

    def __activate__(self, event):
        """
        Triggers proc_activate, needed to activate procedural process.
        """
        if event.action != self.__pr._UNKNOWN and event.proc != self.__pr._PROCEDURAL:
            if not self.__proc_activate.triggered:
                self.__proc_activate.succeed()

    def __envGenerator__(self, ep, **kwargs):
        """
        Creates simulation process for process in environment.
        """
        generator = ep(**kwargs)
        event = next(generator)
        while True:
            pro = self.__simulation.process(self.__envprocess__(event))
            yield pro | self.__environment_activate
            if self.__environment_activate.triggered:
                expected, triggered = self.__environment_activate.value
                self.__environment_activate = self.__simulation.event()
                pro.interrupt()
            try:
                event = next(generator)
            except StopIteration:
                break
            # this part below ensures automatic bufferring which proceeds independently of PROCEDURAL
            for name in self.__buffers:
                if isinstance(self.__buffers[name], vision.VisualLocation) and self.__buffers[
                    name].environment == self.__env:
                    proc = (name,
                            self.__pr.automatic_search(name, self.__buffers[name], list(self.__env.stimulus.values()),
                                                       self.__simulation.now))
                    self.__procs_started.append(proc)
                elif isinstance(self.__buffers[name], vision.Visual) and self.__buffers[name].environment == self.__env:
                    try:
                        cf = tuple(self.__buffers[name].current_focus)
                    except AttributeError:
                        pass
                    else:
                        proc = (name, self.__pr.automatic_buffering(name, self.__buffers[name],
                                                                    list(self.__env.stimulus.values()),
                                                                    self.__simulation.now))
                        self.__procs_started.append(proc)
                else:
                    continue
                if not self.__dict_extra_proc_activate[proc[0]].triggered:
                    self.__interruptibles[proc[0]] = proc[
                        1]  # add new process interruptibles if the process can be interrupted according to ACT-R
                    self.__dict_extra_proc_activate[proc[0]].succeed()  # activate modules that are used if not active
                else:
                    if proc[1] != self.__interruptibles[proc[0]]:
                        self.__interruptibles[proc[0]] = proc[1]
                        self.__dict_extra_proc[proc[0]].interrupt()  # otherwise, interrupt them

    def __envprocess__(self, event):
        """
        Runs local environment process.
        """
        try:
            yield self.__simulation.timeout(event.time - self.__simulation.now)
        except simpy.Interrupt:
            pass
        else:
            self.__printenv__(event)
        finally:
            self.__activate__(event)

    def __extraprocessGenerator__(self, name):
        """
        Creates simulation process for other rules.
        """
        while True:
            try:
                _, proc = next(filter(lambda x: x[0] == name, self.__procs_started))
            except StopIteration:
                if name in self.__interruptibles:
                    self.__interruptibles.pop(name)  # remove this process from interruptibles since it's finished
                yield self.__dict_extra_proc_activate[name]
                self.__dict_extra_proc_activate[name] = self.__simulation.event()
            else:
                self.__procs_started.remove((name, proc))
                if not self.__dict_extra_proc_activate[name].triggered:
                    self.__dict_extra_proc_activate[name].succeed()  # activate modules that were used
                pro = self.__simulation.process(self.__localprocess__(name, proc))

                try:
                    cont = yield pro
                except simpy.Interrupt:
                    if not pro.triggered:
                        warnings.warn("Process in %s interupted" % name)
                        pro.interrupt()  # interrupt process

                # if first extra process is followed by another process (returned as cont), do what follows; used only for motor and visual
                else:
                    if cont:
                        pro = self.__simulation.process(self.__localprocess__(name, cont))
                        try:
                            yield pro
                        except simpy.Interrupt:
                            pass

    def __localprocess__(self, name, generator):
        """
        Triggers local process. name is the name of module. generator must only yield Events.
        """
        while True:
            event = next(generator)
            try:
                yield self.__simulation.timeout(event.time - round(self.__simulation.now,
                                                                   4))  # a hack -- rounded because otherwise there was a very tiny negative delay in some cases
            except simpy.Interrupt:
                break
            else:
                self.__printevent__(event)
                self.__activate__(event)
            try:
                if self.__env.trigger in self.__pr.env_interaction:
                    self.__environment_activate.succeed(value=tuple((self.__env.trigger, self.__pr.env_interaction)))
                self.__pr.env_interaction = set()
            except AttributeError:
                pass

    def __printevent__(self, event):
        """
        Stores current event in self.current_event and prints event.
        """
        if event.action != self.__pr._UNKNOWN:
            self.current_event = event
            if self.__trace and not self.gui:
                print(event[0:3])

    def __printenv__(self, event):
        """
        Prints environment event.
        """
        if event.action != self.__pr._UNKNOWN:
            self.current_event = event

    def __procprocessGenerator__(self):
        """
        Creates simulation process for procedural rules.
        """
        pro = self.__simulation.process(self.__localprocess__(self.__pr._PROCEDURAL, self.__pr.procedural_process(
            self.__simulation.now)))  # create procedural process
        self.__procs_started = yield pro  # run the process, keep its return value
        while True:
            try:
                self.__procs_started.remove(self.__pr._PROCEDURAL)
            except ValueError:
                yield self.__proc_activate  # wait for proc_activate
            else:
                for proc in self.__procs_started:
                    name = proc[0]
                    if not self.__dict_extra_proc_activate[name].triggered:
                        if proc[1].__name__ in self.__pr._INTERRUPTIBLE:
                            self.__interruptibles[name] = proc[
                                1]  # add new process interruptibles if the process can be interrupted according to ACT-R
                        self.__dict_extra_proc_activate[name].succeed()  # activate modules that were used if not active
                    else:
                        if name in self.__interruptibles and proc[1] != self.__interruptibles[name]:
                            self.__interruptibles[name] = proc[1]
                            self.__dict_extra_proc[name].interrupt()  # otherwise, interrupt them
            for _ in range(5):
                yield self.__simulation.timeout(
                    0)  # move procedural process to the bottom; right now, this is a hack - it yields 0 timeout five times, so other processes get enough cycles to start etc.
            pro = self.__simulation.process(
                self.__localprocess__(self.__pr._PROCEDURAL, self.__pr.procedural_process(self.__simulation.now)))
            self.__procs_started = yield pro
            self.__proc_activate = self.__simulation.event()  # start the event

    def run(self, max_time=1):
        """
        Run simulation for the number of seconds specified in max_time.
        """
        if not self.gui:
            self.__simulation.run(max_time)
        else:
            self.__runGUI__()
        if self.__simulation.peek() == float("inf"):
            self.__pr.compile_rules()  # at the end of the simulation, run compilation (the last two rules are not yet compiled)

    def show_time(self):
        """
        Show current time in simulation.
        """
        try:
            t = self.__simulation.now
        except AttributeError:
            raise AttributeError("No simulation is running")
        else:
            return t

    def step(self):
        """
        Make one step through simulation.
        """
        while True:
            self.__simulation.step()
            if self.current_event and self.current_event.action != self._UNKNOWN and self.current_event != self.__last_event:
                self.__last_event = self.current_event
                break
            if self.__simulation.peek() == float("inf"):
                self.__pr.compile_rules()  # at the end of the simulation, run compilation (the last two rules are not yet compiled)

    def steps(self, count):
        """
        Make several one or more steps through simulation. The number of steps is given in count.
        """
        count = int(count)
        assert count > 0, "the 'count' argument in 'steps' must be a positive number"
        for _ in range(count):
            self.step()

    def __runGUI__(self):
        """
        Simulation run using GUI for environment.
        """

        self.__root = tk.Tk()
        self.__root.wm_title("Environment")

        # Create the queue
        self.__queue = queue.Queue()

        # Set up the GUI part
        self.__environmentGUI = GuiPart(self.__env, self.__root, self.__queue, self.__endGui__)

        # Set up the thread to do asynchronous I/O -- taken from Python cookbook
        self.__running = True
        self.__thread1 = threading.Thread(target=self.__workerThread1__)
        self.__thread1.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.__periodicCall__()
        self.__root.mainloop()
        self.__running = False

    def __periodicCall__(self):
        """
        Check every 10 ms if there is something new in the queue.
        """
        self.__environmentGUI.processIncoming()
        if not self.__running:
            # This is a brutal stop of the system. Should more cleanup take place?
            import sys
            sys.exit(1)
        self.__root.after(10, self.__periodicCall__)

    def __workerThread1__(self):
        """
        Function handling the asynchronous trace output.
        """
        self.__last_event = None
        old_time = 0
        old_stimulus = None
        old_focus = None
        while self.__running:
            try:
                self.__simulation.step()
            except simpy.core.EmptySchedule:
                self.__endGui__()
            if self.current_event and self.__last_event != self.current_event:
                self.__last_event = self.current_event
                if self.__realtime:
                    time.sleep(self.current_event.time - old_time)
                old_time = self.current_event.time
                if self.__trace:
                    if self.current_event.proc != utilities._ENV:
                        print(self.current_event[0:3])
            if self.__env.stimulus and old_stimulus != self.__env.stimulus:
                old_stimulus = self.__env.stimulus
                self.__queue.put({"stim": self.__env.stimulus})
            if self.__env.current_focus and old_focus != self.__env.current_focus:
                old_focus = tuple(self.__env.current_focus)
                self.__queue.put({"focus": self.__env.current_focus})

    def __endGui__(self):
        self.__running = False