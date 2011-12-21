#!/usr/bin/env python2
# vim: set ts=4 sw=4 tw=79 fileencoding=utf-8:

from __future__ import absolute_import

from wcf.MyHTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
import re
import base64
import logging

log = logging.getLogger(__name__)

from wcf.records import *
from wcf.dictionary import inverted_dict


classes = Record.records.values()
classes = dict([(c.__name__, c) for c in classes])
#inverted_dict = dict([(n,v) for n,v in inverted_dict.iteritems()])


def unescape(s):
    return chr(name2codepoint[s]) if (s in name2codepoint) else "&" + s + ";"

int_reg = re.compile(r'^-?\d+$')
uint_reg = re.compile(r'^\d+$')
uuid_reg = re.compile(r'^(([a-fA-F0-9]{8})-(([a-fA-F0-9]{4})-){3}([a-fA-F0-9]{12}))$')
uniqueid_reg = re.compile(r'^urn:uuid:(([a-fA-F0-9]{8})-(([a-fA-F0-9]{4})-){3}([a-fA-F0-9]{12}))$')
base64_reg = re.compile(r'^[a-zA-Z0-9/+]*={0,2}$')
float_reg = re.compile(r'^-?(INF)|(NaN)|(\d+(\.\d+)?)$')
datetime_reg = re.compile(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{1,7})?)?(Z|(\+|-\d{2}:\d{2}))')


