#-------------------------
# Email Processing Cognitive Modelling
# Author: Harolz
# Year: 2018
# Version: 1.0
#-------------------------
#-------------------------
# Chunks Definition
#-------------------------
# http://act-r.psy.cmu.edu/wordpress/wp-content/themes/ACT-R/tutorials/unit1.htm
# declarative knowledge are called chunks.
# Chunks represent knowledge(encode facts) that a person might be expected to have when they solve a problem
# A Chunk consists of its Chunktype and some number of slots

# chunk_type: sender_address
# value: admin@amaz0n.com **dictionary
# attribute: 1 (1 for suspicious) **dictionary

import collections
import  utilities
import warnings
import  re


def chunktype(cls_name, field_names, verbose=False):
    # if cls_name in utilities.SPECIALCHUNKTYPES and field_names != utilities.SPECIALCHUNKTYPES[cls_name]:
    #     raise ACTRError("You cannot redefine slots of the chunk type '%s'; you can only use the slots '%s'" % (
    #     cls_name, utilities.SPECIALCHUNKTYPES[cls_name]))

    try:
        field_names = field_names.replace(',', ' ').split()
    except AttributeError:  # no .replace or .split
        pass  # assume it's already a sequence of identifiers
    field_names = tuple(sorted(name + "_" for name in field_names))
    # for each in field_names:
    #     if each == "ISA" or each == "isa":
    #         raise ACTRError("You cannot use the slot 'isa' in your chunk. That slot is used to define chunktypes.")

    Chunk._chunktypes.update({cls_name: collections.namedtuple(cls_name, field_names)})  # chunktypes are not returned; they are stored as Chunk class attribute

