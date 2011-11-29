#!/usr/bin/env python2

import struct
import base64
import logging
import datetime

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from datatypes import *
from dictionary import dictionary

class Record(object):
    def __init__(self, type=None):
        if type:
            self.type = type

    def to_bytes(self):
        """
        >>> Record(0xff).to_bytes()
        '\\xff'
        """
        return struct.pack('<B', self.type)


    @classmethod
    def parse(cls, fp):
        if cls != Record:
            return cls()
        root = []
        records = root
        parents = []
        last_el = None
        type = True
        while type:
            type = fp.read(1)
            if type:
                type = struct.unpack('<B', type)[0]
                if type in __records__:
                    log.debug('%s found' % __records__[type].__name__)
                    obj = __records__[type].parse(fp)
                    if isinstance(obj, EndElementRecord):
                        if len(parents) > 0:
                            records = parents.pop()
                        #records.append(obj)
                    elif isinstance(obj, Element):
                        last_el = obj
                        records.append(obj)
                        parents.append(records)
                        obj.childs = []
                        records = obj.childs
                    elif isinstance(obj, Attribute) and last_el:
                        last_el.attributes.append(obj)
                    else:
                        records.append(obj)
                    log.debug('Value: %s' % str(obj))
                elif type-1 in __records__:
                    log.debug('%s with end element found (0x%x)' %
                            (__records__[type-1].__name__, type))
                    records.append(__records__[type-1].parse(fp))
                    #records.append(EndElementRecord())
                    last_el = None
                    if len(parents) > 0:
                        records = parents.pop()
                else:
                    log.warn('type 0x%x not found' % type)

        return root

class Element(Record):
    pass

class Attribute(Record):
    pass

class EndElementRecord(Element):
    type = 0x01

class CommentRecord(Record):
    type = 0x02
    
    def __init__(self, comment, *args, **kwargs):
        self.comment = comment

    def to_bytes(self):
        """
        >>> CommentRecord('test').to_bytes()
        '\\x02\\x04test'
        """
        string = Utf8String(self.comment)

        return (super(CommentRecord, self).to_bytes() + 
                string.to_bytes())

    def __str__(self):
        """
        >>> str(CommentRecord('test'))
        '<!-- test -->'
        """
        return '<!-- %s -->' % self.comment

    @classmethod
    def parse(cls, fp):
        data = Utf8String.parse(fp).value
        return cls(data)

class ArrayRecord(Record):
    type = 0x03

    datatypes = {
            0xB5 : ('BoolTextWithEndElement', 1, '?'),
            0x8B : ('Int16TextWithEndElement', 2, 'h'),
            0x8D : ('Int32TextWithEndElement', 4, 'i'),
            0x8F : ('Int64TextWithEndElement', 8, 'q'),
            0x91 : ('FloatTextWithEndElement', 4, 'f'),
            0x93 : ('DoubleTextWithEndElement', 8, 'd'),
            0x95 : ('DecimalTextWithEndElement', 16, ''),
            0x97 : ('DateTimeTextWithEndElement', 8, ''),
            0xAF : ('TimeSpanTextWithEndElement', 8, ''),
            0xB1 : ('UuidTextWithEndElement', 16, ''),
            }

    def __init__(self, element, recordtype, data):
        self.element = element
        self.recordtype = recordtype
        self.count = len(data)
        self.data = data

    def to_bytes(self):
        """
        >>> ArrayRecord(ShortElementRecord('item'), 0x8D, ['\\x01\\x00\\x00\\x00', '\\x02\\x00\\x00\\x00', '\\x03\\x00\\x00\\x00']).to_bytes()
        '\\x03@\\x04item\\x01\\x8d\\x03\\x01\\x00\\x00\\x00\\x02\\x00\\x00\\x00\\x03\\x00\\x00\\x00'
        """
        bytes = super(ArrayRecord, self).to_bytes()
        bytes += self.element.to_bytes()
        bytes += EndElementRecord().to_bytes()
        bytes += struct.pack('<B', self.recordtype)[0]
        bytes += MultiByteInt31(self.count).to_bytes()
        for data in self.data:
            if type(data) == str:
                bytes += data
            else:
                bytes += data.to_bytes()

        return bytes

    @classmethod
    def parse(cls, fp):
        element = struct.unpack('<B', fp.read(1))[0]
        element = __records__[element].parse(fp)
        recordtype = struct.unpack('<B', fp.read(1))[0]
        count = MultiByteInt31.parse(fp).value
        data = []
        for i in range(count):
            data.append(__records__[recordtype-1].parse(fp))
        return cls(element, recordtype, data)

    def __str__(self):
        """
        >>> str(ArrayRecord(ShortElementRecord('item'), 0x8D, [Int32TextRecord(1),Int32TextRecord(2),Int32TextRecord(3)]))
        '<item >1</item><item >2</item><item >3</item>'
        """
        string = ''
        for data in self.data:
            string += str(self.element)
            string += str(data)
            string += '</%s>' % self.element.name

        return string

            
