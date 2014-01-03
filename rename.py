#!/usr/bin/python3
# -*- coding: utf-8 -*-
import codecs
import sys
import os
import os.path
import re
import tempfile
import copy
from datetime import date
from difflib import Differ
import urllib.request
import time
from collections import defaultdict

from logconfig import logger

endings = ["mkv", "avi", "mp4"]
patterns = [
    "(\d{1,2})x(\d{2})(-(\d{2}))?", #01x02-03
    "S(\d{2})E(\d{2})(-(\d{2}))?", #S01E02-3
    "(\d{1,2})(\d{2})(-(\d{2}))?", #102-03
    "(\d{1,2})-(\d{2})(-(\d{2}))?", #01-02
]


def download(url, dest):
    urllib.request.urlretrieve(url, dest)


def updateCacheForSeries(base):
    url = "http://epguides.com/" + base
    tmpdir = os.path.join(tempfile.gettempdir(), "renamer")
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    tmpf = os.path.join(tmpdir, base)
    if not os.path.exists(tmpf) or (date.today() - date.fromtimestamp(os.path.getmtime(tmpf))).days > 0:
        logger.info("downloading " + url)
        download(url, tmpf)
    return tmpf


def readEpisodeListFromFile(tmpf):
    with codecs.open(tmpf, encoding='cp1252') as contentfile:
        episodes = defaultdict(dict)  # lambda: defaultdict(dict)
        for line in contentfile:
            logger.debug("read line: %s" % line)
            epIdMatch = re.search("\s+([1-9][0-9]?)\-\s*([0-9][0-9]?)\s+", line)
            if epIdMatch is None:
                continue
            season = int(epIdMatch.group(1))
            episodenum = int(epIdMatch.group(2))
            epname = re.search("<a[^>]+>([^<]+)</a>", line).group(1)
            logger.debug("name is %s" % epname)
            episodes[season][episodenum] = epname
        return episodes


def splitid(idmatch):
    return [idmatch.group(1), idmatch.group(2), idmatch.group(4), ]


def rreplace(s, old, new, count=1):
    return (s[::-1].replace(old[::-1], new[::-1], count))[::-1]


def getFileEnding(name):
    endingmatch = re.search("[^\.]+$", name)
    if endingmatch is None:
        logger.warn("no ending found for file: %s" % name)
        return None
    return endingmatch.group()


def printAllEpisodes(episodesDict):
    for s, eps in episodesDict:
        if len(eps) > 0:
            print("Season {}".format(s))
            print(eps.keys())


def logrename(path, entry):
    with open(path + "/move.log", "a") as logfile:
        logger.info(entry)
        logfile.write(entry)
        logfile.write("\n")


def getSeriesNameForPath(path):
    if os.path.exists(os.path.join(path, ".epguide")):
        with open(os.path.join(path, ".epguide")) as f:
            return f.readline()
    else:
        path = re.sub("/$", "", path)  # remove trailing slash
        base = os.path.basename(path)
        base = re.sub("^[Tt]he*", "", base)  # remove leading "the" from series name
        base = re.sub("\s+", "", base)  # remove spaces
        return base


def build_episode_cache(series_path):
    base = getSeriesNameForPath(series_path)
    tmpf = updateCacheForSeries(base)
    episodes = readEpisodeListFromFile(tmpf)
    return episodes


class EpisodeNames:
    def __init__(self, series_path):
        self.episodes = build_episode_cache(series_path)

    def getEpisodeName(self, season, episodenumber):
        return self.episodes[season][episodenumber]

    def getEpisodeTitles(self, season, episode1, episode2):
        names = []
        for x in range(episode1, episode2 + 1):
            nextname = self.getEpisodeName(season, x)
            if nextname is None:
                logger.warn("missing season %s from episodelist" % season)
                continue
            nextname = re.sub("[!:\?\\\\\\/]+", "_", nextname)  # replace characters not allowed in filenames
            if len(names) > 0:
                d = Differ()
                result = list(int(i[2]) for i in d.compare(names[0], nextname) if i[0] in ['-', '+'] and i[2].isdigit())
                if len(result) == 2:
                    names[0] = rreplace(names[0], str(result[0]), "{}+{}".format(result[0], result[1]))
                else:
                    names.append(nextname)
            else:
                names.append(nextname)
        return names

    def findEpisodeIdentifier(self, f):
        for p in patterns:
            seasonAndEpisode = re.search(p, f, re.IGNORECASE)
            if seasonAndEpisode is not None:
                return seasonAndEpisode
        return None

    def get_episode_identifier(self, f):
        groups = self.findEpisodeIdentifier(f).groups()
        return int(groups[0]), int(groups[1])

    def getNewFileName(self, f):
        logger.debug("get new filename for {}".format(f))
        f = re.sub("x264", "", f)
        seasonAndEpisode = self.findEpisodeIdentifier(f)
        if seasonAndEpisode is None:
            logger.warn("could not find identifier on ", f)
            return None
        season = int(seasonAndEpisode.group(1))
        episode1 = int(seasonAndEpisode.group(2))
        episode2 = int(seasonAndEpisode.group(4) or episode1)

        names = self.getEpisodeTitles(season, episode1, episode2)
        if len(names) == 0:
            logger.warn("could not find name for ", f)
            return None
        name = " - ".join(names)
        epidname = str(episode1).zfill(2)
        if episode2 != episode1:
            epidname += "-" + str(episode2).zfill(2)
        return "{}x{} - {}".format(season, epidname, name)

    def doRename(self, directory, filename):
        try:
            newFileName = self.getNewFileName(filename)
        except KeyError:
            return None
        if newFileName is None:
            logger.warn("No new filename found for {}".format(filename))
            return
        newFileName = str(newFileName) + "." + getFileEnding(filename)
        if newFileName == filename:
            return
        logrename(directory, "mv \"{}\" -> \"{}\"\n".format(filename, os.path.basename(newFileName)))
        srcFileName = os.path.join(directory, filename)
        dstFileName = os.path.join(directory, newFileName)
        while os.path.exists(dstFileName):
            dstFileName += "_"
        # workaround for case-insentitive file-systems
        intFileName = "{}_{}".format(srcFileName, time.time())
        logger.debug("move via ", intFileName)
        os.rename(srcFileName, intFileName)
        os.rename(intFileName, dstFileName)
        return newFileName


def main():
    if len(sys.argv) > 1:
        series_path = sys.argv[1]
    else:
        return
    print(getSeriesNameForPath(series_path))
    cache = EpisodeNames(series_path)
    missing = copy.deepcopy(cache.episodes)
    for dirpath, dirnames, filenames in os.walk(series_path):
        for f in filenames:
            if getFileEnding(f) in endings:
                cache.doRename(dirpath, f)
                season, num = cache.get_episode_identifier(f)
                try:
                    del missing[season][num]
                except KeyError:
                    pass

    for key, value in list(missing.items()):
        if len(value) == 0:
            del missing[key]

    for season, episodes in missing.items():
        print("SEASON: {}".format(season))
        print("\t {}".format(sorted(list(episodes.keys()))))


if __name__ == "__main__":
    main()
