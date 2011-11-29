#!/usr/bin/env python2

if __name__ == '__main__':
    import sys
    from records import Record,print_records
    fp = sys.stdin
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        fp = open(filename, 'rb')
    
    with fp:
        records = Record.parse(fp)
        print_records(records)
