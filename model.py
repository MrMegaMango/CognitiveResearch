import chunks
import utilities
import declarative
import goals
import simulation

class Email_Cog_Sim_Model(object):
    MODEL_PARAMETERS = {"subsymbolic": False,
                        "rule_firing": 0.05,
                        "latency_factor": 0.1,
                        "latency_exponent": 1.0,
                        "decay": 0.5,
                        "baselevel_learning": True,
                        "optimized_learning": False,
                        "instantaneous_noise": 0,
                        "retrieval_threshold": 0,
                        "buffer_spreading_activation": {},
                        "spreading_activation_restricted": False,
                        "strength_of_association": 0,
                        "association_only_from_chunks": True,
                        "partial_matching": False,
                        "mismatch_penalty": 1,
                        "activation_trace": False,
                        "utility_noise": 0,
                        "utility_learning": False,
                        "utility_alpha": 0.2,
                        "motor_prepared": False,
                        "strict_harvesting": False,
                        "production_compilation": False,
                        "automatic_visual_search": True,
                        "emma": True,
                        "emma_noise": True,
                        "emma_landing_site_noise": False,
                        "eye_mvt_angle_parameter": 1,  # in LispACT-R: 1
                        "eye_mvt_scaling_parameter": 0.01,  # in LispACT-R: 0.01, but dft rule firing -- 0.01
                        }

    def __init__(self, environment=None, **model_parameters):
        self.chunktype = chunks.chunktype
        start_goal = goals.Goal()
        self.goals = {"g": start_goal}

        self.__buffers = {"g": start_goal}

        start_retrieval = declarative.DecMemBuffer()
        self.retrievals = {"retrieval": start_retrieval}

        self.__buffers["retrieval"] = start_retrieval

        start_dm = declarative.DecMem()
        self.decmems = {"decmem": start_dm}

        self.__similarities = {}

        self.model_parameters = self.MODEL_PARAMETERS.copy()

        try:
            if not set(model_parameters.keys()).issubset(set(self.MODEL_PARAMETERS.keys())):
                raise (utilities.ModelError(
                    "Incorrect model parameter(s) %s. The only possible model parameters are: '%s'" % (
                    set(model_parameters.keys()).difference(set(self.MODEL_PARAMETERS.keys())),
                    set(self.MODEL_PARAMETERS.keys()))))
            self.model_parameters.update(model_parameters)
        except TypeError:
            pass

        self.__env = environment

    @property
    def retrieval(self):
        """
        Retrieval in the model.
        """
        if len(self.retrievals) == 1:
            return list(self.retrievals.values())[0]
        else:
            raise (ValueError(
                "Zero or more than 1 retreival specified, unclear which one should be shown. Use ACTRModel.retrievals instead."))

    @property
    def decmem(self):
        """
        Declarative memory in the model.
        """
        if len(self.decmems) == 1:
            return list(self.decmems.values())[0]
        else:
            raise (ValueError(
                "Zero or more than 1 declarative memory specified, unclear which one should be shown. Use ACTRModel.decmems instead."))

    def set_decmem(self, data=None):
        """
        Set declarative memory.
        """
        dm = declarative.DecMem(data)
        if len(self.decmems) > 1:
            self.decmems["".join(["decmem", str(len(self.decmems))])] = dm
        else:
            self.decmems["decmem"] = dm
        return dm

    def set_similarities(self, chunk, otherchunk, value):
        """
        Set similarities between chunks. By default, different chunks have the value of -1.

        chunk and otherchunk are two chunks whose similarities are set. value must be a non-positive number.
        """
        if value > 0:
            raise utilities.ACTRError("Values in similarities must be 0 or smaller than 0")
        self.__similarities[tuple((chunk, otherchunk))] = value
        self.__similarities[tuple((otherchunk, chunk))] = value


    def simulation(self, realtime=False, trace=True, gui=True, initial_time=0, environment_process=None, **kwargs):
        """
        Prepare simulation of the model

        This will actually not run the simulation it will only return the simulation object. The object can then be run using run(max_time) command.

        realtime - should the simualtion be run in real time or not?
        trace - should the trace of the simulation be printed?
        gui - should the environment appear on a separate screen? (This requires tkinter)
        initial_time - what is the starting time point of the simulation?
        environment_process - what environment process should the simulation use?
        The last argument should be supplied with the method environment_process of the environemnt used in the model.
        kwargs are arguments that environment_process will be supplied with.
        """

        if len(self.decmems) == 1:
            for key in self.__buffers:
                self.__buffers[key].dm = self.decmem #if only one dm, let all buffers use it
        elif len([x for x in self.decmems.values() if x]) == 1:
            for key in self.__buffers:
                if not self.__buffers[key].dm:
                    self.__buffers[key].dm = self.decmem #if only one non-trivial dm, let buffers use it that do not have a dm specified

        decmem = {name: self.__buffers[name].dm for name in self.__buffers\
                if self.__buffers[name].dm != None} #dict of declarative memories used; more than 1 decmem might appear here

        # self.__buffers["manual"] = motor.Motor() #adding motor buffer

        if self.__env:
            self.__env.initial_time = initial_time #set the initial time of the environment to be the same as simulation
            # if self.visbuffers:
            #     self.__buffers.update(self.visbuffers)
            # else:
            #     dm = list(decmem.values())[0]
            #     self.__buffers["visual"] = vision.Visual(self.__env, dm) #adding vision buffers
            #     self.__buffers["visual_location"] = vision.VisualLocation(self.__env, dm) #adding vision buffers

        self.used_productions = productions.ProductionRules(self.__productions, self.__buffers, decmem, self.model_parameters) #only temporarily changed, should be used_productions

        chunks.Chunk._similarities = self.__similarities

        return simulation.Simulation(self.__env, realtime, trace, gui, self.__buffers, self.used_productions, initial_time, environment_process, **kwargs)

