from __future__ import absolute_import
import sys
import logging

log = logging.getLogger(__name__)

from records.base import *
from records.text import *
from records.attributes import *
from records.elements import *

def print_records(records, skip=0, fp=None):
    if records == None:
        return
    if fp == None:
        fp = sys.stdout

    was_el = False
    for r in records:
        if isinstance(r, EndElementRecord):
            continue
        if isinstance(r, Element):
            fp.write('\n' + ' ' * skip + str(r))
        else:
            fp.write(str(r))
       
        new_line = False
        if hasattr(r, 'childs'):
            new_line = print_records(r.childs, skip+1, fp)
        if isinstance(r, Element):
            if new_line:
                fp.write('\n' + ' ' * skip)
            if hasattr(r, 'prefix'):
                fp.write('</%s:%s>' % (r.prefix, r.name))
            else:
                fp.write('</%s>' % r.name)
            was_el = True
        else:
            was_el = False
    return was_el

def repr_records(records, skip=0):
    if records == None:
        return

    for r in records:
        print ' '*skip + str(r)
        if hasattr(r, 'childs'):
            repr_records(r.childs, skip+1)

def dump_records(records):
    out = ''

    for r in records:
        msg = 'Write %s' % type(r).__name__
        if r == records[-1]:
            if isinstance(r, Text):
                r.type = r.type + 1
                msg += ' with EndElement (0x%X)' % r.type
        log.debug(msg)
        log.debug('Value %s' % str(r))
        if isinstance(r, Element) and not isinstance(r, EndElementRecord) and len(r.attributes):
            log.debug(' Attributes:')
            for a in r.attributes:
                log.debug(' %s: %s' % (type(a).__name__, str(a)))
        out += r.to_bytes()
        
        if hasattr(r, 'childs'):
            out += dump_records(r.childs)
            if len(r.childs) == 0 or not isinstance(r.childs[-1], Text):
                log.debug('Write EndElement for %s' % r.name)
                out += EndElementRecord().to_bytes()
        elif isinstance(r, Element) and not isinstance(r, EndElementRecord):
            log.debug('Write EndElement for %s' % (r.name,))
            out += EndElementRecord().to_bytes()

    return out
