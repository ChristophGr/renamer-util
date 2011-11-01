#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import string
import tempfile
import copy
from datetime import date
from difflib import Differ

import time

from logconfig import *

endings = ["mkv", "avi"]
patterns = [
             "(\d{1,2})x(\d{2})(-(\d{2}))?", #01x02-03
             "S(\d{2})E(\d{2})(-(\d{2}))?", #S01E02-3
             "(\d{1,2})(\d{2})(-(\d{2}))?", #102-03
             "(\d{1,2})-(\d{2})(-(\d{2}))?", #01-02
           ]

def download(url, dest):
    import urllib
    webFile = urllib.urlopen(url)
    localFile = open(dest, 'w')
    localFile.write(webFile.read())
    webFile.close()
    localFile.close()

def getBaseNameFromPath(path):
    path = re.sub("/$", "", path)
    base = os.path.basename(path)
    base = re.sub("^[Tt]he*", "", base)
    base = re.sub("\s+", "", base)
    return base

def updateCacheForSeries(base):
    url = "http://epguides.com/" + base
    tmpdir = tempfile.gettempdir() + "/renamer"
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    tmpf = tmpdir + "/" + base
    if not os.path.exists(tmpf) or (date.today() - date.fromtimestamp(os.path.getmtime(tmpf))).days > 0:
            logger.info("downloading " + url)
            download(url, tmpf)
    return tmpf

def readEpisodeListFromFile(tmpf):
    contentfile = open(tmpf, 'r')
    episodes = dict()
    for line in contentfile.xreadlines():
        logger.debug("read line: %s" % line)
        epIdMatch = re.search("\s+[1-9][0-9]?\-[0-9]{2}\s+", line)
        if epIdMatch != None:
            epid = epIdMatch.group().rstrip().lstrip()
            logger.info("matched %s" % epid)
            splitted = epid.split("-")
            logger.info(splitted)
            season = int(splitted[0])
            episodenum = int(splitted[1])

            if not season in episodes:
                episodes[season] = dict()

            linkstring = re.search("<a[^<]+</a>", line).group()
            logger.info("link-string: %s" % linkstring)
            epname = linkstring[linkstring.find(">") + 1:linkstring.find("</")]
            logger.info("name is %s" % epname)
            episodes[season][episodenum] = epname
    contentfile.close();
    return episodes

def splitid(idmatch):
    return [ idmatch.group(1), idmatch.group(2), idmatch.group(4), ]

def rreplace(s, old, new, count = 1):
    return (s[::-1].replace(old[::-1], new[::-1], count))[::-1]

def getNewFileName(episodes, f):
    if(f == None):
        raise
        
    logger.info("get new filename for %s" % f)
    for p in patterns:
        mid = re.search(p, f, re.IGNORECASE)
        if(mid == None):
            continue
        ids = splitid(mid)
        season = int(ids[0])
        episode1 = int(ids[1])
        episode2 = int(ids[2] or episode1)

        names = []
        for x in range(episode1, episode2 + 1):
            if not season in episodes:
                logger.warn("missing season %s from episodelist" % season)
                continue
            seasonepisodes = episodes[season]
            if not x in seasonepisodes:
                logger.warn("missing episode %s in season %s" % (x, season))
                continue
            nextname = seasonepisodes[x]
            nextname = re.sub("[!:\?\\\\\\/]+", "_", nextname)
            if len(names) > 0:
                print "multi-episode found, %s" % f
                d = Differ()
                result = list(int(i[2]) for i in d.compare(names[0],nextname) if i[0] in ['-','+'] and i[2].isdigit())
                if len(result) == 2:
                    names[0] = rreplace(names[0], str(result[0]), "%s+%s" % (result[0],result[1]))
                    # print names[0]
                else:
                    names.append(nextname)
            else:
                names.append(nextname)

            if x in episodes[season]:
                del episodes[season][x]
        if len(names) == 0:
            return None
        name = " - ".join(names)
        epidname = string.zfill(episode1, 2)
        if episode2 != episode1:
            epidname += "-" + string.zfill(episode2, 2)
        return "%sx%s - %s" % (season, epidname, name)

def getFileEnding(name):
    endingmatch = re.search("[^\.]+$", name)
    if endingmatch == None:
        logger.warn("no ending found for file: %s" % name)
        return None
    return endingmatch.group()

def printAllEpisodes(episodesDict):
    for s, eps in episodesDict.iteritems():
        if len(eps) > 0:
            print "Season %s" % s
            print(eps.keys())

def logrename(path, entry):
    logfile = open(path + "/move.log", "a")
    logger.info(entry)
    logfile.write(entry)
    logfile.write("\n")
    logfile.close()

def getContainingDirectoryName(filename):
    containerdir = os.path.dirname(filename)
    return os.path.split(containerdir)[1]

episodes = dict()

def getBaseNameFromFile(path):
    f = open(os.path.join(path, ".epguide"))
    name = f.readline()
    f.close()
    return name
    
def main():
    path = sys.argv[1]

    base = None
    if os.path.exists(os.path.join(path, ".epguide")):
        base = getBaseNameFromFile(path)
    else:
        base = getBaseNameFromPath(path)
    tmpf = updateCacheForSeries(base)

    episodes = readEpisodeListFromFile(tmpf)
    episodescopy = copy.deepcopy(episodes)

    def visit(arg, dirname, names):
        for f in names:
            ending = getFileEnding(f)
            if not os.path.isdir(f) and (ending in endings):
                newFileName = getNewFileName(episodescopy, f)
                logger.info("got new filename %s" % newFileName)
                if newFileName == None:
                    logger.warn("No new filename found for %s" % f)
                    continue
                newFileName += "." + ending
                if newFileName == os.path.basename(f):
                    continue
                logrename(path, "mv \"%s\" -> \"%s\"\n" % (f, os.path.basename(newFileName)))
                srcFileName = dirname + "/" + f
                dstFileName = dirname + "/" + newFileName
                # workaround for case-insentitive file-systems
                intFileName = "%s_%d" % (srcFileName, time.time())
                os.rename(srcFileName, intFileName)
                os.rename(intFileName, dstFileName)

    os.path.walk(path, visit, 0)

    print("missing episodes: ")
    printAllEpisodes(episodescopy)

if __name__ == "__main__":
    main()