class Chunk(collections.Sequence):
    class EmptyValue(object):
        """
        Empty values used in chunks. These are None values.
        """

        def __init__(self):
            self.value = utilities.EMPTYVALUE

        def __eq__(self, val):
            if val == utilities.EMPTYVALUE or val == str(utilities.EMPTYVALUE):
                return True #Chunks make strings out of values; (this holds for everything but cases in which chunks themselves are values); so, None will be turned into a string as well, hence the equality
            else:
                return False

        def __hash__(self):
            return hash(self.value)

        def __repr__(self):
            return repr(self.value)

    _chunktypes = {}
    _undefinedchunktypecounter = 0
    _chunks = {}
    __emptyvalue = EmptyValue()
    _similarities = {} #dict of similarities between chunks

    def __init__(self, typename,text_value,criterion, **dictionary):
        self.typename = typename
        self.criterion=criterion
        self.text_value = text_value
        self.boundvars = {} #dict of bound variables
        self.dict = dictionary

        kwargs = {}
        for key in dictionary:

            #change values (and values in a tuple) into string, when possible (when the value is not another chunk)
            if isinstance(dictionary[key], Chunk):
                dictionary[key] = utilities.VarvalClass(variables=None, values=dictionary[key], negvariables=(), negvalues=())

            elif isinstance(dictionary[key], utilities.VarvalClass):
                for x in dictionary[key]._fields:
                    if x in {"values", "variables"} and not isinstance(getattr(dictionary[key], x), str) and getattr(dictionary[key], x) != self.__emptyvalue and not isinstance(getattr(dictionary[key], x), Chunk):
                        raise TypeError("Values and variables must be strings, chunks or empty (None)")

                    elif x in {"negvariables", "negvalues"} and (not isinstance(getattr(dictionary[key], x), collections.Sequence) or isinstance(getattr(dictionary[key], x), collections.MutableSequence)):
                        raise TypeError("Negvalues and negvariables must be tuples")

            elif (isinstance(dictionary[key], collections.Iterable) and not isinstance(dictionary[key], str)) or not isinstance(dictionary[key], collections.Hashable):
                raise ValueError("The value of a chunk slot must be hashable and not iterable; you are using an illegal type for the value of the chunk slot %s, namely %s" % (key, type(dictionary[key])))

            else:
                #create namedtuple varval and split dictionary[key] into variables, values, negvariables, negvalues
                try:
                    temp_dict = utilities.stringsplitting(str(dictionary[key]))
                except utilities.ModelError as e:
                    raise utilities.ModelError("The chunk %s is not defined correctly; %s" %(dictionary[key], e))
                loop_dict = temp_dict.copy()
                for x in loop_dict:
                    if x == "negvariables" or x == "negvalues":
                        val = tuple(temp_dict[x])
                    else:
                        try:
                            val = temp_dict[x].pop()
                        except KeyError:
                            val = None
                    temp_dict[x] = val
                dictionary[key] = utilities.VarvalClass(**temp_dict)

            #adding _ to minimize/avoid name clashes
            kwargs[key+"_"] = dictionary[key]
        try:
            for elem in self._chunktypes[typename]._fields:

                if elem not in kwargs:

                    kwargs[elem] = self.__emptyvalue #emptyvalues are explicitly added to attributes that were left out
                    dictionary[elem[:-1]] = self.__emptyvalue #emptyvalues are also added to attributes in the original dictionary (since this might be used for chunktype creation later)

            if set(self._chunktypes[typename]._fields) != set(kwargs.keys()):

                chunktype(typename, dictionary.keys())  #If there are more args than in the original chunktype, chunktype has to be created again, with slots for new attributes
                warnings.warn("Chunk type %s is extended with new attributes" % typename)

        except KeyError:

            chunktype(typename, dictionary.keys())  #If chunktype completely missing, it is created first
            warnings.warn("Chunk type %s was not defined; added automatically" % typename)

        finally:
            self.actrchunk = self._chunktypes[typename](**kwargs)

        self.__empty = None #this will store what the chunk looks like without empty values (the values will be stored on the first call of the relevant function)
        self.__unused = None #this will store what the chunk looks like without unused values
        self.__hash = None, self.boundvars.copy() #this will store the hash along with variables (hash changes if some variables are resolved)
        # print("chunks added: ",end="")
        # print(self.actrchunk)

    def __getitem__(self, pos):
        return re.sub("_$", "", self.actrchunk._fields[pos]), self.actrchunk[pos]
    def __iter__(self):
        for x, y in zip(self.actrchunk._fields, self.actrchunk):
            yield re.sub("_$", "", x), y
    def __len__(self):
        return len(self.actrchunk)
    def __repr__(self):
        reprtxt = ""
        for x, y in self:
            if isinstance(y, utilities.VarvalClass):
                y = str(y)
            elif isinstance(y, self.EmptyValue):
                y = ""
            if reprtxt:
                reprtxt = ", ".join([reprtxt, '%s= %s' % (x, y)])
            elif x:
                reprtxt = '%s= %s' % (x, y)
            else:
                reprtxt = '%s' % y
        return "".join([self.typename,"[","TEXT_VALUE=",self.text_value,",","CRITERION=",self.criterion,"]","(", reprtxt, ")"])
    def __le__(self, otherchunk):
        """
        Check whether one chunk is part of another (given boundvariables in boundvars).
        """
        return self == otherchunk or self.match(otherchunk, partialmatching=False) #actually, the second disjunct should be enough -- TODO: check why it fails in some cases; this might be important for partial matching

    def match(self, otherchunk, partialmatching, mismatch_penalty=0):
        """
        Check partial match (given bound variables in boundvars).
        """
        similarity = 0
        if self == otherchunk:
            return similarity
        # below starts the check that self is proper part of otherchunk. __emptyvalue is ignored. 4 cases have to be checked separately, =x, ~=x, !1, ~!1. Also, variables and their values have to be saved in boundvars. When self is not part of otherchunk the loop adds to (dis)similarity.
        for x in self:

            try:
                matching_val = getattr(otherchunk.actrchunk, x[0] + "_")  # get the value of attr
            except AttributeError:
                matching_val = None  # if it is missing, it must be None

            if isinstance(matching_val, utilities.VarvalClass):
                matching_val = matching_val.values  # the value might be written using _variablesvalues namedtuple; in that case, get it out
            varval = utilities.splitting(x[1])
            # if otherchunk.typename == "IDENTIFY_LINKS":
            #     print("xxx:",x)
            #     print(matching_val)
            #     print(varval.values)
            # print(type(varval.values))

            # checking variables, e.g., =x
            if varval.variables:
                # if matching_val == self.__emptyvalue:
                #    similarity -= 1 #these two lines would require that variables are matched only to existing values; uncomment if you want that
                var = varval.variables
                for each in self.boundvars.get("~=" + var, set()):
                    if each == matching_val:
                        if partialmatching:
                            similarity += utilities.get_similarity(self._similarities, each, matching_val,
                                                                   mismatch_penalty)  # False if otherchunk's value among the values of ~=x
                        else:
                            return False
                try:
                    if self.boundvars["=" + var] != matching_val:
                        if partialmatching:
                            similarity += utilities.get_similarity(self._similarities, self.boundvars["=" + var],
                                                                   matching_val,
                                                                   mismatch_penalty)  # False if =x does not match otherchunks' value
                        else:
                            return False
                except KeyError:
                    self.boundvars.update({"=" + var: matching_val})  # if boundvars lack =x, update and proceed

            # checking negvariables, e.g., ~=x
            if varval.negvariables:
                for var in varval.negvariables:
                    try:
                        if self.boundvars["=" + var] == matching_val:
                            if partialmatching:
                                similarity += utilities.get_similarity(self._similarities, self.boundvars["=" + var],
                                                                       matching_val,
                                                                       mismatch_penalty)  # False if =x does not match otherchunks' value
                            else:
                                return False
                    except KeyError:
                        pass
                    self.boundvars.setdefault("~=" + var, set([])).add(matching_val)

            # checking values, e.g., 10 or !10

            if varval.values:
                val = varval.values
                if val != None and val != matching_val:  # None is the misssing value of the attribute
                    if partialmatching:
                        similarity += utilities.get_similarity(self._similarities, val, matching_val, mismatch_penalty)
                    else:
                        return False
            # checking negvalues, e.g., ~!10
            if varval.negvalues:
                for negval in varval.negvalues:
                    if negval == matching_val or (
                            negval in {self.__emptyvalue, 'None'} and matching_val == self.__emptyvalue):
                        if partialmatching:
                            similarity += utilities.get_similarity(self._similarities, negval, matching_val,
                                                                   mismatch_penalty)
                        else:
                            return False
        if partialmatching:
            return similarity
        else:
            return True

    def removeunused(self):
        """
        Remove values that were only added to fill in empty slots, using None.

        Be careful! This returns a generator with slot-value pairs.
        """

        def unusing_func():
            for x in self:
                try:
                    if x[1].removeunused():
                        if x[1] != utilities.EMPTYVALUE:
                            yield x
                except AttributeError:
                    try:
                        if x[1].values != utilities.EMPTYVALUE or x[1].variables or x[1].negvariables or x[1].negvalues:
                            yield x
                    except AttributeError:
                        pass

        if not self.__unused:
            self.__unused = tuple(unusing_func())
        return self.__unused

