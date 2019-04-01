#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Create initial project table
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Neil Kleynhans"
__email__ = "ntkleynhans@gmail.com"

import os
import argparse
try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite #for old Python versions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("outfn", metavar="OUTFN", type=str, help="Output DB filename.")
    args = parser.parse_args()
    outfn = args.outfn
    
    db_conn = sqlite.connect(outfn)
    db_curs = db_conn.cursor()
    db_curs.execute("CREATE TABLE projects ({})".format(", ".join(["projectid VARCHAR(36) PRIMARY KEY",
                                                                   "projectname VARCHAR(32)",
                                                                   "category VARCHAR(36)",
                                                                   "creator VARCHAR(30)",
                                                                   "projectmanager VARCHAR(30)",
                                                                   "collator VARCHAR(30)",
                                                                   "audiofile VARCHAR(128)",
                                                                   "audiodur REAL",
                                                                   "year INTEGER",
                                                                   "creation REAL",
                                                                   "assigned VARCHAR(1)",
                                                                   "jobid VARCHAR(36)",
                                                                   "projectstatus VARCHAR(30)",
                                                                   "errstatus VARCHAR(128)"])))
    db_curs.execute("CREATE TABLE incoming ({})".format(", ".join(["projectid VARCHAR(36)",
                                                                   "taskid INTEGER",
                                                                   "url VARCHAR(128)",
                                                                   "servicetype VARCHAR(128)"])))
    db_curs.execute("CREATE TABLE outgoing ({})".format(", ".join(["projectid VARCHAR(36)",
                                                                   "url VARCHAR(128)",
                                                                   "audiofile VARCHAR(128)",
                                                                   "start REAL",
                                                                   "end REAL"])))
    db_curs.execute("CREATE TABLE message ({})".format(", ".join(["key VARCHAR(36)",
                                                                  "message VARCHAR(128)"])))
    db_conn.commit()