class ZeroTextRecord(Record):
    type = 0x80

    def __str__(self):
        return '0'

    @classmethod
    def parse(cls, fp):
        return cls()

class OneTextRecord(Record):
    type = 0x82

    def __str__(self):
        return '1'

    @classmethod
    def parse(cls, fp):
        return cls()

class FalseTextRecord(Record):
    type = 0x84

    def __str__(self):
        return 'false'

    @classmethod
    def parse(cls, fp):
        return cls()

class TrueTextRecord(Record):
    type = 0x86

    def __str__(self):
        return 'true'

    @classmethod
    def parse(cls, fp):
        return cls()

class Int8TextRecord(Record):
    type = 0x88

    def __init__(self, value):
        self.value = value

    def to_bytes(self):
        return super(Int8TextRecord, self).to_bytes() + struct.pack('<b',
                self.value)[0]

    def __str__(self):
        return str(self.value)

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<b', fp.read(1))[0])

class Int16TextRecord(Int8TextRecord):
    type = 0x8A

    def to_bytes(self):
        return super(Int16TextRecord, self).to_bytes() + struct.pack('<h',
                self.value)[0]

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<h', fp.read(2))[0])

class Int32TextRecord(Int8TextRecord):
    type = 0x8C

    def to_bytes(self):
        return super(Int32TextRecord, self).to_bytes() + struct.pack('<i',
                self.value)[0]

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<i', fp.read(4))[0])

class Int64TextRecord(Int8TextRecord):
    type = 0x8E

    def to_bytes(self):
        return super(Int64TextRecord, self).to_bytes() + struct.pack('<q',
                self.value)[0]

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<q', fp.read(8))[0])

class UInt64TextRecord(Int64TextRecord):
    type = 0xB2

    def to_bytes(self):
        return super(UInt64TextRecord, self).to_bytes() + struct.pack('<Q',
                self.value)[0]

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<Q', fp.read(8))[0])

class BoolTextRecord(Record):
    type = 0xB4

    def __init__(self, value):
        self.value = value

    def to_bytes(self):
        return (struct.pack('<B', self.type) + 
                struct.pack('<B', 1 if self.value else 0))

    def __str__(self):
        return str(self.value)

    @classmethod
    def parse(cls, fp):
        value = True if struct.unpack('<B', fp.read(1))[0] == 1 else False
        return cls(value)

class UnicodeChars8TextRecord(Record):
    type = 0xB6

    def __init__(self, string):
        if isinstance(string, unicode):
            self.value = string
        else:
            self.value = unicode(string)

    def to_bytes(self):
        """
        >>> UnicodeChars8TextRecord('abc').to_bytes()
        '\\xb6\\x06a\\x00b\\x00c\\x00'
        >>> UnicodeChars8TextRecord(u'abc').to_bytes()
        '\\xb6\\x06a\\x00b\\x00c\\x00'
        """
        data = self.value.encode('utf-16')[2:] # skip bom
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<B', len(data))
        bytes += data
        return bytes

    def __str__(self):
        return self.value

    @classmethod
    def parse(cls, fp):
        """
        >>> import StringIO
        >>> fp = StringIO.StringIO('\\x06a\\x00b\\x00c\\x00')
        >>> str(UnicodeChars8TextRecord.parse(fp))
        'abc'
        """
        ln = struct.unpack('<B', fp.read(1))[0]
        data = fp.read(ln)
        return cls(data.decode('utf-16'))

