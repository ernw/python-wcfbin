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
from wcf.dictionary import *


class ShortElementRecord(Element):
    type = 0x40

    def __init__(self, name, *args, **kwargs):
        self.childs = []
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
        return '<%s %s>' % (self.name, 
                ' '.join([str(a) for a in self.attributes]))

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
        return '<%s:%s %s>' % (self.prefix, self.name, 
                ' '.join([str(a) for a in self.attributes]))
   
    @classmethod
    def parse(cls, fp):
        prefix = Utf8String.parse(fp).value
        name = Utf8String.parse(fp).value
        return cls(prefix, name)


class ShortDictionaryElementRecord(Element):
    type = 0x42

    def __init__(self, index, *args, **kwargs):
        self.childs = []
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
        self.childs = []
        self.prefix = prefix
        self.index = index
        self.attributes = []
        self.name = dictionary[self.index]

    def __str__(self):
        """
        >>> str(DictionaryElementRecord('x', 2))
        '<x:Envelope >'
        """
        return '<%s:%s %s>' % (self.prefix, self.name, 
                ' '.join([str(a) for a in self.attributes]))
   
    def to_bytes(self):
        """
        >>> DictionaryElementRecord('x', 2).to_bytes()
        'C\\x01x\\x02'
        """
        pref = Utf8String(self.prefix)
        string = MultiByteInt31(self.index)

        bytes = (super(DictionaryElementRecord, self).to_bytes() +
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


class PrefixElementRecord(ElementRecord):
    def __init__(self, name):
        super(PrefixElementRecord, self).__init__(self.char, name)

    def to_bytes(self):
        string = Utf8String(self.name)

        bytes = (struct.pack('<B', self.type) +
                string.to_bytes())

        for attr in self.attributes:
            bytes += attr.to_bytes()
        return bytes

    @classmethod
    def parse(cls, fp):
        name = Utf8String.parse(fp).value
        return cls(name)


class PrefixDictionaryElementRecord(DictionaryElementRecord):
    def __init__(self, index):
        super(PrefixDictionaryElementRecord, self).__init__(self.char, index)

    def to_bytes(self):
        string = MultiByteInt31(self.index)

        bytes = (struct.pack('<B', self.type) +
                string.to_bytes())

        for attr in self.attributes:
            bytes += attr.to_bytes()
        return bytes

    @classmethod
    def parse(cls, fp):
        index = MultiByteInt31.parse(fp).value
        return cls(index)


Record.add_records((
        ShortElementRecord,
        ElementRecord,
        ShortDictionaryElementRecord,
        DictionaryElementRecord,
    ))

__records__ = []

for c in range(0x44, 0x5D + 1):
    char = chr(c - 0x44 + ord('a'))
    cls = type(
           'PrefixDictionaryElement' + char.upper() + 'Record',
           (PrefixDictionaryElementRecord,),
           dict(
                type=c,
                char=char,
            )
           )
    __records__.append(cls)

for c in range(0x5E, 0x77 + 1):
    char = chr(c - 0x5E + ord('a'))
    cls = type(
           'PrefixElement' + char.upper() + 'Record',
           (PrefixElementRecord,),
           dict(
                type=c,
                char=char,
            )
           )
    __records__.append(cls)

Record.add_records(__records__)
del __records__
