#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import sys

from renamer.logconfig import logger

ENDINGS = {"mkv", "avi", "mp4"}


def getMatcherString(entry):
    result = re.sub("^[Tt]he*", "", entry)
    result = result.lstrip()
    result = re.sub("\s", ".", result)
    logger.debug("converted to regex: " + result)
    return re.compile(result, re.IGNORECASE)


def findDestDirectory(base, entries):
    logger.info("finding dest-directory for " + base)
    logger.debug(entries)
    for name, e in entries.iteritems():
        match = e.search(base)
        if match is not None:
            logger.info("found match for " + base + ": " + name)
            return name


def main():
    host = None
    if len(sys.argv) == 4:
        host = sys.argv[1]
        remotedir = sys.argv[2]
        lookupdir = sys.argv[3]
    elif len(sys.argv) == 3:
        remotedir = sys.argv[1]
        lookupdir = sys.argv[2]
    else:
        print("missing merge-path")
        sys.exit(2)

    entries = os.listdir(lookupdir)

    patterns = dict([(e, getMatcherString(e)) for e in entries])
    logger.debug(patterns.keys())

    logger.debug("Counted %s new files." % len(newFiles))
    for f in newFiles:
        base = os.path.basename(f)
        series = findDestDirectory(base.rstrip(), patterns)
        if series is None:
            logger.warn("nothing found for " + f)
            continue
        dest = os.path.join(lookupdir, series)
        if host is None:
            source = f
        else:
            source = "%s:\"%s\"" % (host, f)
#        command = ["rsync", "-hv", "--progress", "--remove-source-files", source , dest]
        command = ["cp", source, dest]
        logger.debug(" ".join(command))
        retcode = subprocess.call(command)
        subprocess.call([os.path.join(sys.path[0], "./rename.py"), dest])
        subprocess.call([os.path.join(sys.path[0], "./sorter.py"), dest])

if __name__ == "__main__":
    main()
