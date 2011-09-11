#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import sys

from logconfig import *


def getMatcherString(entry):
    result = re.sub("^[Tt]he*", "", entry)
    result = re.sub("\s", ".", result)
    return re.compile(result, re.IGNORECASE)

def findDestDirectory(base, entries):
    for name, e in entries.iteritems():
        match = e.match(base)
        if match != None:
            logger.info("found match for " + base + ": " + name)
            return name

def findNewFiles(remotedir, ending, host):
    findtemplate = "find \"%s\" -iname '*.%s'"
    command = findtemplate % (remotedir, ending)
    if host != None:
        command = "ssh " + host + " " + command

    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    return [ f.rstrip() for f in proc.stdout.readlines() ]

def main():
    host=None
    remotedir=""
    lookupdir=""
    if(len(sys.argv) == 4):
        host = sys.argv[1]
        remotedir=sys.argv[2]
        lookupdir=sys.argv[3]
    elif(len(sys.argv) == 3):
        remotedir=sys.argv[1]
        lookupdir=sys.argv[2]
    else:
        print "missing merge-path"
        sys.exit(2)

    entries = os.listdir(lookupdir)

    patterns = dict([(e, getMatcherString(e)) for e in entries])
    logger.debug(patterns.keys())

    newFiles = findNewFiles(remotedir, "avi", host)
    newFiles += findNewFiles(remotedir, "mkv", host)

    logger.debug("Counted %s new files." % len(newFiles))
    for f in newFiles:
        base = os.path.basename(f)
        series = findDestDirectory(base.rstrip(), patterns)
        if series == None:
            logger.warn("nothing found for " + f)
            continue
        dest = os.path.join(lookupdir, series)
        if host == None:
            source = f
        else:
            source = "%s:\"%s\"" % (host, f)
        command = ["rsync", "-hv", "--progress", "--remove-source-files", source , dest]
        logger.debug(" ".join(command))
        retcode = subprocess.call(command)
        subprocess.call([os.path.join(sys.path[0], "./rename.py"), dest])
        subprocess.call([os.path.join(sys.path[0], "./sorter.py"), dest])

if __name__ == "__main__":
    main()