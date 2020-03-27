#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *
import os

cpu = CPU()

if __name__ == '__main__':
    path = ''
    if len(sys.argv) == 1:
        path = os.path.join('examples', 'sctest.ls8')
    elif len(sys.argv) == 2:
        path = os.path.join('examples', sys.argv[1])
    cpu.load(path)
    cpu.run()

