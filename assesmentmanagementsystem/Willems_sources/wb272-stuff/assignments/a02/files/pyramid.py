#!/usr/bin/env python3

import sys

def volume(A, h, d):
    return '{0:.{1}f}'.format(float(A) * float(h) / 3, d)

if __name__ == '__main__':
    print(volume(*sys.argv[1:]))
