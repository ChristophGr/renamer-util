#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import subprocess

logging.basicConfig(format='%(asctime)-15s %(module)s:%(lineno)s %(levelname)s %(message)s')
logger = logging.getLogger("rename")

if subprocess.call("tty") > 0:
    hdlr = logging.FileHandler('rename.log')
    formatter = logging.Formatter('%(asctime)-15s %(module)s:%(lineno)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