def makechunk(nameofchunk="", typename="",text_value="",criterion="",**dictionary):
    if not nameofchunk:
        nameofchunk = "unnamedchunk"
    if not typename:
        typename = "undefined" + str(Chunk._undefinedchunktypecounter)
        Chunk._undefinedchunktypecounter += 1
    if not criterion:
        criterion = "criterion"
    if not text_value:
        text_value = "no_text"
    for key in dictionary:
        if isinstance(dictionary[key], Chunk):
            pass
        elif isinstance(dictionary[key], utilities.VarvalClass):
            pass
        else:
            try:
                temp_dict = utilities.stringsplitting(str(dictionary[key]))
                # print(temp_dict)
            except utilities.ModelError as e:
                raise utilities.ModelError("The chunk value %s is not defined correctly; %s" % (dictionary[key], e))
            loop_dict = temp_dict.copy()
            for x in loop_dict:
                if x == "negvariables" or x == "negvalues":
                    val = tuple(temp_dict[x])
                else:
                    try:
                        val = temp_dict[x].pop()
                    except KeyError:
                        val = None
                temp_dict[x] = val
            dictionary[key] = utilities.VarvalClass(**temp_dict)

    created_chunk = Chunk(typename,text_value,criterion,**dictionary)
    created_chunk._chunks[nameofchunk] = created_chunk
    return created_chunk


