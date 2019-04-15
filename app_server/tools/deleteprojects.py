#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function

import requests
import sys
import json
import os
import codecs
import logging
import logging.handlers

# Some constants
BASEURL = None

# Format the logger output
class CustomFormatter(logging.Formatter):
  """Custom formatter, overrides funcName with value of funcname if it
     exists
  """
  def format(self, record):
    if hasattr(record, 'funcname'):
        record.funcName = record.funcname
    return super(CustomFormatter, self).format(record)

# Editor testing logging
LOGNAME = "DELETEPROJECT"
LOGFNAME = "deleteproject.log"
LOGLEVEL = logging.DEBUG
try:
  fmt = "%(asctime)s [%(levelname)s] %(name)s in %(funcName)s(): %(message)s"
  LOG = logging.getLogger(LOGNAME)
  formatter = CustomFormatter(fmt)
  ofstream = logging.handlers.TimedRotatingFileHandler(LOGFNAME, when="D", interval=1, encoding="utf-8")
  ofstream.setFormatter(formatter)
  LOG.addHandler(ofstream)
  LOG.setLevel(LOGLEVEL)
except Exception as e:
  print("FATAL ERROR: Could not create logging instance: {}".format(e), file=sys.stderr)
  sys.exit(1)

class Downloader:

    def __init__(self, config):
        self.user_password = config['user_password']
        self.user_token = None
        self.project_id = None
        self.project_user = config['project_user']
        self.project_token = None
        BASEURL = config['baseurl']

    def login_project(self):
        """
            Login as user
            Place user 'token' in self.user_token
        """
        if self.project_token is None:
            LOG.info("{} logging in".format(self.project_user))
            headers = {"Content-Type" : "application/json"}
            data = {"username": self.project_user, "password": self.user_password, "role" : 'project'}
            res = requests.post(BASEURL + "projects/login", headers=headers, data=json.dumps(data))
            LOG.info('login(): SERVER SAYS:{}'.format(res.text))
            pkg = res.json()
            self.project_token = pkg['token']
        else:
            LOG.info("User logged in already!")

    def logout_project(self):
        """
            Logout as user
        """
        if self.project_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.project_token}
            res = requests.post(BASEURL + "projects/logout", headers=headers, data=json.dumps(data))
            LOG.info('logout(): SERVER SAYS:{}'.format(res.text))
            self.project_token = None
        else:
            LOG.info("User not logged in!")

    def listprojects(self):
        """
        """
        if self.project_token is not None:
            LOG.info("Creating project")
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.project_token }
            res = requests.post(BASEURL + "projects/listprojects", headers=headers, data=json.dumps(data))
            LOG.info('loadproject(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            pkg = res.json()
            self.project_info = pkg['projects']
        else:
            LOG.info("User not logged in!")

    def deleteproject(self, projectid):
        """
            Delete Project
        """
        if self.project_token is not None:
            LOG.info("Deleting Project -- {}".format(projectid))
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.project_token, "projectid" : projectid}
            res = requests.post(BASEURL + "projects/deleteproject", headers=headers, data=json.dumps(data))
            LOG.info('deleteproject(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            self.projectid = None
        else:
            LOG.info("User not logged in!")


if __name__ == "__main__":
    if not os.path.exists('config.json'):
        print('ERROR: cannot load config.json file in current folder')
        sys.exit(1)

    config = json.load(open('config.json'))
    downloader = Downloader(config)

    downloader.login_project()
    downloader.listprojects()
    for project in downloader.project_info:
        print('Deleting project -- {}'.format(project['projectid']))
        downloader.deleteproject(project['projectid'])
    downloader.logout_project()

