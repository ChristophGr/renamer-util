#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os.path
import subprocess
import re

def findAllFilesWithExt(path, ext):
    cmd = "find \"%s\" -iname '*.%s'" % (path, ext)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return [ f.rstrip() for f in proc.stdout.readlines() ]

path = sys.argv[1]
files = findAllFilesWithExt(path, "mkv")
files += findAllFilesWithExt(path, "avi")

def moveFileToDir(srcpath, dest):
    if not os.path.exists(dest):
        os.mkdir(dest);
    fname = os.path.basename(srcpath)
    os.rename(srcpath, os.path.join(dest, fname))
    print "os.rename(%s, os.path.join(%s, %s))" % (srcpath, dest, fname)
    return

for f in files:
    filename =  os.path.basename(f)
    match = re.search("^[0-9]+", filename)
    if match == None:
        continue;
    season = match.group()
    print season
    relpath = os.path.relpath(f, path)
    seasondir = os.path.dirname(relpath)
    print seasondir
    if season != seasondir:
        print "orig: %s" % (f)
        os.path.join(path, season)
        print "new: %s" % (os.path.join(path, season))
        moveFileToDir(f, os.path.join(path, season))

