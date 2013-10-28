#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import os.path
import re

from logconfig import logger
from rename import EpisodeNames
from collections import defaultdict
from collections import deque
from time import time
from cpstat import moveAndPrintProgress
import math

ENDINGS = {"avi", "mkv", "mp4"}
PREFIXES = {0: "", 1: "k", 2: "M", 3: "G", 4: "T"}


def formatsize(size):
    if size == 0:
        return "0 B"
    length = math.floor(math.log10(size))
    prefix = PREFIXES[int(math.floor(length / 3))]
    return "{} {}B".format(round(size / math.pow(10, (math.floor(length / 3) * 3)), 1), prefix)


def getFileEnding(name):
    endingmatch = re.search("[^\.]+$", name)
    if endingmatch is None:
        logger.warn("no ending found for file: %s" % name)
        return None
    return endingmatch.group()


def moveFileToDir(srcpath, dest):
    if not os.path.exists(dest):
        logger.info("creating dir %s" % dest)
        os.mkdir(dest)
    fname = os.path.basename(srcpath)
    logger.info("moving from %s to %s", srcpath, dest)
    destpath = os.path.join(dest, fname)
    while os.path.exists(destpath):
        destpath += "_"
    os.rename(srcpath, destpath)
    print("os.rename(%s, os.path.join(%s, %s))".format(srcpath, dest, fname))
    return


def moveFileToCorrectDirectory(targetpath, sourcefilepath, newfilename):
    filename = os.path.basename(sourcefilepath)
    match = re.search("^[0-9]+", newfilename)
    if match is None:
        logger.warn("cannot determine season-dir for %s" % filename)
        return
    season = match.group()
    targetdir = os.path.join(targetpath, season)
    if os.path.dirname(sourcefilepath) == targetdir:
        logger.info("%s is in the correct directory" % filename)
        return
    logger.info("%s should be moved" % filename)
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)
    moveAndPrintProgress(sourcefilepath, os.path.join(targetdir, newfilename))


def getMatcherString(entry):
    result = re.sub("^[Tt]he*", "", entry)
    result = result.lstrip()
    result = re.sub("\s", ".", result)
    logger.debug("converted to regex: " + result)
    return re.compile(result, re.IGNORECASE)


def findDestDirectory(base, entries):
    logger.info("finding dest-directory for " + base)
    logger.debug(entries)
    for name, e in entries.items():
        match = e.search(base)
        if match is not None:
            logger.info("found match for " + base + ": " + name)
            return name


class EpisodeNamesCache():
    def __init__(self):
        self.data = dict()

    def get(self, key):
        if key not in self.data:
            self.data[key] = EpisodeNames(key)
        return self.data[key]


def main():
    print("main")
    if len(sys.argv) > 1:
        sourcepath = sys.argv[1]
    if len(sys.argv) > 2:
        targetpath = sys.argv[2]

    series_list = os.listdir(targetpath)
    search_patterns = dict([(e, getMatcherString(e)) for e in series_list])
    cache = EpisodeNamesCache()

    for dirpath, dirnames, filenames in os.walk(sourcepath):
        for f in filenames:
            if getFileEnding(f) not in ENDINGS:
                continue
            series = findDestDirectory(f.rstrip(), search_patterns)
            if series is None:
                continue
            episode_names = cache.get(series)
            newfilename = episode_names.getNewFileName(f) + "." + getFileEnding(f)
            try:
                moveFileToCorrectDirectory(os.path.join(targetpath, series), os.path.join(dirpath, f), newfilename)
            except IOError as e:
                logger.warn("could not move file to correct directory.")
                logger.warn(str(e))
                continue


if __name__ == "__main__":
    main()
