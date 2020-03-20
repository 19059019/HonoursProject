#!/usr/bin/env python3
# vim: textwidth=79 tabstop=4 shiftwidth=4 expandtab:

def qsolve(a, b, c):
    d = b**2 - 4*a*c
    return (-b + d**0.5)/(2*a), (-b - d**0.5)/(2*a)

if __name__ == "__main__":
    import sys
    a = float(sys.argv[1])
    b = float(sys.argv[2])
    c = float(sys.argv[3])
    for x in qsolve(a, b, c):
        print('x = {}, eval = {}'.format(x, a*x*x + b*x + c))