class UnicodeChars16TextRecord(UnicodeChars8TextRecord):
    type = 0xB8

    def to_bytes(self):
        data = self.value.encode('utf-16')[2:] # skip bom
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<H', len(data))
        bytes += data
        return bytes

    def __str__(self):
        return self.value

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<H', fp.read(1))[0]
        data = fp.read(ln)
        return cls(data.decode('utf-16'))

class UnicodeChars32TextRecord(UnicodeChars8TextRecord):
    type = 0xBA

    def to_bytes(self):
        data = self.value.encode('utf-16')[2:] # skip bom
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<I', len(data))
        bytes += data
        return bytes

    def __str__(self):
        return self.value

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<I', fp.read(1))[0]
        data = fp.read(ln)
        return cls(data.decode('utf-16'))

class QNameDictionaryTextRecord(Record):
    type = 0xBC

    def __init__(self, prefix, index):
        self.prefix = prefix
        self.index = index

    def to_bytes(self):
        """
        >>> QNameDictionaryTextRecord('b', 2).to_bytes()
        '\\xbc\\x01\\x00\\x00\\x02'
        """
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<B', ord(self.prefix) - ord('a'))
        bytes += struct.pack('<BBB', 
                        (self.index >> 16) & 0xFF,
                        (self.index >>  8) & 0xFF,
                        (self.index >>  0) & 0xFF)
        return bytes
    
    def __str__(self):
        """
        >>> str(QNameDictionaryTextRecord('b', 2))
        'b:Envelope'
        """
        return '%s:%s' % (self.prefix, dictionary[self.index])

    @classmethod
    def parse(cls, fp):
        """
        >>> import StringIO
        >>> fp = StringIO.StringIO('\\x01\\x00\\x00\\x02')
        >>> str(QNameDictionaryTextRecord.parse(fp))
        'b:Envelope'
        """
        prefix = chr(struct.unpack('<B', fp.read(1))[0] + ord('a'))
        idx = struct.unpack('<BBB', fp.read(3))
        index = idx[0] << 16 | idx[1] << 8 | idx[2]
        return cls(prefix, index)


class FloatTextRecord(Record):
    type = 0x90

    def __init__(self, value):
        self.value = value

    def to_bytes(self):
        bytes = super(FloatTextRecord, self).to_bytes()
        bytes += struct.pack('<f', self.value)
        return bytes

    def __str__(self):
        """
        >>> str(FloatTextRecord(float('-inf')))
        '-INF'
        >>> str(FloatTextRecord(-0.0))
        '-0'
        >>> str(FloatTextRecord(1.337))
        '1.337'
        """
        try:
            if self.value == int(self.value):
                return '%.0f' % self.value
            else: 
                return str(self.value)
        except:
            return str(self.value).upper()


    @classmethod
    def parse(cls, fp):
        value = struct.unpack('<f', fp.read(4))[0]
        return cls(value)

class DoubleTextRecord(FloatTextRecord):
    type = 0x92

    def __init__(self, value):
        self.value = value

    def to_bytes(self):
        bytes = super(FloatTextRecord, self).to_bytes()
        bytes += struct.pack('<d', self.value)
        return bytes

    def __str__(self):
        """
        >>> str(DoubleTextRecord(float('-inf')))
        '-INF'
        >>> str(DoubleTextRecord(-0.0))
        '-0'
        >>> str(DoubleTextRecord(1.337))
        '1.337'
        """
        return super(DoubleTextRecord, self).__str__()

    @classmethod
    def parse(cls, fp):
        value = struct.unpack('<d', fp.read(8))[0]
        return cls(value)

class DecimalTextRecord(Record):
    type = 0x94

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def to_bytes(self):
        return (super(DecimalTextRecord, self).to_bytes() + 
                self.value.to_bytes())

    @classmethod
    def parse(cls, fp):
        value = Decimal.parse(fp)
        return cls(value)

