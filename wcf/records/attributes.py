# vim: set ts=4 sw=4 tw=79 fileencoding=utf-8:
#  Copyright (c) 2011, Timo Schmid <tschmid@ernw.de>
#  All rights reserved.
# 
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of the ERMW GmbH nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from __future__ import absolute_import

import struct
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from wcf.datatypes import *
from wcf.records.base import *
from wcf.records.text import *
from wcf.dictionary import dictionary


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
        name = Utf8String.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= Record.records[type].parse(fp)

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
        value= Record.records[type].parse(fp)

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
        value= Record.records[type].parse(fp)

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
        return '%s:%s="%s"' % (self.prefix, dictionary[self.index], 
                str(self.value))
   
    @classmethod
    def parse(cls, fp):
        prefix = Utf8String.parse(fp).value
        index = MultiByteInt31.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= Record.records[type].parse(fp)

        return cls(prefix, index, value)


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
        super(ShortXmlnsAttributeRecord, self).__init__(*args, **kwargs)
        self.value = value

    def to_bytes(self):
        bytes = struct.pack('<B', self.type)
        bytes += Utf8String(self.value).to_bytes()
        return bytes

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
        return bytes

    def __str__(self):
        return 'xmlns:%s="%s"' % (self.name, self.value)
   
    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp).value
        value = Utf8String.parse(fp).value
        return cls(name, value)


class PrefixAttributeRecord(AttributeRecord):
    def __init__(self, name, value):
        super(PrefixAttributeRecord, self).__init__(self.char, name, value)

    def to_bytes(self):
        string = Utf8String(self.name)
        return (struct.pack('<B', self.type) + string.to_bytes() +
                self.value.to_bytes())

    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= Record.records[type].parse(fp)
        return cls(name, value)


class PrefixDictionaryAttributeRecord(DictionaryAttributeRecord):
    def __init__(self, index, value):
        super(PrefixDictionaryAttributeRecord, self).__init__(self.char, 
                index, value)

    def to_bytes(self):
        idx = MultiByteInt31(self.index)
        return (struct.pack('<B', self.type) + idx.to_bytes() +
                self.value.to_bytes())

    @classmethod
    def parse(cls, fp):
        index= MultiByteInt31.parse(fp).value
        type = struct.unpack('<B', fp.read(1))[0]
        value= Record.records[type].parse(fp)
        return cls(index, value)


Record.add_records((
        ShortAttributeRecord,
        AttributeRecord,
        ShortDictionaryAttributeRecord,
        DictionaryAttributeRecord,
        ShortDictionaryXmlnsAttributeRecord,
        DictionaryXmlnsAttributeRecord,
        ShortXmlnsAttributeRecord,
        XmlnsAttributeRecord,
        ))


__records__ = []

for c in range(0x0C, 0x25 + 1):
    char = chr(c - 0x0C + ord('a'))
    cls = type(
           'PrefixDictionaryAttribute' + char.upper() + 'Record',
           (PrefixDictionaryAttributeRecord,),
           dict(
                type=c,
                char=char,
            )
           )
    __records__.append(cls)

for c in range(0x26, 0x3F + 1):
    char = chr(c - 0x26 + ord('a'))
    cls = type(
           'PrefixAttribute' + char.upper() + 'Record',
           (PrefixAttributeRecord,),
           dict(
                type=c,
                char=char,
            )
           )
    __records__.append(cls)

Record.add_records(__records__)
del __records__
