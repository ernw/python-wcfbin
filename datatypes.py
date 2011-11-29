import struct
import logging

log = logging.getLogger(__name__)

class MultiByteInt31(object):

    def __init__(self, *args):
        self.value = args[0] if len(args) else None
    
    def to_bytes(self):
        """
        >>> MultiByteInt31(268435456).to_bytes()
        '\\x80\\x80\\x80\\x80\\x01'
        >>> MultiByteInt31(0x7f).to_bytes()
        '\\x7f'
        >>> MultiByteInt31(0x3fff).to_bytes()
        '\\xff\\x7f'
        >>> MultiByteInt31(0x1fffff).to_bytes()
        '\\xff\\xff\\x7f'
        >>> MultiByteInt31(0xfffffff).to_bytes()
        '\\xff\\xff\\xff\\x7f'
        >>> MultiByteInt31(0x3fffffff).to_bytes()
        '\\xff\\xff\\xff\\xff\\x03'
        """
        value_a = self.value & 0x7F
        value_b = (self.value >>  7) & 0x7F
        value_c = (self.value >> 14) & 0x7F
        value_d = (self.value >> 21) & 0x7F
        value_e = (self.value >> 28) & 0x03
        if value_e != 0:
            return struct.pack('<BBBBB',
                    value_a | 0x80,
                    value_b | 0x80,
                    value_c | 0x80,
                    value_d | 0x80,
                    value_e)
        elif value_d != 0:
            return struct.pack('<BBBB',
                    value_a | 0x80,
                    value_b | 0x80,
                    value_c | 0x80,
                    value_d)
        elif value_c != 0:
            return struct.pack('<BBB',
                    value_a | 0x80,
                    value_b | 0x80,
                    value_c)
        elif value_b != 0:
            return struct.pack('<BB',
                    value_a | 0x80,
                    value_b)
        elif value_a != 0:
            return struct.pack('<B',
                    value_a)

    def __str__(self):
        return str(self.value)

    @classmethod
    def parse(cls, fp):
        v = 0
        #tmp = ''
        for pos in range(4):
            b = fp.read(1)
            #tmp += b
            value = struct.unpack('<B', b)[0]
            v |= (value & 0x7F) << 7*pos
            if not value & 0x80:
                break
        #print ('%s => 0x%X' % (repr(tmp), v))
        
        return cls(v)

class Utf8String(object):

    def __init__(self, *args):
        self.value = args[0] if len(args) else None

    def to_bytes(self):
        """
        >>> Utf8String("abc").to_bytes()
        '\\x03\x61\x62\x63'
        """
        strlen = len(self.value)

        return MultiByteInt31(strlen).to_bytes() + self.value

    def __str__(self):
        return str(self.value)

    @classmethod
    def parse(cls, fp):
        lngth = struct.unpack('<B', fp.read(1))[0]
        
        return cls(fp.read(lngth))

class Decimal(object):
    def __init__(self, sign, high, low, scale):

        if not 0 <= scale <= 28:
            raise ValueError('scale %d isn\'t between 0 and 28' % scale)
        self.sign = sign
        self.high = high
        self.low  = low
        self.scale = scale

    def to_bytes(self):
        """
        >>> Decimal(False, 0, 5123456, 6).to_bytes()
        '\\x00\\x00\\x06\\x00\\x00\\x00\\x00\\x00\\x80-N\\x00\\x00\\x00\\x00\\x00'
        """
        log.warn('Possible false interpretation')
        bytes  = struct.pack('<H', 0)
        bytes += struct.pack('<B', self.scale)
        bytes += struct.pack('<B', 0x80 if self.sign else 0x00)
        bytes += struct.pack('<I', self.high)
        bytes += struct.pack('<Q', self.low)

        return bytes

    def __str__(self):
        """
        >>> str(Decimal(False, 0, 1234, 3))
        '1.234'
        >>> str(Decimal(False, 0, 1234, 1))
        '123.4'
        >>> str(Decimal(True, 0, 1234, 1))
        '-123.4'
        >>> str(Decimal(False, 0, 5123456, 6))
        '5.123456'
        """
        log.warn('Possible false interpretation')
        value = str(self.high * 2**64 + self.low)
        if self.scale > 0:
            value = value[:-self.scale] + '.' + value[-self.scale:]
        
        if self.sign:
            value = '-%s' % value
        return value

    @classmethod
    def parse(cls, fp):
        log.warn('Possible false interpretation')
        fp.read(2)
        scale = struct.unpack('<B', fp.read(1))[0]
        sign  = struct.unpack('<B', fp.read(1))[0] & 0x80
        high  = struct.unpack('<I', fp.read(4))[0]
        low   = struct.unpack('<Q', fp.read(8))[0]

        return cls(sign, scale, high, low)
        

if __name__ == '__main__':
    import doctest
    doctest.testmod()
