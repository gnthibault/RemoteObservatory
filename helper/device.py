# Generic imports
from abc import ABC
import asyncio
import base64
import functools
import logging
import lxml
from lxml import etree
import os
import time
import traceback
import threading
import xml.parsers.expat

"""
The Base classes for the pyINDI device. Definitions
are adapted from the INDI white paper:
http://www.clearskyinstitute.com/INDI/INDI.pdf
For now we will only by supporting version 1.7

Naming convention are based on the indilib c++ version:
http://www.indilib.org/api/index.html
"""

class _indinameconventions:
    """
    The INDI naming scheme.
    @ivar basenames : The possible "Basenames" of an L{indiobject} ["Text","Switch","Number","BLOB","Light"]
    @type basenames : list of StringType
    """

    def __init__(self):
        self.basenames = ["Text", "Switch", "Number", "BLOB", "Light"]

    def _get_defelementtag(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:  xml tag of an element that is send by the server when an C{IDDef*} function is called
        on vector which contains the element (like C{defText}).
        @rtype: StringType
        """
        return "def" + basename

    def _get_defvectortag(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:  xml tag of a vector that is send by the server when an C{IDDef*} function is called(like C{defTextVector}).
        @rtype: StringType
        """
        return "def" + basename + "Vector"

    def _get_setelementtag(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:		xml tag of an element that is send by the server when an C{IDSet*} function is called
        on vector which contains the element (like C{oneText}).
        @rtype: StringType
        """
        return "one" + basename

    def _get_setvectortag(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:  xml tag of a vector that is send by the server when am C{IDSet*} function is called (like C{setTextVector}).
        @rtype: StringType
        """
        return "set" + basename + "Vector"

    def _get_newelementtag(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:  xml tag of an element that is send by the client (like C{oneText}).
        @rtype: StringType
        """
        return "one" + basename

    def _get_newvectortag(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:  xml tag of a vector that is send by the client (like C{newTextVector}).
        @rtype: StringType
        """
        return "new" + basename + "Vector"

    def _get_message_tag(self):
        """
        @return:  xml tag of an INDI message.
        @rtype: StringType
        """
        return "message"

    def _get_vector_repr(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:  printable representation of the type of the vector .
        @rtype: StringType
        """
        return basename + "Vector"

    def _get_element_repr(self, basename):
        """
        @param basename : The basename of the tag see (L{basenames})
        @type basename : StringType
        @return:  printable representation of the type of the element .
        @rtype: StringType
        """
        return basename


class _inditagfactory(_indinameconventions):
    """
    A Class to create an L{indixmltag} from its XML representation
    @ivar dict : a dictionary mapping XML representations to the corresponding L{indixmltag} objects
    @type dict : DictType
    """

    def __init__(self):
        """
        Constructor
        """
        _indinameconventions.__init__(self)
        self.dict = {}
        for i, basename in enumerate(self.basenames):
            inditag = indixmltag(True, False, False, i, inditransfertypes.idef)
            stringtag = self._get_defvectortag(basename)
            self.dict.update({stringtag: inditag})
            inditag = indixmltag(False, True, False, i, inditransfertypes.idef)
            stringtag = self._get_defelementtag(basename)
            self.dict.update({stringtag: inditag})

            inditag = indixmltag(True, False, False, i, inditransfertypes.iset)
            stringtag = self._get_setvectortag(basename)
            self.dict.update({stringtag: inditag})
            inditag = indixmltag(False, True, False, i, inditransfertypes.iset)
            stringtag = self._get_setelementtag(basename)
            self.dict.update({stringtag: inditag})

            inditag = indixmltag(True, False, False, i, inditransfertypes.inew)
            stringtag = self._get_newvectortag(basename)
            self.dict.update({stringtag: inditag})
            inditag = indixmltag(False, True, False, i, inditransfertypes.inew)
            stringtag = self._get_newelementtag(basename)
            self.dict.update({stringtag: inditag})

        inditag = indixmltag(False, False, True, None, inditransfertypes.inew)
        self.dict.update({"message": inditag})

    def create_tag(self, tag):
        """
        @param tag : the XML tag denoting the vector
        @type tag : StringType
        @return: An L{indixmltag} created according to the information given in  L{tag}
        @rtype: L{indixmltag}
        """
        if tag in self.dict:
            inditag = self.dict[tag]
            return inditag
        else:
            return None


class inditransfertype:
    """
    This is object is used to denote whether the an object was sent from the client to the server or vice versa and
    whether the object is just being defined or if it  was defined earlier.
    """
    None


class inditransfertypes(inditransfertype):
    """
    A Class containing the different transfer types
    """
    class inew(inditransfertype):
        """The object is send from the client to the server"""
        None

    class idef(inditransfertype):
        """
        The object is send from to the server to the client and the client is not expected to know about it already.
        Thus the server is just defining the object to the client. This corresponds to an C{def*} tag in the XML representation.
        Or  a client calling the C{IDDef*} function.
        """
        None

    class iset(inditransfertype):
        """
        The object is send from to the server to the client and the client is expected to know about it already.
        Thus the server is just setting new value for an existing object to the client. This corresponds to an C{set*} tag
        in the XML representation. Or  a client calling the C{IDSet*}
        """
        None


class indixmltag(_indinameconventions):
    """
    Classifys a received INDI object by its tag. Provides functions to generate different versions of the tag for different
    ways of sending it (see L{inditransfertype}).
    @ivar _is_vector : C{True} if the tag denotes an L{indivector}, C{False} otherwise
    @type _is_vector : BooleanType
    @ivar _is_element : C{True} if the tag denotes an L{indielement}, C{False} otherwise
    @type _is_element : BooleanType
    @ivar _is_message : C{True} if the tag denotes an L{indimessage}, C{False} otherwise
    @type _is_message : BooleanType
    @ivar _transfertype : the way the object has been transferred (see L{inditransfertype}).
    @type _transfertype : L{inditransfertype}
    @ivar _index : The index of the basename of the object, in the L{basenames} list
    @type _index : IntType
    """

    def __init__(self, is_vector, is_element, is_message, index, transfertype):
        """
        @param is_vector : C{True} if the tag shall denote an L{indivector}, C{False} otherwise
        @type is_vector : BooleanType
        @param is_element : C{True} if the tag shall denote an L{indielement}, C{False} otherwise
        @type is_element : BooleanType
        @param is_message : C{True} if the tag shall denote an L{indimessage}, C{False} otherwise
        @type is_message : BooleanType
        @param transfertype : the way the object has been transferred (see L{inditransfertype}).
        @type transfertype : L{inditransfertype}
        @param index : The index of the basename of the object, in the L{basenames} list
        @type index : IntType
        """
        _indinameconventions.__init__(self)
        self._is_vector = is_vector
        self._is_element = is_element
        self._is_message = is_message
        self._transfertype = transfertype
        self._index = index
        if index is not None:
            self._basename = self.basenames[index]
        if self.is_message():
            self._initial_tag = self._get_message_tag()
        else:
            self._initial_tag = self.get_xml(self.get_transfertype())

    def get_transfertype(self):
        """
        @return:  The way the object has been transferred
        @rtype: L{inditransfertype}
        """
        return self._transfertype

    def get_index(self):
        """
        @return: The index of the basename of the object, in the L{basenames} list
        @rtype: IntType
        """
        return self._index

    def is_vector(self):
        """
        @return:  C{True}, if it denotes vector, C{False} otherwise
        @rtype: BooleanType
        """
        return self._is_vector

    def is_element(self):
        """
        @return:  C{True}, if it denotes an element, C{False} otherwise
        @rtype: BooleanType
        """
        return self._is_element

    def is_message(self):
        """
        @return:  C{True}, if it denotes a message, C{False} otherwise
        @rtype: BooleanType
        """
        return self._is_message

    def get_initial_tag(self):
        """
        @return:  A sting representing the tag specified by the parameters given to the initialiser
        @rtype: StringType
        """
        return self._initial_tag

    def get_xml(self, transfertype):
        """
        Returns the string the be used in the tags in the XML representation of the object
        (like C{defTextVector} or C{oneSwitch} or C{newLightVector}).
        @param transfertype : An object describing the way the generated XML data is going to be sent (see L{inditransfertype}).
        @type transfertype : L{inditransfertype}
        @return: An XML representation of the object
        @rtype: StringType
        """
        if transfertype == inditransfertypes.inew:
            if self._is_vector:
                return self._get_newvectortag(self._basename)
            if self._is_element:
                return self._get_newelementtag(self._basename)
        if transfertype == inditransfertypes.iset:
            if self._is_vector:
                return self._get_setvectortag(self._basename)
            if self._is_element:
                return self._get_setelementtag(self._basename)
        if transfertype == inditransfertypes.idef:
            if self._is_vector:
                return self._get_defvectortag(self._basename)
            if self._is_element:
                return self._get_defelementtag(self._basename)
        if self._is_message:
            return self._get_message_tag()

    def get_type(self):
        """
        Returns a string representing the type of the object denoted by this tag (like C{TextVector} or C{Number}).
        @return: a string representing the type of the object denoted by this tag (like C{TextVector} or C{Number}).
        @rtype: StringType
        """
        if self._is_vector:
            return self._get_vector_repr(self._basename)
        if self._is_element:
            return self._get_element_repr(self._basename)
        if self._is_message:
            return self._get_message_tag()


class _indiobjectfactory(_indinameconventions):
    """
    A Class to create L{indiobject}s from their XML attributes
    @ivar elementclasses : a list of classes derived from L{indielement} the index has to be synchronous with L{basenames}
    @type elementclasses : a list of L{indielement}
    @ivar vectorclasses : a list of classes derived from L{indielement} the index has to be synchronous with L{basenames}
    @type vectorclasses : a list of L{indivector}
    """

    def __init__(self):
        """
        Constructor
        """
        _indinameconventions.__init__(self)
        self.tagfactory = _inditagfactory()
        self.elementclasses = [inditext, indiswitch, indinumber, indiblob, indilight]
        self.vectorclasses = [inditextvector, indiswitchvector, indinumbervector, indiblobvector, indilightvector]

    def create(self, tag, attrs):
        """
        @param tag : the XML tag denoting the vector
        @type tag : StringType
        @param attrs : The XML attributes of the vector
        @type attrs : DictType
        @return: An indiobject created according to the information given in  L{tag}  and L{attrs}
        @rtype: L{indiobject}
        """
        inditag = self.tagfactory.create_tag(tag)
        if inditag is None:
            return None
        if tag == self._get_message_tag():
            return indimessage(attrs)
        i = inditag.get_index()
        if inditag.is_element():
            vec = self.elementclasses[i](attrs, inditag)
            return vec

        if inditag.is_vector():
            return self.vectorclasses[i](attrs, inditag)


class indipermissions:
    """
    The indi read/write permissions.
    @ivar perm : The users read/write permissions for the  vector possible values are:
            - C{ro} (Read Only )
            - C{wo} (Write Only)
            - C{rw} (Read/Write)
    @type perm : StringType
    """

    def __init__(self, perm):
        """
        @param perm : The users read/write permissions for the  vector possible values are:
                - C{ro} (Read Only )
                - C{wo} (Write Only)
                - C{rw} (Read/Write)
        @type perm : StringType
        """
        self.perm = perm

    def is_readable(self):
        """
        @return: C{True} is the object is readable, C{False} otherwise
        @rtype: BooleanType
        """
        if (self.perm == "ro" or self.perm == "rw"):
            return True
        else:
            return False

    def is_writeable(self):
        """
        @return: C{True} is the object is writable, C{False} otherwise
        @rtype: BooleanType
        """
        if (self.perm == "wo" or self.perm == "rw"):
            return True
        else:
            return False

    def get_text(self):
        """
        @return: a string representing the permissions described by this object
        @rtype: StringType
        """
        if self.perm == "wo":
            return "write only"
        if self.perm == "rw":
            return "read and write"
        if self.perm == "ro":
            return "read only"


class indiobject:
    """ The Base Class for INDI objects (so anything that INDI can send or receive )
    @ivar tag: The XML tag of the INDI object (see L{indixmltag}).
    @type tag: L{indixmltag}
    """

    def __init__(self, attrs, tag):
        """
        @param tag: The XML tag of the vector (see L{indixmltag}).
        @type tag: L{indixmltag}
        @param attrs: The attributes of the XML version of the INDI object.
        @type attrs: DictType
        """
        self.tag = tag

    def is_valid(self):
        """
        Checks whether the object is valid.
        @return:  C{True} if the object is valid, C{False} otherwise.
        @rtype: BooleanType
        """
        return True

    def get_xml(self, transfertype):
        """
        Returns an XML representation of the object
        @param transfertype : The L{inditransfertype} for which the XML code  shall be generated
        @type transfertype : {inditransfertype}
        @return:  an XML representation of the object
        @rtype: StringType
        """
        None

    def _check_writeable(self):
        """
        Raises an exception if the object is not writable
        @return: B{None}
        @rtype: NoneType
        """
        return True

    def update(self, attrs, tag):
        """
        Update this element with data received form the XML Parser.
        @param attrs: The attributes of the XML version of the INDI object.
        @type attrs: DictType
        @param tag: The XML tag of the object (see L{indixmltag}).
        @type tag: L{indixmltag}
        @return: B{None}
        @rtype: NoneType
        """
        self.tag = tag


class indinamedobject(indiobject):
    """
    An indiobject that has got a name as well as a label
    @ivar name : name of the INDI object as given in the "name" XML attribute
    @type name : StringType
    @ivar label : label of the INDI object as given in the "label" XML attribute
    @type label : StringType
    """

    def __init__(self, attrs, tag):
        """
        @param tag: The XML tag of the object (see L{indixmltag}).
        @type tag: L{indixmltag}
        @param attrs: The attributes of the XML version of the INDI object.
        @type attrs: DictType
        """
        indiobject.__init__(self, attrs, tag)
        name = attrs.get('name', "").strip()
        label = attrs.get('label', "").strip()
        self.name = name
        if label == "":
            self.label = name
        else:
            self.label = label

    def getName(self):
        return self.name


class indielement(indinamedobject):
    """ The Base Class of any element of an INDI Vector \n
    @ivar _value : The value of the INDI object. Meaning character contained between the end of the
            I{StartElement} and the beginning of the I{EndElement} in XML version. This may be coded in another format
            or compressed  and thus require some manipulation before it can be used.
    @type _value : StringType
    @ivar _old_value : The old value of the object, the value it had when L{_get_changed} was called last time.
    @type _old_value : StringType
    """

    def __init__(self, attrs, tag):
        indinamedobject.__init__(self, attrs, tag)
        self._set_value('')
        self._old_value = self._value

    def _get_changed(self):
        """
        @return: C{True} if the objects XML data was changed since the last L{_get_changed} was called,
        C{False} otherwise.
        @rtype: BooleanType
        """
        if self._old_value == self._value:
            return False
        else:
            self._old_value = self._value
            return True

    def set_float(self, num):
        """
        @param num: The new value to be set.
        @type num: FloatType
        @return: B{None}
        @rtype: NoneType
        """
        self._set_value(str(num))

    def _set_value(self, value):
        """
        Sets the value variable of this object.
        @param value: A string to be copied into the L{_value}.
        @type value: DictType
        @return: B{None}
        @rtype: NoneType
        """
        self._check_writeable()
        self._value = value

    def tell(self):
        """
        Logs all parameters of the object
        @return: B{None}
        @rtype: NoneType
        """
        logging.info("INDIElement: %s %s %s %s" % (self.name, self.label, self.tag.get_type(), self._value))

    def get_text(self):
        """
        @return: a string representation of it value
        @rtype: StringType
        """
        return self._value

    def set_text(self, text):
        """
        @param text: A string representation of the data to be written into the object.
        @type text: StringType
        @return: B{None}
        @rtype: NoneType
        """
        self._check_writeable()
        self._set_value(str(text))

    def get_xml(self, transfertype):
        tag = self.tag.get_xml(transfertype)
        data = "<" + tag + ' name="' + self.name + '"> ' + self._value + "</" + tag + "> "
        return data

    def updateByElement(self, element):
        self._set_value(element._value)


class indinumber(indielement):
    """
    A floating point number with a defined format \n
    @ivar format : A format string describing the way the number is displayed
    @type format : StringType
    @ivar _min : The minimum value of the number
    @type _min : StringType
    @ivar _max : The maximum value of the number
    @type _max : StringType
    @ivar _step : The step increment of the number
    @type _step : StringType
    """

    def __init__(self, attrs, tag):
        self._value = ""
        indielement.__init__(self, attrs, tag)
        self.format = attrs.get('format', "").strip()
        self._min = attrs.get('min', "").strip()
        self._max = attrs.get('max', "").strip()
        self._step = attrs.get('step', "").strip()

    def get_min(self):
        """
        @return: The smallest possible value for this object
        @rtype: FloatType
        """
        return float(self._min)

    def get_max(self):
        """
        @return: The highest possible value for this object
        @rtype: FloatType
        """
        return float(self._max)

    def get_step(self):
        """
        @return: The stepsize
        @rtype: FloatType
        """
        return float(self._step)

    def is_range(self):
        """
        @return: C{True} if (L{get_step}>0) B{and} (L{get_range}>0)  , C{False} otherwise.
        @rtype: FloatType
        """
        if self.get_step() <= 0 or (self.get_range()) <= 0:
            return False
        return True

    def get_range(self):
        """
        @return: L{get_max}-L{get_min}
        @rtype: FloatType
        """
        return self.get_max() - self.get_min()

    def get_number_of_steps(self):
        """
        @return: The number of steps between min and max, 0 if L{is_range}==False
        @rtype: IntType
        """
        if self.is_range():
            return int(np.floor(self.get_range() / self.get_step()))
        else:
            return 0

    def _set_value(self, value):
        try:
            float(value)
        except Exception:
            return
        indielement._set_value(self, value)

    def get_float(self):
        """
        @return: a float representation of it value
        @rtype: FloatType
        """
        success = False
        while success is False:
            success = True
            try:
                x = float(self._value)
            except Exception as e:
                success = False
                time.sleep(1)
                logging.warning(f"INDI Warning: invalid float {self._value} ({e})")
        return x

    def get_digits_after_point(self):
        """
        @return: The number of digits after the decimal point in the string representation of the number.
        @rtype: IntType
        """
        text = self.get_text()
        i = len(text) - 1
        while i >= 0:
            if text[i] == ".":
                return (len(text) - i - 1)
            i = i - 1
        return 0

    def get_int(self):
        """
        @return: an integer representation of it value
        @rtype: IntType
        """
        return int(round(self.get_float()))

    def set_float(self, num):
        """
        @param num: The new value to be set.
        @type num: FloatType
        @return: B{None}
        @rtype: NoneType
        """
        if self.is_sexagesimal:
            self._set_value(str(num))
        else:
            self._set_value(self.format % num)

    def is_sexagesimal(self):
        """
        @return: C{True} if the format property requires sexagesimal display
        @rtype: BooleanType
        """
        return (not (-1 == self.format.find("m")))

    def get_text(self):
        """
        @return: a formated string representation of it value
        @rtype:  StringType
        """
        if (-1 == self.format.find("m")):
            return self.format % self.get_float()
        else:
            return _sexagesimal(self.format, self.get_float())

    def set_text(self, text):
        """
        @param text: A string representing the the new value to be set.
                Sexagesimal format is also supported
        @type text: StringType
        @return: B{None}
        @rtype: NoneType
        """
        sex = []
        sex.append("")
        sex.append("")
        sex.append("")
        nsex = 0
        for i in range(len(text)):
            if text[i] == ":":
                nsex = nsex + 1
            else:
                sex[nsex] = sex[nsex] + text[i]
        val = 0
        error = False
        if nsex > 2:
            error = True
        for i in range(nsex + 1):
            factor = 1.0 / pow(60, i)
            try:
                val = val + float(sex[i]) * factor
            except Exception as e:
                logging.warning(f"Problem setting indinumber text: {e}")
                error = True
        if not error:
            self.set_float(val)


class inditext(indielement):
    """a (nearly) arbitrary text"""


class indilight(indielement):
    """
    a status light
    @ivar _value : The overall operating state of the device. possible values are:
            - C{Idle} (device is currently not connected or unreachable)
            - C{Ok} (device is ready to do something)
            - C{Busy} (device is currently busy doing something, and not ready to do anything else)
            - C{Alert} (device is responding, but at least one function does not work at the moment)
    @type _value : StringType
    """

    def __init__(self, attrs, tag):
        self._value = ""
        indielement.__init__(self, attrs, tag)
        if self.tag.is_vector():
            self._set_value("Alert")
            self._set_value(attrs.get('state', "").strip())
            indielement.__init__(self, attrs, tag)
        if self.tag.is_element():
            indielement.__init__(self, attrs, tag)

    def is_ok(self):
        """
        @return: C{True} if the light indicates the C{Ok} state (device is ready to do something), C{False} otherwise
        @rtype:  BooleanType
        """
        if self._value == "Ok":
            return True
        else:
            return False

    def is_busy(self):
        """
        @return: C{True} if the light indicates the C{Busy} state (device is currently busy doing something,
        and not ready to do anything else) , C{False} otherwise
        @rtype:  BooleanType
        """
        if self._value == "Busy":
            return True
        else:
            return False

    def is_idle(self):
        """
        @return: C{True} if the light indicates the C{Idle} state (device is currently not connected or unreachable)
        , C{False} otherwise
        @rtype:  BooleanType
        """
        if self._value == "Idle":
            return True
        else:
            return False

    def is_alert(self):
        """
        @return: C{True} if the light indicates the C{Alert}state (device is responding, but at least
        one function does not work at the moment) C{False} otherwise
        @rtype:  BooleanType
        """
        if self._value == "Alert":
            return True
        else:
            return False

    def _set_value(self, value):
        for state in ["Idle", "Ok", "Busy", "Alert"]:
            if value == state:
                indielement._set_value(self, value)

    def set_text(self, text):
        raise Exception("INDILigths are read only")
        # self._set_value(str(text))

    def update(self, attrs, tag):
        if self.tag.is_vectortag(tag):
            self._set_value("Alert")
            self._set_value(attrs.get('state', "").strip())
            indielement.update(self, attrs, tag)
        if self.tag.is_elmenttag(tag):
            indielement.update(self, attrs, tag)


class indiswitch(indielement):
    """a switch that can be either C{On} or C{Off}"""

    def get_active(self):
        """
        @return: a Boolean representing the state of the switch:
                - True (I{Python}) = C{"On"} (I{INDI})
                - False (I{Python}) = C{"Off"} (I{INDI})
        @rtype: BooleanType
        """
        if self._value == "On":
            return True
        else:
            return False

    def set_active(self, bool):
        """
        @param bool: The boolean representation of the new state of the switch.
                - True (I{Python}) = C{"On"} (I{INDI})
                - False (I{Python}) = C{"Off"} (I{INDI})
        @type bool: BooleanType:
        @return: B{None}
        @rtype: NoneType
        """
        if bool:
            self._set_value("On")
        else:
            self._set_value("Off")


class indiblob(indielement):
    """
    @ivar format : A string describing the file-format/-extension (e.g C{.fits})
    @type format : StringType
    """

    def __init__(self, attrs, tag):
        indielement.__init__(self, attrs, tag)
        self.format = attrs.get('format', "").strip()

    def _get_decoded_value(self):
        """
        Decodes the value of the BLOB it does the base64 decoding as well as zlib decompression.
        zlib decompression is done only if the current L{format} string ends with C{.z}.
        base64 decoding is always done.
        @return: the decoded version of value
        @rtype: StringType
        """
        value = self._value.encode("utf8")
        if len(self.format) >= 2:
            if self.format[len(self.format) - 2] + self.format[len(self.format) - 1] == ".z":
                return zlib.decompress(base64.decodestring(value))
            else:
                return base64.decodestring(value)
        else:
            return base64.decodestring(value)

    def _encode_and_set_value(self, value, format):
        """
        Encodes the value to be written into the BLOB it does the base64 encoding as well as
        zlib compression. Zlib compression is done only if the current L{format} string ends with C{.z}.
        base64 encoding is always done.
        @param value:  The value to be set, plain binary version.
        @type value: StringType
        @param format:  The format of the value to be set.
        @type format: StringType
        @return: B{None}
        @rtype: NoneType
        """
        self.format = format
        if len(self.format) >= 2:
            if self.format[len(self.format) - 2] + self.format[len(self.format) - 1] == ".z":
                self._set_value(base64.encodestring(zlib.compress(value)))
            else:
                self._set_value(base64.encodestring(value))
        else:
            self._set_value(base64.encodestring(value))

    def get_plain_format(self):
        """
        @return: The format of the BLOB, possible extensions due to compression like C{.z} are removed
        @rtype: StringType
        """
        if len(self.format) >= 2:
            if self.format[len(self.format) - 2] + self.format[len(self.format) - 1] == ".z":
                return self.format.rstrip(".z")
            else:
                return self.format
        else:
            return self.format

    def get_data(self):
        """
        @return: the plain binary version of its data
        @rtype: StringType
        """
        return self._get_decoded_value()

    def get_text(self):
        """
        @return: the plain binary version of its data
        @rtype: StringType
        """
        return self._get_decoded_value()

    def set_from_file(self, filename):
        """
        Loads a BLOB with data from a file.
        The extension of the file is used as C{format} attribute of the BLOB
        @param filename:  The name of the file to be loaded.
        @type filename: StringType
        @return: B{None}
        @rtype: NoneType
        """
        in_file = open(filename, "r")
        text = in_file.read()
        in_file.close()
        (root, ext) = os.path.splitext(filename)
        self._encode_and_set_value(text, ext)

    def set_text(self, text):
        self._encode_and_set_value(text, ".text")

    def get_size(self):
        """
        @return: size of the xml representation of the data. This is usually not equal to the size of the
        string object returned by L{get_data}. Because blobs are base64 encoded and can be compressed.
        @rtype: StringType
        """
        return len(self._value)

    def set_from_string(self, text, format):
        """
        Loads a BLOB with data from a string.
        @param text:  The string to be loaded into the BLOB.
        @type text: StringType
        @param format:  A string to be used as the format attribute of the BLOB
        @type format: 	StringType
        @return: B{None}
        @rtype: NoneType
        """
        self._encode_and_set_value(text, format)

    def update(self, attrs, tag):
        self._check_writeable()
        indielement.update(self, attrs, tag)
        self.format = attrs.get('format', "").strip()

    def get_xml(self, transfertype):
        tag = self.tag.get_xml(transfertype)
        data = "<" + tag + ' name="' + self.name + '" size="' + str(self.get_size()) + '" format="' + self.format + '"> '
        data = data + self._value + "</" + tag + "> "
        return data

    def updateByElement(self, element):
        self._set_value(element._value)
        self.format = element.format


class indivector(indinamedobject):
    """
    The base class of all INDI vectors \n
    @ivar host : The hostname of the server that send the vector
    @type host : StringType
    @ivar port : The port on which the server send the vector
    @type port : IntType
    @ivar elements  : The list of L{indielement} objects contained in the vector
    @type elements  : list of L{indielement}
    @ivar _perm : The users read/write permissions for the  vector
    @type _perm : L{indipermissions}
    @ivar group : The INDI group the vector belongs to
    @type group : StringType
    @ivar _light : The StatusLED of the vector
    @type _light : L{indilight}
    @ivar timeout  : The timeout value. According to the indi white paper it is defined as follows:
    Each Property has a timeout value that specifies the worst-case time it might
    take to change the value to something else The Device may report changes to the timeout
    value depending on current device status. Timeout values give Clients a simple
    ability to detect dysfunctional Devices or broken communication and also gives them
    a way to predict the duration of an action for scheduling purposes as discussed later
    @type timeout  : StringType
    @ivar timestamp : The time when the vector was send out by the INDI server.
    @type timestamp : StringType
    @ivar device  : The INDI device the vector belongs to
    @type device  : StringType
    @ivar _message  : The L{indimessage} associated with the vector or B{None} if not present
    @type _message  : L{indimessage}
    """

    def __init__(self, attrs, tag):
        """
        @param attrs: The attributes of the XML version of the INDI vector.
        @type attrs: DictType
        @param tag: The XML tag of the vector (see L{indixmltag}).
        @type tag: L{indixmltag}
        """
        indinamedobject.__init__(self, attrs, tag)
        self.device = attrs.get('device', "").strip()
        self.timestamp = attrs.get('timestamp', "").strip()
        self.timeout = attrs.get('timeout', "").strip()
        self._light = indilight(attrs, tag)
        self.group = attrs.get('group', "").strip()
        self._perm = indipermissions(attrs.get('perm', "").strip())
        if 'message' in attrs:
            self._message = indimessage(attrs)
        else:
            self._message = None
        self.elements = []
        self.port = None
        self.host = None

    def get_message(self):
        """
        @return: The L{indimessage} associated with the vector, if there is any, B{None} otherwise
        @rtype: L{indimessage}
        """
        return self._message

    def _get_changed(self):
        """
        @return: C{True} if the objects XML data was changed since the last L{_get_changed} was called,
        C{False} otherwise.
        @rtype: BooleanType
        """
        changed = False
        for element in self.elements:
            if element._get_changed():
                changed = True
        return changed

    def to_dict(self):
        return {e.name: e._value for e in self.elements}

    def tell(self):
        """"
        Logs the most important parameters of the vector and its elements.
        @return: B{None}
        @rtype: NoneType
        """
        logging.info("INDIVector: %s %s %s %s %s" % (self.device, self.name, self.label, self.tag.get_type(), self._perm.get_text()))
        for element in self.elements:
            element.tell()

    def get_light(self):
        """
        Returns the L{indilight} of the vector
        @return: L{indilight} of the vector
        @rtype: L{indilight}
        """
        return self._light

    def get_permissions(self):
        """
        Returns the read/write permission of the vector
        @return: the read/write permission of the vector
        @rtype: L{indipermissions}
        """
        return self._perm

    def get_element(self, elementname):
        """
        Returns an element on this vector matching a given name.
        @param elementname: The name of the element requested
        @type elementname: 	StringType
        @return: The element requested
        @rtype: L{indielement}
        """
        for element in self.elements:
            if elementname == element.name:
                return element

    def get_first_element(self):
        """
        Returns the first element on this vector.
        @return: The first element
        @rtype: L{indielement}
        """
        return self.elements[0]

    def _wait_for_ok_general(self, checkinterval, timeout):
        """
        Wait until its state is C{Ok}. Usually this means to wait until the server has
        finished the operation requested by sending this vector.
        @param timeout: An exception will be raised if the no C{Ok} was received for longer than timeout
        since this method was called.
        @type timeout: FloatType
        @param checkinterval: The interval in which this method will check if the state is {Ok}
        @type checkinterval: FloatType
        @return: B{None}
        @rtype: NoneType
        """
        t = time.time()
        while not(self._light.is_ok()):
            time.sleep(checkinterval)
            if (time.time() - t) > timeout:
                raise Exception("timeout waiting for state to turn Ok " +
                                "devicename=" + self.device + " vectorname= " + self.name +
                                " " + str(timeout) + " " + str(time.time() - t))

    def wait_for_ok_timeout(self, timeout):
        """
        @param timeout: The time after which the L{_light} property of the object has to turn ok .
        @type timeout: FloatType
        @return: B{None}
        @rtype:  NoneType
        """
        checkinterval = 0.1
        if timeout < checkinterval:
            checkinterval = timeout
        self._wait_for_ok_general(checkinterval, timeout)

    def wait_for_ok(self):
        """
        Wait until its state is C{Ok}. Usually this means to wait until the server has
        finished the operation requested by sending this vector.
        @return: B{None}
        @rtype: NoneType
        """
        if float(self.timeout) == 0.0:
            timeout = 0.1
        else:
            timeout = float(self.timeout)
        checkinterval = 0.1
        if timeout < checkinterval:
            checkinterval = timeout
        self._wait_for_ok_general(checkinterval, timeout)

    def update(self, attrs, tag):
        indinamedobject.update(self, attrs, tag)
        self._check_writeable()
        self.timestamp = attrs.get('timestamp', "").strip()
        self.timeout = attrs.get('timeout', "").strip()
        self._light = indilight(attrs, tag)

    def get_xml(self, transfertype):
        tag = self.tag.get_xml(transfertype)
        data = "<" + tag + ' device="' + self.device + '" name="' + self.name + '"> '
        for element in self.elements:
            data = data + element.get_xml(transfertype)
        data = data + "</" + tag + "> "
        return data

    def updateByVector(self, vector):
        self.timestamp = vector.timestamp
        self.timeout = vector.timeout
        self._light = vector._light
        for oe in vector.elements:
            for e in self.elements:
                if e.name == oe.name:
                    e.updateByElement(oe)

    def getDevice(self):
        return self.device


class indiswitchvector(indivector):
    """
    a vector of switches \n
    @ivar rule: A rule defining which states of switches of the vector are allowed. possible values are:
            - C{OneOfMany} Exactly one of the switches in the vector has to be C{On} all others have to be C{Off}
            - C{AtMostOne}  At most one of the switches in the vector can to be C{On} all others have to be C{Off}
            - C{AnyOfMany} Any switch in the vector may have any state
    @type rule: StringType
    """

    def __init__(self, attrs, tag):
        indivector.__init__(self, attrs, tag)
        self.rule = attrs.get('rule', "").strip()

    def tell(self):
        logging.info("INDISwitchVector: %s %s %s %s %s" % (self.device, self.name, self.label, self.tag.get_type(), self.rule))
        for element in self.elements:
            element.tell()

    def set_by_element_name(self, element_name, is_active):
        if self.rule == "OneOfMany":
            assert(is_active)
            self.set_one_of_many_by_element_name(element_name)
        else:
            self.set_single_element_by_name(element_name, is_active)

    def set_by_element_label(self, element_label, is_active):
        if self.rule == "OneOfMany":
            assert(is_active)
            self.set_one_of_many_by_element_label(element_label)
        else:
            self.set_single_element_by_label(element_label, is_active)



    def set_single_element_by_name(self, element_name, is_active=True):
        """
        Sets a single L{indiswitch} elements of this vector to desired value.
        If no matching one is found, an error is thrown
        @param element_name: The INDI name of the Switch to be set to C{On}
        @type element_name: StringType
        @return: B{None}
        @rtype: NoneType
        """
        found = False
        for element in self.elements:
            if element.name == element_name:
                if found:
                    raise RuntimeError(
                        f"Element with name {element_name} is present more than once")
                element.set_active(is_active)
                found = True
        if not found:
            raise RuntimeError(f"There is no element with name {element_name} in indiswitch")

    def set_one_of_many_by_element_name(self, element_name):
        """
        Sets all L{indiswitch} elements of this vector to C{Off}. And sets the one who's name property matches L{element_name}
        to C{On} . If no matching one is found, an error is thrown
        @param element_name: The INDI Label of the Switch to be set to C{On}
        @type element_name: StringType
        @return: B{None}
        @rtype: NoneType
        """
        found = False
        for element in self.elements:
            if element.name == element_name:
                if found:
                    raise RuntimeError(
                        f"Element with name {element_name} is present more than once")
                found = True
        if not found:
            raise RuntimeError(f"Cannot set indiswitch element by name {element_name}")
        for element in self.elements:
            element.set_active(False)
            if element.name == element_name:
                element.set_active(True)

    def set_single_element_by_label(self, element_label, is_active=True):
        """
        Sets a single L{indiswitch} elements of this vector to desired value.
        If no matching one is found, an error is thrown
        @param element_name: The INDI name of the Switch to be set to C{On}
        @type element_name: StringType
        @return: B{None}
        @rtype: NoneType
        """
        found = False
        for element in self.elements:
            if element.label == element_label:
                if found:
                    raise RuntimeError(
                        f"Element with label {element_label} is present more than once")
                element.set_active(is_active)
                found = True
        if not found:
            raise RuntimeError(f"There is no element with label {element_label} in indiswitch")


    def set_one_of_many_by_element_label(self, element_label):
        """
        Sets all L{indiswitch} elements of this vector to C{Off}. And sets the one who's label property matches L{element_name}
        to C{On} . If no matching one is found, an error is thrown
        @param element_name: The INDI Label of the Switch to be set to C{On}
        @type element_name: StringType
        @return: B{None}
        @rtype: NoneType
        """
        found = False
        for element in self.elements:
            if element.label == element_label:
                if found:
                    raise RuntimeError(
                        f"Element with label {element_label} is present more than once")
                found = True
        if not found:
            raise RuntimeError(f"Cannot set indiswitch element by label {element_label}")
        for element in self.elements:
            element.set_active(False)
            if element.label == element_label:
                element.set_active(True)

    def get_active_element(self):
        """
        @return: The first active (C{On}) element, B{None} if there is none
        @rtype: L{indiswitch}
        """
        for element in self.elements:
            if element.get_active():
                return element
        return None

    def set_active_index(self, index):
        """
        Turns the switch with index L{index} to C{On} and all other switches of this vector to C{Off}.
        @param index: the index of the switch to turned C{On} exclusively
        @type index: IntType
        @return: B{None}
        @rtype: NoneType
        """
        for i, element in enumerate(self.elements):
            if i == index:
                element.set_active(True)
            else:
                element.set_active(False)

    def get_active_index(self):
        """
        @return:  the index of the first switch in the Vector that is C{On}
        @rtype: IntType
        """
        for i, element in enumerate(self.elements):
            if element.get_active():
                return i
        return None


class indinumbervector(indivector):
    """A vector of numbers """


class indiblobvector(indivector):
    """A vector of BLOBs """


class inditextvector(indivector):
    """A vector of texts"""


class indilightvector(indivector):
    """A vector of lights """

    def __init__(self, attrs, tag):
        self.tag = tag
        newattrs = attrs.copy()
        newattrs.update({"perm": 'ro'})
        indivector.__init__(self, newattrs, self.tag)

    def update(self, attrs):
        newattrs = attrs.copy()
        newattrs.update({"perm": "ro"})
        indivector.update(self, newattrs, self.tag)


class indimessage(indiobject):
    """
    a text message.
    @ivar device:  The INDI device the message belongs to.
    @type device: StringType
    @ivar timestamp: The time when the message was send out by the INDI server
    @type timestamp: StringType
    @ivar _value: The INDI message send by the server
    @type _value: StringType
    """

    def __init__(self, attrs):
        """
        @param attrs: The attributes of the XML version of the INDI message.
        @type attrs: DictType
        """
        tag = indixmltag(False, False, True, None, inditransfertypes.inew)
        indiobject.__init__(self, attrs, tag)
        self.device = attrs.get('device', "").strip()
        self.timestamp = attrs.get('timestamp', "").strip()
        self._value = attrs.get('message', "").strip()

    def tell(self):
        """
        Log the message to the screen
        @return: B{None}
        @rtype: NoneType
        """
        logging.info("INDImessage: %s %s" % (self.device, self.get_text()))

    def get_text(self):
        """
        @return: A text representing the message received
        @rtype: StringType
        """
        return self._value

    def is_valid(self):
        """
        @return: C{True} if the message is valid.
        @rtype: StringType
        """
        return self._value != ""

class device(ABC):
    """
    Horrible mix of various MMTO classes        
    """

    def __init__(self, name, config=None):
        """
        Arguments:
        loop: the asyncio event loop
        config: the configurable info from ConfigParser
        name: Name of the device defaulting to name of the class
        """
        self.device_name = name

        # Factory that will turn received xml into proper python objects
        self._factory = _indiobjectfactory()

        # parsing tools
        self.expat = xml.parsers.expat.ParserCreate()
        self.expat.StartElementHandler = self._start_element
        self.expat.EndElementHandler = self._end_element
        self.expat.CharacterDataHandler = self._char_data
        self.expat.Parse('<?xml version="1.5" encoding="UTF-8"?> <doc>', 0)
        self.current_vector = None
        self.current_element = None
        self.current_xml_str = []

        # vector/property handlers
        self.custom_element_handler_list = []
        self.custom_vector_handler_list = []
        self.blob_def_handler = self._default_def_handler
        self.number_def_handler = self._default_def_handler
        self.switch_def_handler = self._default_def_handler
        self.text_def_handler = self._default_def_handler
        self.blob_def_handler = self._default_def_handler
        self.light_def_handler = self._default_def_handler
        self.message_handler = self._default_message_handler
        self.timeout_handler = self._default_timeout_handler

        # Dicitonary of Property vector for the current device, each having multiple properties
        self.property_vectors = {}
        self.property_vectors_lock = threading.Lock()
        self.config = config
        self.timer_queue = asyncio.Queue()

    def __getitem__(self, name: str):
        """
        Retrieve IVectorProperty that has been
        registered with the device.Set method.
        """
        return self.IUFind(name)

    def name(self):
        return self.device_name

    @property
    def device(self):
        return self.device_name

    def __repr__(self):
        return f"<{self.name()}>"

    def add_custom_vector_handler(self, handler):
        """
        Adds a custom handler function for an L{indivector}, the handler will be called each time the vector is received.
        Furthermore this method will call the hander once. If the vector has not been received yet, this function will wait
        until the vector is received before calling the handler function. If the vector does not exist this method will
        B{not} return.
        @param handler:  The handler to be called.
        @type handler: L{indi_custom_vector_handler}
        @return: The handler given in the parameter L{handler}
        @rtype: L{indi_custom_vector_handler}
        """
        handler.indi = self
        self.custom_vector_handler_list.append(handler)
        vector = self.get_vector(handler.devicename, handler.vectorname)
        handler.configure(vector)
        handler.indi_object_change_notify(vector)
        return handler

    def _default_message_handler(self, message, indi):
        """
        Called whenever an INDI message has been received from the server.
        C{timeout} since the request was issued. May be replaced by a custom one see L{set_message_handler}
        @param message: The indimessage received
        @type message: L{indimessage}
        @param indi : This parameter will be equal to self. It still make sense as external timeout handlers might need it.
        @type indi : L{indiclient}
        @return: B{None}
        @rtype: NoneType
        """
        logging.info(f"Got message by host: {indi.host} :")
        message.tell()


    def _default_def_handler(self, vector, indi):
        """
        Called whenever an indivector was received with an C{def*vector} tag. This
        means that the INDI driver has called an C{IDDef*} function and thus defined a INDI vector.
        It will be called only once for each element, even if more than C{def*vector}
        signals are received. May be replaced by a custom one see L{set_def_handlers}
        @param vector: The vector received.
        @type vector: L{indivector}
        @param indi : The L{indiclient} instance that received the L{indivector} from the server
        @type indi : L{indiclient}
        @return: B{None}
        @rtype: NoneType
        """
        pass

    def _default_timeout_handler(self, devicename, vectorname, indi):
        """
        Called whenever an indielement has been requested but was not received for a time longer than
        C{timeout} since the request was issued. May be replaced by a custom handler see L{set_timeout_handler}
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname: The name of the Indivector
        @type vectorname: StringType
        @param indi : This parameter will be equal to self. It still make sense as external timeout handlers might need it.
        @type indi : indiclient
        @return: B{None}
        @rtype: NoneType
        """
        logging.warning(f"Timeout: {devicename} {vectorname}")

    def _element_received(self, vector, element):
        """ Called during the L{process_events} method each time an INDI element has been received
        @param vector: The vector containing the element that has been received
        @type vector: indivector
        @param element:  The element that has been received
        @type element: indielement
        @return: B{None}
        @rtype: NoneType
        """
        for handler in self.custom_element_handler_list:
            if ((handler.vectorname == vector.name) and (handler.elementname == element.name) and
                    (handler.devicename == vector.device)):
                handler.indi_object_change_notify(vector, element)

    def _vector_received(self, vector):
        """ Called during the L{process_events} method each time an indivector element has been received
        @param vector: The vector that has been received
        @type vector: indivector
        @return: B{None}
        @rtype: NoneType
        """
        for handler in self.custom_vector_handler_list:
            if ((handler.vectorname == vector.name) and (handler.devicename == vector.device)):
                handler.indi_object_change_notify(vector)

    def process_vector(self, vector):
        """
        """
        try:
            if vector.is_valid:
                if vector.device!=self.device_name:
                    return
                if vector.tag.is_message():
                    # vector is in fact an indimessage (historical reasons, marked for change)
                    self.message_handler(vector, self)
                if vector.tag.is_vector():
                    self._vector_received(vector)
                    for element in vector.elements:
                        self._element_received(vector, element)
                if vector.tag.get_transfertype() == inditransfertypes.idef:
                    # In that case, we are not supposed to know the vector !
                    # TODO TN not clear, I would rather force replacing vector
                    with self.property_vectors_lock:
                        for vec_name, vec in self.property_vectors.items():
                            if (vec.name == vector.name) and (
                                    vec.device == vector.device):
                                #self.property_vectors[vec_name] = vector
                                return
                    if vector.tag.get_type() == "BLOBVector":
                        self.blob_def_handler(vector, self)
                    if vector.tag.get_type() == "TextVector":
                        self.text_def_handler(vector, self)
                    if vector.tag.get_type() == "NumberVector":
                        self.number_def_handler(vector, self)
                    if vector.tag.get_type() == "SwitchVector":
                        self.switch_def_handler(vector, self)
                    if vector.tag.get_type() == "LightVector":
                        self.light_def_handler(vector, self)
                    try:
                        with self.property_vectors_lock:
                            self.property_vectors[vector.name].updateByVector(
                                vector)
                    except KeyError:
                        with self.property_vectors_lock:
                            self.property_vectors[vector.name] = vector
            else:
                logging.warning("Received bogus INDIVector")
                try:
                    vector.tell()
                    raise Exception
                    vector.tell()
                except Exception as e:
                    logging.error(f"Error logging bogus INDIVector: {e}")
                    raise Exception
        except Exception as e:
            raise RuntimeError(f"Error while trying to process vector from indiserver: {e}")

    def _char_data(self, data):
        """Char data handler for expat parser. For details (see
        U{http://www.python.org/doc/current/lib/expat-example.html})
        @param data: The data contained in the INDI element
        @type data: StringType
        @return: B{None}
        @rtype: NoneType
        """
        if self.current_element is None:
            return None
        if self.current_vector is None:
            return None
        self.current_xml_str += data

    def _end_element(self, name):
        """End of XML element handler for expat parser. For details (see
        U{http://www.python.org/doc/current/lib/expat-example.html})
        @param name : The name of the XML object
        @type name : StringType
        @return: B{None}
        @rtype: NoneType
        """
        if self.current_vector is None:
            return None
        self.current_vector.host = self.indi_client.host
        self.current_vector.port = self.indi_client.port
        if self.current_element is not None:
            if self.current_element.tag.get_initial_tag() == name:
                string_currentData = "".join(self.current_xml_str).replace('\\n', '').strip()
                self.current_element._set_value(string_currentData)
                self.current_vector.elements.append(self.current_element)
                self.current_element = None
                self.current_xml_str = None
        if self.current_vector.tag.get_initial_tag() == name:
            self.process_vector(self.current_vector)
            self.current_vector = None

    def _start_element(self, name, attrs):
        """
        Start XML element handler for expat parser. For details (see
        U{http://www.python.org/doc/current/lib/expat-example.html})
        @param name : The name of the XML object
        @type name : StringType
        @param attrs : The attributes of the XML object
        @type attrs : DictType
        @return: B{None}
        @rtype: NoneType
        """
        obj = self._factory.create(name, attrs)
        if obj is None:
            return
        if 'message' in attrs:
            logging.warning(
                f"Legacy type of message received from indi: {name, attrs}")
        if obj.tag.is_vector():
            if obj.tag.get_transfertype() in (inditransfertypes.idef, inditransfertypes.iset):
                self.current_vector = obj
        if self.current_vector is not None:
            if obj.tag.is_element():
                if self.current_vector.tag.get_transfertype() in (inditransfertypes.idef, inditransfertypes.iset):
                    self.current_element = obj
        self.current_xml_str = []

    async def parse_xml_str(self, xml_str):
        """
        Build properties from a skeleton File.. 
        args:
            skelfile: string path to skeleton
            file.
        """
        if len(xml_str)>0:
            self.expat.Parse(xml_str, 0)
        await asyncio.sleep(0)
        # self.current_xml_str += xml_str.decode()
        # try:
        #     xml = etree.fromstring(self.current_xml_str)
        # except lxml.etree.XMLSyntaxError as e:
        #     logging.error(f"Current xml is {self.current_xml_str}")
        #     return #string has not been fully received
        # # reset current xml
        # self.current_xml_str = ''
        # vector = self._factory.create(xml.tag, xml.attrib)
        # if vector is None:
        #     return
        # if 'message' in xml.attrib:
        #     logging.warning(f"Legacy type of message received from indi: {xml_str.decode()}")
        # if vector.tag.is_vector():
        #     if vector.device != self.device_name:
        #         return
        #     if vector.tag.get_transfertype() in (inditransfertypes.idef, inditransfertypes.iset):
        #         self.process_vector(vector)
        # # if self.current_vector is not None:
        # #     if obj.tag.is_element():
        # #         if self.current_vector.tag.get_transfertype() in (inditransfertypes.idef, inditransfertypes.iset):
        # #             self.current_element = obj
        # # properties = []
        # # for prop in xml.getchildren():
        # #     att = prop.attrib
        # #     att.update({'value': prop.text.strip()})
        # #     properties.append(att)
        # # self.process_vector(xml.tag, xml.attrib, properties)
        await asyncio.sleep(0)

    def send_vector(self, vector):
        """
        Sends an INDI vector to the INDI server.
        @param vector:  The INDI vector to be send
        @type vector: indivector
        @return: B{None}
        @rtype: NoneType
        """
        if not vector.tag.is_vector():
            raise RuntimeError(f"Attempt to set vector with wrong tag: {vector.tag}")
        data = vector.get_xml(inditransfertypes.inew)
        self.indi_client.xml_to_indiserver(data)
        vector._light._set_value("Busy")

    def _get_vector(self, vectorname):
        try:
            with self.property_vectors_lock:
                return self.property_vectors[vectorname]
        except KeyError:
            return None

    def _get_vector_dict(self, vectorname):
        try:
            with self.property_vectors_lock:
                return self.property_vectors[vectorname].to_dict()
        except KeyError:
            return None

    def get_vector(self, vectorname, timeout=None):
        """
        Returns an L{indivector} matching the given L{devicename} and L{vectorname}
        This method will wait until it has been received. In case the vector doesn't exists this
        routine will never return.
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @return: The L{indivector} found
        @rtype: L{indivector}
        """
        started = time.time()
        if timeout is None:
            timeout = self.timeout
        vector = None
        while vector is None:
            vector = self._get_vector(vectorname)
            if 0 < timeout < time.time() - started:
                self.logger.debug(f"device: Timeout while waiting for "
                                  f"property status {vectorname} for device "
                                  f"{self.device_name}")
                raise RuntimeError(f"Timeout error while waiting for property "
                                   f"{vectorname}")
            time.sleep(0.01)
        return vector

    def get_vector_dict(self, vectorname, timeout=None):
        """
        Returns an L{indivector} matching the given L{devicename} and L{vectorname}
        This method will wait until it has been received. In case the vector doesn't exists this
        routine will never return.
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @return: The L{indivector} found
        @rtype: L{indivector}
        """
        started = time.time()
        if timeout is None:
            timeout = self.timeout
        vector_dict = None
        while vector_dict is None:
            vector_dict = self._get_vector_dict(vectorname)
            if 0 < timeout < time.time() - started:
                self.logger.debug(f"device: Timeout while waiting for "
                                  f"property status {vectorname} for device "
                                  f"{self.device_name}")
                raise RuntimeError(f"Timeout error while waiting for property "
                                   f"{vectorname}")
            time.sleep(0.01)
        return vector_dict

    def get_element(self, vectorname, elementname):
        """
        Returns an L{indielement} matching the given L{devicename} and L{vectorname}
        This method will wait until it has been received. In case the vector doesn't exists this
        routine will never return.
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param elementname:  The name of the element
        @type elementname: StringType
        @return: The element found
        @rtype: L{indielement}
        """
        vector = self.get_vector(vectorname)
        for i, element in enumerate(vector.elements):
            if elementname == element.name:
                return element

    def set_and_send_text(self, vectorname, elementname, text):
        """
        Sets the value of an element by a text, and sends it to the server
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param elementname:  The name of the element
        @type elementname: StringType
        @param text:  The value to be set.
        @type text: StringType
        @return: The vector containing the element that was just sent.
        @rtype: L{indivector}
        """
        vector = self.get_vector(vectorname)
        if vector is not None:
            vector.get_element(elementname).set_text(text)
            self.send_vector(vector)
        return vector

    def set_and_send_bool(self, vectorname, elementname, state):
        """
        Sets the value of of an indi element by a boolean, and sends it to the server
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param elementname:  The name of the element
        @type elementname: StringType
        @param state:  The state to be set.
        @type state: BooleanType
        @return: The vector containing the element that was just sent.
        @rtype: L{indivector}
        """
        vector = self.get_vector(vectorname)
        if vector is not None:
            vector.get_element(elementname).set_active(state)
            self.send_vector(vector)
        return vector

    def set_and_send_float(self, vectorname, elementname, number):
        """
        Sets the value of an indi element by a floating point number, and sends it to the server
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param elementname:  The name of the element
        @type elementname: StringType
        @param number: The number to be set.
        @type number: FloatType
        @return: The vector containing the element that was just sent.
        @rtype: L{indivector}
        """
        vector = self.get_vector(vectorname)
        if vector is not None:
            vector.get_element(elementname).set_float(number)
            self.send_vector(vector)
        return vector

    def set_and_send_switchvector_by_element_name(self, vectorname, element_name, is_active=True):
        """
        Sets all L{indiswitch} elements in this vector to C{Off}. And sets the one matching the given L{element_name}
        to C{On}
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param element_name: The INDI Label of the Switch to be set to C{On}
        @type element_name: StringType
        @return: The vector that that was just sent.
        @rtype: L{indivector}
        """
        vector = self.get_vector(vectorname)
        if vector is not None:
            vector.set_by_element_name(element_name, is_active)
            self.send_vector(vector)
        else:
            raise RuntimeError(f"Indi switchvector {vectorname} does not exist")
        return vector

    def get_float(self, vectorname, elementname):
        """
        Returns a floating point number representing the value of the element requested.
        The element must be an L{indinumber}.
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param elementname:  The name of the element
        @type elementname: StringType
        @return: the value of the element
        @rtype: FloatType
        """
        vector = self.get_vector(vectorname)
        try:
            num = vector.get_element(elementname).get_float()
        except Exception as e:
            logging.error("Can't get float from bogus vector: %s" % e)
            num = None
        return num

    def get_text(self, vectorname, elementname):
        """
        Returns a text representing the value of the element requested.
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param elementname:  The name of the element
        @type elementname: StringType
        @return: the value of the element
        @rtype: StringType
        """
        vector = self.get_vector(vectorname)
        try:
            text = vector.get_element(elementname).get_text()
        except Exception as e:
            logging.error("Can't get text from bogus vector: %s" % e)
            text = None
        return text

    def get_bool(self, vectorname, elementname):
        """
        Returns Boolean representing the value of the element requested.
        The element must be an L{indiswitch}
        @param devicename:  The name of the device
        @type devicename: StringType
        @param vectorname:  The name of the vector
        @type vectorname: StringType
        @param elementname:  The name of the element
        @type elementname: StringType
        @return: the value of the element
        @rtype: BooleanType
        """
        vector = self.get_vector(vectorname)
        try:
            bol = vector.get_element(elementname).get_active()
        except Exception as e:
            logging.error("Can't get bool from bogus vector: %s" % e)
            bol = None
        return bol