class DatetimeTextRecord(Record):
    type = 0x96

    def __init__(self, value, tz):
        self.value = value
        self.tz = tz

    def __str__(self):
        tick = self.value
        dt = (datetime.datetime(1, 1, 1) + 
                datetime.timedelta(microseconds=ticks/10))
        return str(dt)

    def to_bytes(self):
        bytes  = super(DateTimeTextRecord, self).to_bytes()
        bytes += struct.pack('<Q', 
                (self.tz & 3) | (self.value & 0x1FFFFFFFFFFFFFFF) << 2)

        return bytes

    @classmethod
    def parse(cls, fp):
        data = struct.unpack('<Q', fp.read(8))[0]
        tz = data & 3
        value = data >> 2

        return DatetimeTextRecord(value, tz)

class Char8TextRecord(Utf8String):
    type = 0x98

class Char16TextRecord(Utf8String):
    type = 0x9A

    def to_bytes(self):
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<H', len(self.value))
        bytes += self.value

        return bytes

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<H', fp.read(2))[0]
        value = fp.read(ln)
        return cls(value)

class Char32TextRecord(Utf8String):
    type = 0x9C

    def to_bytes(self):
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<I', len(self.value))
        bytes += self.value

        return bytes

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<I', fp.read(4))[0]
        value = fp.read(ln)
        return cls(value)

class UniqueIdTextRecord(Record):
    type = 0xAC

    def __init__(self, uuid):
        if isinstance(uuid, list) or isinstance(uuid, tuple):
            self.uuid = uuid
        else:
            uuid = uuid.split('-')
            tmp = uuid[0:3]
            tmp.append(uuid[3][0:2])
            tmp.append(uuid[3][2:])
            tmp.append(uuid[4][0:2])
            tmp.append(uuid[4][2:4])
            tmp.append(uuid[4][4:6])
            tmp.append(uuid[4][6:8])
            tmp.append(uuid[4][8:10])
            tmp.append(uuid[4][10:])
            
            self.uuid = [int(s,16) for s in tmp]

    def to_bytes(self):
        """
        #>>> UniqueIdTextRecord('33221100-5544-7766-8899-aabbccddeeff').to_bytes()
        '\\x33\\x22\\x11\\x00\\x55\\x44\\x77\\x66\\x88\\x99\\xaa\\xbb\\xcc\\xdd\\xee\\xff'
        """
        bytes = super(UniqueIdTextRecord, self).to_bytes()
        bytes += struct.pack('<IHHBBBBBBBB', *self.uuid)

        return bytes

    def __str__(self):
        return 'urn:uuid:%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x' % self.uuid

    @classmethod
    def parse(cls, fp):
        uuid = struct.unpack('<IHHBBBBBBBB', fp.read(16))
        return cls(uuid)

class UuidTextRecord(UniqueIdTextRecord):
    type = 0xB0

class Bytes8TextRecord(Utf8String):
    type = 0x9E

    def __init__(self, data):
        self.value = data

    def __str__(self):
        return base64.b64encode(self.value)

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<B', fp.read(1))[0]
        data = struct.unpack('%ds' % ln, fp.read(ln))[0]
        return cls(data)

class Bytes16TextRecord(Utf8String):
    type = 0xA0

    def __init__(self, data):
        self.value = data

    def __str__(self):
        return base64.b64encode(self.value)

    def to_bytes(self):
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<H', len(self.value))
        bytes += self.value

        return bytes

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<H', fp.read(2))[0]
        data = struct.unpack('%ds' % ln, fp.read(ln))[0]
        return cls(data)

class Bytes32TextRecord(Utf8String):
    type = 0xA2

    def __init__(self, data):
        self.value = data

    def __str__(self):
        return base64.b64encode(self.value)

    def to_bytes(self):
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<I', len(self.value))
        bytes += self.value

        return bytes

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<I', fp.read(4))[0]
        data = struct.unpack('%ds' % ln, fp.read(ln))[0]
        return cls(data)

class StartListTextRecord(Record):
    type = 0xA4

class EndListTextRecord(Record):
    type = 0xA6

