#!/usr/bin/env python2

if __name__ == '__main__':
    import doctest
    from records import text,attributes,elements,base
    doctest.testmod(base)
    doctest.testmod(elements)
    doctest.testmod(attributes)
    doctest.testmod(text)