class XMLParser(HTMLParser):

    def reset(self):
        HTMLParser.reset(self)
        self.records = []
        self.last_record = Record()
        self.last_record.childs = self.records
        self.last_record.parent = None
        self.data = None

    def _parse_tag(self, tag):
        if ':' in tag:
            prefix = tag[:tag.find(':')]
            name   = tag[tag.find(':')+1:]

            if len(prefix) == 1:
                cls_name = 'Element' + prefix.upper() + 'Record'
                if name in inverted_dict:
                    cls_name = 'PrefixDictionary' + cls_name
                    log.debug('New %s: %s' % (cls_name, name))
                    return classes[cls_name](inverted_dict[name])
                else:
                    cls_name = 'Prefix' + cls_name
                    log.debug('New %s: %s' % (cls_name, name))
                    return classes[cls_name](name)
            else:
                if name in inverted_dict:
                    log.debug('New DictionaryElementRecord: %s:%s' % 
                            (prefix, name))
                    return DictionaryElementRecord(prefix,
                            inverted_dict[name])
                else:
                    log.debug('New ElementRecord: %s:%s' % (prefix, name))
                    return ElementRecord(prefix, name)
        else:
            if tag in inverted_dict:
                log.debug('New ShortDictionaryElementRecord: %s' % (tag, ))
                return ShortDictionaryElementRecord(inverted_dict[tag])
            else:
                log.debug('New ShortElementRecord: %s' % (tag, ))
                return ShortElementRecord(tag)

    def _store_data(self, data, end=False):
        textrecord = self._parse_data(data)
        if isinstance(textrecord, EmptyTextRecord):
            return
        log.debug('New %s: %s' % (type(textrecord).__name__, data))

        self.last_record.childs.append(textrecord)
        #if end:
        #    textrecord.type += 1
 
    def _parse_data(self, data):
        data = data.strip()
        b64 = False
        try:
            if base64_reg.match(data):
                base64.b64decode(data)
                b64 = True
        except:
            b64 = False
        if data == '0':
            return ZeroTextRecord()
        elif data == '1':
            return OneTextRecord()
        elif data.lower() == 'false':
            return FalseTextRecord()
        elif data.lower() == 'true':
            return TrueTextRecord()
        elif len(data) > 3 and data[1] == ':' and data[2:] in inverted_dict:
            return QNameDictionaryTextRecord(data[0], inverted_dict[data[2:]])
        elif uniqueid_reg.match(data):
            m = uniqueid_reg.match(data)
            return UniqueIdTextRecord(m.group(1))
        elif uuid_reg.match(data):
            m = uuid_reg.match(data)
            return UuidTextRecord(m.group(1))
        elif int_reg.match(data):
            val = int(data)
            if val < 2**8:
                return Int8TextRecord(val)
            elif val < 2**16:
                return Int16TextRecord(val)
            elif val < 2**32:
                return Int32TextRecord(val)
            elif val < 2**64:
                return Int64TextRecord(val)
        elif data == '':
            return EmptyTextRecord()
        elif b64:
            data = base64.b64decode(data)
            val = len(data)
            if val < 2**8:
                return Bytes8TextRecord(data)
            elif val < 2**16:
                return Bytes16TextRecord(data)
            elif val < 2**32:
                return Bytes32TextRecord(data)
        elif float_reg.match(data):
            return DoubleTextRecord(float(data))
        elif data in inverted_dict:
            return DictionaryTextRecord(inverted_dict[data])
        elif datetime_reg.match(data) and False:  # TODO
            t = data.split('Z')
            tz = 0
            if len(t) > 1:
                dt = t[0]
                tz = 1 if len(tz[1]) else 2
            dt = t[0]
            dt = dt.split('.')
            ns = 0
            if len(dt) > 1:
                ns = int(dt[1])
            dt = dt[0]
            if len(dt) == 10:
                dt = datetime.datetime.strptime(dt, "%Y-%m-%d")
            elif len(dt) == 16:
                dt = datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M")
            else:
                dt = datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")

            base_diff = 62135596800.0
            dt = int((time.mktime(dt.timetuple()) - base) * 10 + ms)
           
            return DateTimeTextRecord(dt, tz)
        else:
            val = len(data)
            if val < 2**8:
                return Char8TextRecord(data)
            elif val < 2**16:
                return Char16TextRecord(data)
            elif val < 2**32:
                return Char32TextRecord(data)

    def _parse_attr(self, name, value):

        if ':' in name:
            prefix = name[:name.find(':')]
            name   = name[name.find(':')+1:]
           
            if prefix == 'xmlns':
                if value in inverted_dict:
                    return DictionaryXmlnsAttributeRecord(name,
                            inverted_dict[value])
                else:
                    return XmlnsAttributeRecord(name, value)
            elif len(prefix) == 1:
                value = self._parse_data(value)
                cls_name = 'Attribute' + prefix.upper() + 'Record'
                if name in inverted_dict:
                    return classes['PrefixDictionary' +
                            cls_name](inverted_dict[name], value)
                else:
                    return classes['Prefix' + cls_name](name, value)
            else:
                value = self._parse_data(value)
                if name in inverted_dict:
                    return DictionaryAttributeRecord(prefix,
                            inverted_dict[name], value)
                else:
                    return AttributeRecord(prefix, name, value)
        elif name == 'xmlns':
            if value in inverted_dict:
                return ShortDictionaryXmlnsAttributeRecord(inverted_dict[value])
            else:
                return ShortXmlnsAttributeRecord(value)
        else:
            value = self._parse_data(value)
            if name in inverted_dict:
                return ShortDictionaryAttributeRecord(inverted_dict[name], value)
            else:
                return ShortAttributeRecord(name, value)

    def handle_starttag(self, tag, attrs):
        if self.data:
            self._store_data(self.data, False)
            self.data = None
       
        el = self._parse_tag(tag)
        for n, v in attrs:
            el.attributes.append(self._parse_attr(n, v))
        self.last_record.childs.append(el)
        el.parent = self.last_record
        self.last_record = el
   
    def handle_startendtag(self, tag, attrs):
        if self.data:
            self._store_data(self.data, False)
            self.data = None
       
        el = self._parse_tag(tag)
        for n, v in attrs:
            el.attributes.append(self._parse_attr(n, v))
        self.last_record.childs.append(el)
        #self.last_record.childs.append(EndElementRecord())
   
    def handle_endtag(self, tag):
        if self.data:
            self._store_data(self.data, True)
            self.data = None
        else:
            pass#self.last_record.childs.append(EndElementRecord())

        self.last_record = self.last_record.parent

    def handle_data(self, data):
        if not self.data:
            self.data = data
        else:
            self.data += data

    def handle_charref(self, name):
        self.handle_data(chr(int(name, 16)))

    def handle_entityref(self, name):
        self.handle_data(unescape(name))

    handle_decl = handle_data

    def handle_comment(self, comment):
        if data:
            self._store_data(self.data, False)
            self.data = None

        self.last_record.childs.append(CommentRecord(comment))

    @classmethod
    def parse(cls, data):
        """
        Parses a XML String/Fileobject into a Record tree

        :param data: a XML string or fileobject
        :returns: a Record tree

        >>> from wcf.records import dump_records, print_records
        >>> from wcf.xml2records import XMLParser
        >>> r = XMLParser.parse('<s:Envelope><b:Body /></s:Envelope>')
        >>> dump_records(r)
        'V\\x02E\\x0e\\x01\\x01'
        >>> b = print_records(r)
        <s:Envelope >
         <b:Body ></b:Body>
        </s:Envelope>
        """
        p = cls()
        if isinstance(data, str):
            pass
        elif hasattr(data, 'read'):
            tmp = data.read()
            data.close()
            data = tmp
        else:
            raise ValueError("%s has an incompatible type %s" % (data,
                type(data)))
        
        p.feed(data)

        return p.records

if __name__ == '__main__':
    import sys
   
    fp = sys.stdin

    if len(sys.argv) > 1:
        fp = open(sys.argv[1], 'r')

    logging.basicConfig(level=logging.INFO)

    p = XMLParser()
    indata = fp.read()#.strip()
    fp.close()
    p.feed(indata)
    sys.stdout.write(dump_records(p.records))
