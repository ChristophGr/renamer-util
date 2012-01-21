#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os.path
import subprocess
import re

from logconfig import *

def findAllFilesWithExt(path, ext):
    cmd = "find \"%s\" -iname '*.%s'" % (path, ext)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return [ f.rstrip() for f in proc.stdout.readlines() ]

path = sys.argv[1]
files = findAllFilesWithExt(path, "mkv")
files += findAllFilesWithExt(path, "avi")
files.sort()

logger.info("found files %s" % files)

def moveFileToDir(srcpath, dest):
    if not os.path.exists(dest):
        logger.info("creating dir %s" % dest)
        os.mkdir(dest);
    fname = os.path.basename(srcpath)
    logger.info("moving from %s to %s", srcpath, dest)
    destpath = os.path.join(dest, fname)
    while os.path.exists(destpath):
        destpath += "_"
    os.rename(srcpath, destpath)
    print "os.rename(%s, os.path.join(%s, %s))" % (srcpath, dest, fname)
    return

for f in files:
    filename =  os.path.basename(f)
    match = re.search("^[0-9]+", filename)
    if match == None:
        logger.warn("cannot determine season-dir for %s" % f)
        continue;
    season = match.group()
    relpath = os.path.relpath(f, path)
    seasondir = os.path.dirname(relpath)
    logger.info("checking %s" % f)
    if season != seasondir:
        logger.info("%s should be moved" % f)
        print "orig: %s" % (f)
        os.path.join(path, season)
        print "new: %s" % (os.path.join(path, season))
        moveFileToDir(f, os.path.join(path, season))
    else:
        logger.info("%s is in the correct directory" % f)

