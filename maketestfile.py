#!/usr/bin/env python
# -*- coding:utf-8; mode:python-mode -*-

import sys
import os, os.path
import shutil


copy = 3

def main():
    d = sys.argv[1]
    a = os.listdir(d)

    os.chdir(d)

    for i in xrange(copy):
        for f in a:
            name, ext = os.path.splitext(os.path.abspath(f))
            fname = ('%s__%d%s' % (name, i, ext) )
            shutil.copy(os.path.abspath(f), fname)



if __name__ == '__main__':
    main()
