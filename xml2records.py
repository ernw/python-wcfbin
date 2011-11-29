#!/usr/bin/env python2

from HTMLParser import HTMLParser
import re
import base64
import logging

log = logging.getLogger(__name__)

from records import *
from dictionary import inverted_dict

classes = Record.records.values()
classes = dict([(c.__name__, c) for c in classes])
inverted_dict = dict([((n.lower()),v) for n,v in inverted_dict.iteritems()])


int_reg = re.compile(r'^-?\d+$')
uint_reg = re.compile(r'^\d+$')
uuid_reg = re.compile(r'^urn:uuid:(([a-fA-F0-9]{8})-(([a-fA-F0-9]{4})-){3}([a-fA-F0-9]{12}))$')
base64_reg = re.compile(r'^[a-zA-Z0-9/+]*={0,2}$')
float_reg = re.compile(r'^-?(INF)|(NaN)|(\d+(\.\d+)?)$')

class Parser(HTMLParser):

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
                if name.lower() in inverted_dict:
                    cls_name = 'PrefixDictionary' + cls_name
                    log.debug('New %s: %s' % (cls_name, name))
                    return classes[cls_name](inverted_dict[name.lower()])
                else:
                    cls_name = 'Prefix' + cls_name
                    log.debug('New %s: %s' % (cls_name, name))
                    return classes[cls_name](name)
            else:
                if name.lower() in inverted_dict:
                    log.debug('New DictionaryElementRecord: %s:%s' % (prefix, name))
                    return DictionaryElementRecord(prefix,
                            inverted_dict[name.lower()])
                else:
                    log.debug('New ElementRecord: %s:%s' % (prefix, name))
                    return ElementRecord(prefix, name)
        else:
            if tag.lower() in inverted_dict:
                log.debug('New ShortDictionaryElementRecord: %s' % (tag, ))
                return ShortDictionaryElementRecord(inverted_dict[tag.lower()])
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
        if data == '0':
            return ZeroTextRecord()
        elif data == '1':
            return OneTextRecord()
        elif data.lower() == 'false':
            return FalseTextRecord()
        elif data.lower() == 'true':
            return TrueTextRecord()
        elif len(data) > 3 and data[1] == ':' and data[2:] in inverted_dict:
            return QNameDictionary(data[0], inverted_dict[data[2:]])
        elif uuid_reg.match(data):
            m = uuid_reg.match(data)
            return UniqueIdTextRecord(m.group(1))
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
        elif base64_reg.match(data):
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
        elif data.lower() in inverted_dict:
            return DictionaryTextRecord(inverted_dict[data.lower()])
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
                if value.lower() in inverted_dict:
                    return DictionaryXmlnsAttributeRecord(name,
                            inverted_dict[value.lower()])
                else:
                    return XmlnsAttributeRecord(name, value)
            elif len(prefix) == 1:
                value = self._parse_data(value)
                cls_name = 'Attribute' + prefix.upper() + 'Record'
                if name.lower() in inverted_dict:
                    return classes['PrefixDictionary' +
                            cls_name](inverted_dict[name.lower()], value)
                else:
                    return classes['Prefix' + cls_name](name,value)
            else:
                value = self._parse_data(value)
                if name.lower() in inverted_dict:
                    return DictionaryAttributeRecord(prefix,
                            inverted_dict[name.lower()], value)
                else:
                    return AttributeRecord(prefix, name, value)
        elif name == 'xmlns':
            if value.lower() in inverted_dict:
                return ShortDictionaryXmlnsAttributeRecord(inverted_dict[value.lower()])
            else:
                return ShortXmlnsAttributeRecord(value)
        else:
            value = self._parse_data(value)
            if name.lower() in inverted_dict:
                return ShortDictionaryAttributeRecord(inverted_dict[name.lower()], value)
            else:
                return ShortAttributeRecord(name, value)


    def handle_starttag(self, tag, attrs):
        if self.data:
            self._store_data(self.data,False)
            self.data = None
        
        el = self._parse_tag(tag)
        for n,v in attrs:
            el.attributes.append(self._parse_attr(n,v))
        self.last_record.childs.append(el)
        el.parent = self.last_record
        self.last_record = el
    
    def handle_startendtag(self, tag, attrs):
        if self.data:
            self._store_data(self.data,False)
            self.data = None
        
        el = self._parse_tag(tag)
        for n,v in attrs:
            el.attributes.append(self._parse_attr(n,v))
        self.last_record.childs.append(el)
    
    def handle_endtag(self, tag):
        if self.data:
            self._store_data(self.data, True)
            self.data = None
        else:
            pass#self.last_record.childs.append(EndElementRecord())

        self.last_record = self.last_record.parent

    def handle_data(self,data):
        if not self.data:
            self.data = data
        else:
            self.data += data

    def handle_comment(self,comment):
        if data:
            self._store_data(self.data, False)
            self.data = None

        self.last_record.childs.append(CommentRecord(comment))


if __name__ == '__main__':
    import sys
    
    fp = sys.stdin

    if len(sys.argv) > 1:
        fp = open(sys.argv[1], 'r')

    logging.basicConfig(level=logging.INFO)

    p = Parser()
    indata = fp.read().strip()
    fp.close()
    p.feed(indata)
    sys.stdout.write(dump_records(p.records))
