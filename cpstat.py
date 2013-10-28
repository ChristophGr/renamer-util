#!/usr/bin/python3
import sys
import subprocess
import os
import time
import threading
import collections
import math
import shutil

PREFIXES = {0: "", 1: "k", 2: "M", 3: "G", 4: "T"}
TIMEOUT = .3


def formatsize(size):
    if size <= 0:
        return "0 B"
    logvalue = math.log10(size)
    length = math.floor(math.log10(size))
    prefix = PREFIXES[math.floor(length / 3)]
    return "{} {}B".format(round(size / math.pow(10, (math.floor(length / 3) * 3)), 1), prefix)


class Progress:
    def __init__(self, srcfile, dstfile):
        self._stopped = False
        self._buf = collections.deque(maxlen=5)
        self.srcfile = srcfile
        self.dstfile = dstfile
        self.totalsize = os.stat(os.path.realpath(self.srcfile)).st_size
        print("{} -> {}".format(srcfile, dstfile))

    def showprogress(self):
        while not self._stopped and (
                not os.path.exists(os.path.realpath(self.srcfile)) or not os.path.exists(os.path.realpath(self.dstfile))):
            continue
        while not self._stopped:
            if not os.path.exists(os.path.realpath(self.srcfile)) or not os.path.exists(os.path.realpath(self.dstfile)):
                continue
            partsize = os.stat(os.path.realpath(self.dstfile)).st_size
            self._buf.append(partsize)
            speed = (self._buf[-1] - self._buf[0]) / len(self._buf) / TIMEOUT
            progress = round(partsize * 100 / self.totalsize, 2)
            sys.stdout.write("{}% ({}/s)          \r".format(progress, formatsize(speed)))
            sys.stdout.flush()
            time.sleep(TIMEOUT)

    def stop(self):
        self._stopped = True


#def showprogress(srcfile, dstfile):
#    buf = collections.deque(maxlen=5)
#    print("{} -> {}".format(srcfile, dstfile))



def moveAndPrintProgress(srcfile, dstfile):
    p = Progress(srcfile, dstfile)
    t = threading.Thread(target=p.showprogress)
    t.daemon = True
    t.start()
    shutil.move(srcfile, dstfile)
    p.stop()


def main():
    print(sys.argv[1:]);
    srcfile = sys.argv[1]
    dstfile = sys.argv[2]
    copyAndPrintProgress(srcfile, dstfile)


if __name__ == "__main__":
    main()