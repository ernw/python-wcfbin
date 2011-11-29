#!/usr/bin/env python2
import logging

if __name__ == '__main__':
    import doctest
    from records import text,attributes,elements,base
    doctest.testmod(base)
    doctest.testmod(elements)
    doctest.testmod(attributes)
    doctest.testmod(text)

    from StringIO import StringIO
    from records import dump_records, Record, print_records
    fp = open('test.bin', 'rb')
    orig = fp.read()
    fp.close()

    fp = StringIO(orig)
    #logging.getLogger('records').setLevel(logging.DEBUG)
    new = dump_records(Record.parse(fp))
    fp.close()
    try:
        assert new == orig
    except AssertionError:
        logging.getLogger('records.base').setLevel(logging.DEBUG)
        print 'orig:'
        print orig.encode('hex')
        fp = StringIO(orig)
        print_records(Record.parse(fp))
        fp.close()
        
        print '\nnew:'
        print new.encode('hex')

        fp = StringIO(new)
        print_records(Record.parse(fp))
        fp.close()