class EmptyTextRecord(Record):
    type = 0xA8

class TimeSpanTextRecord(Record):
    type = 0xAE

    def __init__(self, value):
        self.value = value

    def to_bytes(self):
        return (super(TimeSpanTextRecord, self).to_bytes() +
                    struct.pack('<q', self.value))

    def __str__(self):
        return str(datetime.timedelta(milliseconds=self.value/100))

    @classmethod
    def parse(cls, fp):
        value = struct.unpack('<q', fp.read(8))[0]
        return cls(value)

class DictionaryTextRecord(Record):
    type = 0xAA

    def __init__(self, index):
        self.index = index

    def to_bytes(self):
        return (super(DictionaryTextRecord, self).to_bytes() +
                    MultiByteInt31(self.index).to_bytes())

    def __str__(self):
        return dictionary[self.index]

    @classmethod
    def parse(cls, fp):
        index = MultiByteInt31.parse(fp).value
        return cls(index)


class ShortAttributeRecord(Attribute):
    type = 0x04

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_bytes(self):
        """
        >>> ShortAttributeRecord('test', TrueTextRecord()).to_bytes()
        '\\x04\\x04test\\x86'
        """
        bytes = super(ShortAttributeRecord, self).to_bytes()
        bytes += Utf8String(self.name).to_bytes()
        bytes += self.value.to_bytes()

        return bytes

    def __str__(self):
        return '%s="%s"' % (self.name, str(self.value))

    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp)
        type = struct.unpack('<B', fp.read(1))[0]
        value= __records__[type].parse(fp)

        return cls(name, value)

class AttributeRecord(Attribute):
    type = 0x05

    def __init__(self, prefix, name, value):
        self.prefix = prefix
        self.name = name
        self.value = value

    def to_bytes(self):
        """
        >>> AttributeRecord('x', 'test', TrueTextRecord()).to_bytes()
        '\\x05\\x01x\\x04test\\x86'
        """
        bytes = super(AttributeRecord, self).to_bytes()
        bytes += Utf8String(self.prefix).to_bytes()
        bytes += Utf8String(self.name).to_bytes()
        bytes += self.value.to_bytes()

        return bytes

    def __str__(self):
        return '%s:%s="%s"' % (self.prefix, self.name, str(self.value))
    
    @classmethod
    def parse(cls, fp):
        prefix = Utf8String.parse(fp).value
        name = Utf8String.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= __records__[type].parse(fp)

        return cls(prefix, name, value)


class ShortDictionaryAttributeRecord(Attribute):
    type = 0x06

    def __init__(self, index, value):
        self.index = index
        self.value = value

    def to_bytes(self):
        """
        >>> ShortDictionaryAttributeRecord(3, TrueTextRecord()).to_bytes()
        '\\x06\\x03\\x86'
        """
        bytes = super(ShortDictionaryAttributeRecord, self).to_bytes()
        bytes += MultiByteInt31(self.index).to_bytes()
        bytes += self.value.to_bytes()

        return bytes

    def __str__(self):
        return '%s="%s"' % (dictionary[self.index], str(self.value))
    
    @classmethod
    def parse(cls, fp):
        index = MultiByteInt31.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= __records__[type].parse(fp)

        return cls(index, value)



class DictionaryAttributeRecord(Attribute):
    type = 0x07

    def __init__(self, prefix, index, value):
        self.prefix = prefix
        self.index = index
        self.value = value

    def to_bytes(self):
        """
        >>> DictionaryAttributeRecord('x', 2, TrueTextRecord()).to_bytes()
        '\\x07\\x01x\\x02\\x86'
        """
        bytes = super(DictionaryAttributeRecord, self).to_bytes()
        bytes += Utf8String(self.prefix).to_bytes()
        bytes += MultiByteInt31(self.index).to_bytes()
        bytes += self.value.to_bytes()

        return bytes

    def __str__(self):
        return '%s:%s="%s"' % (self.prefix, dictionary[self.index], str(self.value))
    
    @classmethod
    def parse(cls, fp):
        index = MultiByteInt31.parse(fp).value
        name = Utf8String.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= __records__[type].parse(fp)

        return cls(prefix, index, value)




