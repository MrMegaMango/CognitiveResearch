#-------------------------
# Email Processing Cognitive Modelling
# Author: Harolz
# Year: 2018
# Version: 1.0
#-------------------------
#-------------------------
# Buffers Definition
#-------------------------

import collections
import chunks
import utilities

class Buffer(collections.MutableSet):
    _BUSY = utilities._BUSY
    _FREE = utilities._FREE
    _ERROR = utilities._ERROR

    def __init__(self, dm=None, data=None):
        self.dm = dm
        self.state = self._FREE #set here but state of buffer instances controlled in productions
        if data == None:
            self._data = set([])
        else:
            self._data = data
        assert len(self) <= 1, "Buffer can carry at most one element"


    @property
    def dm(self):
        """
        Default harvest of goal buffer.
        """
        return self.__dm

    @dm.setter
    def dm(self, value):
        if isinstance(value, collections.MutableMapping) or not value:
            self.__dm = value
        else:
            raise ValueError('The attempted dm value cannot be set; it is not a possible declarative memory')

    def __contains__(self, elem):
        return elem in self._data

    def __iter__(self):
        for elem in self._data:
            yield elem

    def __len__(self):
        return len(self._data)

    def add(self, elem):
        """
        Add a chunk into the buffer.

        elem must be a chunk.
        """
        self._data = set()

        if isinstance(elem, chunks.Chunk):
            self._data.add(elem)
        else:
            raise TypeError("Only chunks can be added to Buffer")

    def discard(self, elem):
        """
        Discard an element without clearing it into a memory.
        """
        self._data.discard(elem)