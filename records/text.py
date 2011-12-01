import struct
import base64
import datetime
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from datatypes import *
from records.base import *
from dictionary import dictionary

class ZeroTextRecord(Text):
    type = 0x80

    def __str__(self):
        return '0'

    @classmethod
    def parse(cls, fp):
        return cls()

class OneTextRecord(Text):
    type = 0x82

    def __str__(self):
        return '1'

    @classmethod
    def parse(cls, fp):
        return cls()

class FalseTextRecord(Text):
    type = 0x84

    def __str__(self):
        return 'false'

    @classmethod
    def parse(cls, fp):
        return cls()

class TrueTextRecord(Text):
    type = 0x86

    def __str__(self):
        return 'true'

    @classmethod
    def parse(cls, fp):
        return cls()

class Int8TextRecord(Text):
    type = 0x88

    def __init__(self, value):
        self.value = value

    def to_bytes(self):
        return super(Int8TextRecord, self).to_bytes() + struct.pack('<b',
                self.value)

    def __str__(self):
        return str(self.value)

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<b', fp.read(1))[0])

class Int16TextRecord(Int8TextRecord):
    type = 0x8A

    def to_bytes(self):
        return struct.pack('<B', self.type) + struct.pack('<h',
                self.value)

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<h', fp.read(2))[0])

class Int32TextRecord(Int8TextRecord):
    type = 0x8C

    def to_bytes(self):
        return struct.pack('<B', self.type) + struct.pack('<i',
                self.value)

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<i', fp.read(4))[0])

class Int64TextRecord(Int8TextRecord):
    type = 0x8E

    def to_bytes(self):
        return struct.pack('<B', self.type) + struct.pack('<q',
                self.value)

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<q', fp.read(8))[0])

class UInt64TextRecord(Int64TextRecord):
    type = 0xB2

    def to_bytes(self):
        return struct.pack('<B', self.type) + struct.pack('<Q',
                self.value)

    @classmethod
    def parse(cls, fp):
        return cls(struct.unpack('<Q', fp.read(8))[0])

class BoolTextRecord(Text):
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

class UnicodeChars8TextRecord(Text):
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

class QNameDictionaryTextRecord(Text):
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


class FloatTextRecord(Text):
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

class DecimalTextRecord(Text):
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

class DatetimeTextRecord(Text):
    type = 0x96

    def __init__(self, value, tz):
        self.value = value
        self.tz = tz

    def __str__(self):
        """
        >>> str(DatetimeTextRecord(621355968000000000,0))
        '1970-01-01T00:00:00'
        >>> str(DatetimeTextRecord(0,0))
        '0001-01-01T00:00:00'
        """
        ticks = self.value
        dt = (datetime.datetime(1, 1, 1) + 
                datetime.timedelta(microseconds=ticks/10))
        return dt.isoformat()

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

class Char8TextRecord(Text):
    type = 0x98

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value
    
    def to_bytes(self):
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<B', len(self.value))
        bytes += self.value

        return bytes
    
    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<B', fp.read(1))[0]
        value = fp.read(ln)
        return cls(value)

class Char16TextRecord(Char8TextRecord):
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

class Char32TextRecord(Char8TextRecord):
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

class UniqueIdTextRecord(Text):
    type = 0xAC

    def __init__(self, uuid):
        if isinstance(uuid, list) or isinstance(uuid, tuple):
            self.uuid = uuid
        else:
            if uuid.startswith('urn:uuid'):
                uuid = uuid[9:]
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
        #return 'urn:uuid:{0:08x}-{1:04x}-{2:04x}-{3:02x}{4:02x}-{5:02x}{6:02x}{7:02x}{8:02x}{9:02x}{10:02x}'.format(*self.uuid)
        return 'urn:uuid:%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x' % tuple(self.uuid)

    @classmethod
    def parse(cls, fp):
        uuid = struct.unpack('<IHHBBBBBBBB', fp.read(16))
        return cls(uuid)

class UuidTextRecord(UniqueIdTextRecord):
    type = 0xB0
    
    def __str__(self):
        return '%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x' % tuple(self.uuid)

class Bytes8TextRecord(Text):
    type = 0x9E

    def __init__(self, data):
        self.value = data

    def to_bytes(self):
        bytes  = struct.pack('<B', self.type)
        bytes += struct.pack('<B', len(self.value))
        bytes += self.value

        return bytes

    def __str__(self):
        return base64.b64encode(self.value)

    @classmethod
    def parse(cls, fp):
        ln = struct.unpack('<B', fp.read(1))[0]
        data = struct.unpack('%ds' % ln, fp.read(ln))[0]
        return cls(data)

class Bytes16TextRecord(Bytes8TextRecord):
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

class Bytes32TextRecord(Bytes8TextRecord):
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

class StartListTextRecord(Text):
    type = 0xA4

class EndListTextRecord(Text):
    type = 0xA6

class EmptyTextRecord(Text):
    type = 0xA8

class TimeSpanTextRecord(Text):
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

class DictionaryTextRecord(Text):
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

Record.add_records((ZeroTextRecord,
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
        DictionaryTextRecord,))
