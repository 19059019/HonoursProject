#!/usr/bin/env python3
# vim: textwidth=79 tabstop=4 shiftwidth=4 expandtab:

def sort3(x, y, z):
    minval = min(x, y, z)
    maxval = max(x, y, z)
    midval = x + y + z - maxval - minval
    return minval, midval, maxval

if __name__ == "__main__":
    import sys
    x = int(sys.argv[1])
    y = int(sys.argv[2])
    z = int(sys.argv[3])
    a, b, c = sort3(x, y, z)
    print("{}, {}, {}".format(a, b, c))