class ShortElementRecord(Element):
    type = 0x40

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.attributes = []

    def to_bytes(self):
        """
        >>> ShortElementRecord('Envelope').to_bytes()
        '@\\x08Envelope'
        """
        string = Utf8String(self.name)

        bytes= (super(ShortElementRecord, self).to_bytes() + 
                string.to_bytes())

        for attr in self.attributes:
            bytes += attr.to_bytes()
        return bytes

    def __str__(self):
        #return '<%s[name=%s]>' % (type(self).__name__, self.name)
        return '<%s %s>' % (self.name, ' '.join([str(a) for a in self.attributes]))

    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp).value
        return cls(name)

class ElementRecord(ShortElementRecord):
    type = 0x41

    def __init__(self, prefix, name, *args, **kwargs):
        super(ElementRecord, self).__init__(name)
        self.prefix = prefix
    
    def to_bytes(self):
        """
        >>> ElementRecord('x', 'Envelope').to_bytes()
        'A\\x01x\\x08Envelope'
        """
        pref = Utf8String(self.prefix)
        data = super(ElementRecord, self).to_bytes()
        type = data[0]
        return (type + pref.to_bytes() + data[1:])
    
    def __str__(self):
        return '<%s:%s %s>' % (self.prefix, self.name, ' '.join([str(a) for a in self.attributes]))
    
    @classmethod
    def parse(cls, fp):
        prefix = Utf8String.parse(fp).value
        name = Utf8String.parse(fp).value
        return cls(prefix, name)

class ShortDictionaryElementRecord(Element):
    type = 0x42

    def __init__(self, index, *args, **kwargs):
        self.index = index
        self.attributes = []
        self.name = dictionary[self.index]

    def __str__(self):
        return '<%s %s>' % (self.name, ' '.join([str(a) for a in
            self.attributes]))
    
    def to_bytes(self):
        """
        >>> ShortDictionaryElementRecord(2).to_bytes()
        'B\\x02'
        """
        string = MultiByteInt31(self.index)

        bytes= (super(ShortDictionaryElementRecord, self).to_bytes() + 
                string.to_bytes())

        for attr in self.attributes:
            bytes += attr.to_bytes()
        return bytes

    @classmethod
    def parse(cls, fp):
        index = MultiByteInt31.parse(fp).value
        return cls(index)

class DictionaryElementRecord(Element):
    type = 0x43

    def __init__(self, prefix, index, *args, **kwargs):
        self.prefix = prefix
        self.index = index
        self.attributes = []
        self.name = dictionary[self.index]

    def __str__(self):
        """
        >>> str(DictionaryElementRecord('x', 2))
        '<x:Envelope >'
        """
        return '<%s:%s %s>' % (self.prefix, self.name, ' '.join([str(a) for a in self.attributes]))
    
    def to_bytes(self):
        """
        >>> DictionaryElementRecord('x', 2).to_bytes()
        'C\\x01x\\x02'
        """
        pref = Utf8String(self.prefix)
        string = MultiByteInt31(self.index)

        bytes= (super(DictionaryElementRecord, self).to_bytes() +
                pref.to_bytes() +
                string.to_bytes())

        for attr in self.attributes:
            bytes += attr.to_bytes()
        return bytes



    @classmethod
    def parse(cls, fp):
        prefix = Utf8String.parse(fp).value
        index = MultiByteInt31.parse(fp).value
        return cls(prefix, index)

class ShortDictionaryXmlnsAttributeRecord(Attribute):
    type = 0x0A

    def __init__(self, index):
        self.index = index

    def __str__(self):
        return 'xmlns="%s"' % (dictionary[self.index],)

    def to_bytes(self):
        """
        >>> ShortDictionaryXmlnsAttributeRecord( 6).to_bytes()
        '\\n\\x06'
        """
        bytes = struct.pack('<B', self.type)
        bytes += MultiByteInt31(self.index).to_bytes()

        return bytes

    @classmethod
    def parse(cls, fp):
        index = MultiByteInt31.parse(fp).value
        return cls(index)


