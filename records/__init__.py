from __future__ import absolute_import
import sys

from records.base import *
from records.text import *
from records.attributes import *
from records.elements import *

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

