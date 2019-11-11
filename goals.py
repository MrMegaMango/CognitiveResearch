import chunks
import utilities
import buffers

class Goal(buffers.Buffer):
    """
    Goal buffer module.
    """

    def __init__(self, data=None, default_harvest=None, delay=0):
        buffers.Buffer.__init__(self, default_harvest, data)
        self.delay = delay
        print("Goal Buffer: ", end="")
        print(self)

    @property
    def delay(self):
        """
        Delay (in s) to create chunks in the goal buffer.
        """
        return self.__delay

    @delay.setter
    def delay(self, value):
        if value >= 0:
            self.__delay = value
        else:
            raise ValueError('Delay in the goal buffer must be >= 0')