class DictionaryXmlnsAttributeRecord(Attribute):
    type = 0x0B

    def __init__(self, prefix, index):
        self.prefix = prefix
        self.index = index

    def __str__(self):
        return 'xmlns:%s="%s"' % (self.prefix, dictionary[self.index])

    def to_bytes(self):
        """
        >>> DictionaryXmlnsAttributeRecord('a', 6).to_bytes()
        '\\x0b\\x01\x61\\x06'
        """
        bytes = struct.pack('<B', self.type)
        bytes += Utf8String(self.prefix).to_bytes()
        bytes += MultiByteInt31(self.index).to_bytes()

        return bytes

    @classmethod
    def parse(cls, fp):
        prefix = Utf8String.parse(fp).value
        index = MultiByteInt31.parse(fp).value
        return cls(prefix, index)

class ShortXmlnsAttributeRecord(Attribute):
    type = 0x08

    def __init__(self, value, *args, **kwargs):
        super(XmlnsAttributeRecord, self).__init__(*args, **kwargs)
        self.value = value

    def to_bytes(self):
        bytes = struct.pack('<B', self.type)
        bytes += Utf8String(self.value).to_bytes()

    def __str__(self):
        return 'xmlns="%s"' % (self.value,)
    
    @classmethod
    def parse(cls, fp):
        value = Utf8String.parse(fp).value
        return cls(value)


class XmlnsAttributeRecord(Attribute):
    type = 0x09

    def __init__(self, name, value, *args, **kwargs):
        super(XmlnsAttributeRecord, self).__init__(*args, **kwargs)
        self.name = name
        self.value = value

    def to_bytes(self):
        bytes = struct.pack('<B', self.type)
        bytes += Utf8String(self.name).to_bytes()
        bytes += Utf8String(self.value).to_bytes()

    def __str__(self):
        return 'xmlns:%s="%s"' % (self.name, self.value)
    
    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp).value
        value = Utf8String.parse(fp).value
        return cls(name, value)

__records__ = (
        #CommentRecord,
        #EndElementRecord,
        #ShortElementRecord,
        #ElementRecord,
        #ShortDictionaryElementRecord,
        #DictionaryElementRecord,
        #ArrayRecord,
        #ShortAttributeRecord,
        #AttributeRecord,
        #OneTextRecord,
        #ZeroTextRecord,
        #TrueTextRecord,
        #FalseTextRecord,
        #Int8TextRecord,
        #Int16TextRecord,
        #Int32TextRecord,
        #Int64TextRecord,
        #Char8TextRecord,
        #Bytes8TextRecord,
        #Bytes16TextRecord,
        #UniqueIdTextRecord,
        #DictionaryTextRecord,
        #ShortDictionaryAttributeRecord,
        #DictionaryAttributeRecord,
        #ShortDictionaryXmlnsAttributeRecord,
        #DictionaryXmlnsAttributeRecord,
        #ShortXmlnsAttributeRecord,
        #XmlnsAttributeRecord,
        EndElementRecord,
        CommentRecord,
        ArrayRecord,
        ZeroTextRecord,
        OneTextRecord,
        FalseTextRecord,
        TrueTextRecord,
        Int8TextRecord,
        Int16TextRecord,
        Int32TextRecord,
        Int64TextRecord,
        UInt64TextRecord,
        BoolTextRecord,
        UnicodeChars8TextRecord,
        UnicodeChars16TextRecord,
        UnicodeChars32TextRecord,
        QNameDictionaryTextRecord,
        FloatTextRecord,
        DoubleTextRecord,
        DecimalTextRecord,
        DatetimeTextRecord,
        Char8TextRecord,
        Char16TextRecord,
        Char32TextRecord,
        UniqueIdTextRecord,
        UuidTextRecord,
        Bytes8TextRecord,
        Bytes16TextRecord,
        Bytes32TextRecord,
        StartListTextRecord,
        EndListTextRecord,
        EmptyTextRecord,
        TimeSpanTextRecord,
        DictionaryTextRecord,
        ShortAttributeRecord,
        AttributeRecord,
        ShortDictionaryAttributeRecord,
        DictionaryAttributeRecord,
        ShortElementRecord,
        ElementRecord,
        ShortDictionaryElementRecord,
        DictionaryElementRecord,
        ShortDictionaryXmlnsAttributeRecord,
        DictionaryXmlnsAttributeRecord,
        ShortXmlnsAttributeRecord,
        XmlnsAttributeRecord,
        )

