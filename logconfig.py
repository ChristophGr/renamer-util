#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import subprocess

logging.basicConfig(format='%(asctime)-15s %(module)s:%(lineno)s %(levelname)s %(message)s')
logger = logging.getLogger("rename")
logger.setLevel(logging.INFO)

#if(subprocess.call("tty -s") > 0):
if True:
    hdlr = logging.FileHandler('rename.log')
    formatter = logging.Formatter('%(asctime)-15s %(module)s:%(lineno)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