__records__ = dict([(r.type, r) for r in __records__])

class PrefixElementRecord(ElementRecord):
    def __init__(self, name):
        super(PrefixElementRecord, self).__init__(self.char, name)

    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp).value
        return cls(name)

class PrefixDictionaryElementRecord(DictionaryElementRecord):
    def __init__(self, index):
        super(PrefixDictionaryElementRecord, self).__init__(self.char, index)

    @classmethod
    def parse(cls, fp):
        index = MultiByteInt31.parse(fp).value
        return cls(index)

class PrefixAttributeRecord(AttributeRecord):
    def __init__(self, name, value):
        super(PrefixAttributeRecord, self).__init__(self.char, name, value)

    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= __records__[type].parse(fp)
        return cls(name, value)

class PrefixDictionaryAttributeRecord(DictionaryAttributeRecord):
    def __init__(self, index, value):
        super(PrefixDictionaryAttributeRecord, self).__init__(self.char, index, value)

    @classmethod
    def parse(cls, fp):
        index= MultiByteInt31.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= __records__[type].parse(fp)
        return cls(index, value)

for c in range(0x0C, 0x25 + 1):
    char = chr(c-0x0C + ord('a'))
    cls = type(
           'PrefixDictionaryAttribute' + char.upper() + 'Record',
           (PrefixDictionaryAttributeRecord,),
           dict(
                type = c,
                char = char,
            ) 
           )
    __records__[c] = cls

for c in range(0x44, 0x5D + 1):
    char = chr(c-0x44 + ord('a'))
    cls = type(
           'PrefixDictionaryElement' + char.upper() + 'Record',
           (PrefixDictionaryElementRecord,),
           dict(
                type = c,
                char = char,
            ) 
           )
    __records__[c] = cls

for c in range(0x5E, 0x77 + 1):
    char = chr(c-0x5E + ord('a'))
    cls = type(
           'PrefixElement' + char.upper() + 'Record',
           (PrefixElementRecord,),
           dict(
                type = c,
                char = char,
            ) 
           )
    __records__[c] = cls

for c in range(0x26, 0x3F + 1):
    char = chr(c-0x26 + ord('a'))
    cls = type(
           'PrefixAttribute' + char.upper() + 'Record',
           (PrefixAttributeRecord,),
           dict(
                type = c,
                char = char,
            ) 
           )
    __records__[c] = cls

def print_records2(records, idx=0, last_el=None):
    if len(records) <= idx:
        return

    while not isinstance(records[idx], Element):
        if isinstance(records[idx], EndElementRecord):
            print '</%s>' % last_el.name
        elif isinstance(records[idx], Element):
            break
        else:
            print str(records[idx])
        idx += 1
        if len(records) <= idx:
            return

    print str(records[idx])
    print_records(records, idx+1, records[idx])

def print_records(records, skip=0):
    if records == None:
        return
    was_el = False
    for r in records:
        if isinstance(r, Element):
            sys.stdout.write('\n' + ' ' * skip + str(r))
        else:
            sys.stdout.write(str(r))
       
        new_line = False
        if hasattr(r, 'childs'):
            new_line = print_records(r.childs, skip+1)
        if isinstance(r, Element):
            if new_line:
                sys.stdout.write('\n' + ' ' * skip)
            if hasattr(r, 'prefix'):
                sys.stdout.write('</%s:%s>' % (r.prefix, r.name))
            else:
                sys.stdout.write('</%s>' % r.name)
            was_el = True
        else:
            was_el = False
    return was_el

if __name__ == '__main__':
    import sys
#    print __records__
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        with open(filename) as fp:
            records = Record.parse(fp)
            print_records(records)
    else:
        import doctest
        doctest.testmod()

