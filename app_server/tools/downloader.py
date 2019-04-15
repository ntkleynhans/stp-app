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
LOGNAME = "DOWNLOADER"
LOGFNAME = "downloader.log"
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

USERS = None

class Downloader:

    def __init__(self, config):
        self.user_password = config['user_password']
        self.user_token = None
        self.project_id = None
        self.project_user = config['project_user']
        self.project_token = None

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
            LOG.info("Listing projects")
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.project_token }
            res = requests.post(BASEURL + "projects/listprojects", headers=headers, data=json.dumps(data))
            LOG.info('loadproject(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            pkg = res.json()
            self.project_info = pkg['projects']
        else:
            LOG.info("User not logged in!")

    def login(self, user):
        """
            Login as user
            Place user 'token' in self.user_token
        """
        if self.user_token is None:
            LOG.info("{} logging in".format(user))
            headers = {"Content-Type" : "application/json"}
            data = {"username": user, "password": self.user_password, "role" : 'editor'}
            res = requests.post(BASEURL + "editor/login", headers=headers, data=json.dumps(data))
            LOG.info('login(): SERVER SAYS:{}'.format(res.text))
            pkg = res.json()
            self.user_token = pkg['token']
            self.username = user
        else:
            LOG.info("User logged in already!")

    def logout(self):
        """
            Logout as user
        """
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token}
            res = requests.post(BASEURL + "editor/logout", headers=headers, data=json.dumps(data))
            LOG.info('logout(): SERVER SAYS:{}'.format(res.text))
            self.user_token = None
        else:
            LOG.info("User not logged in!")

    def loadtasks(self):
        """
            Load all tasks belonging to neil
        """
        LOG.info("username={}: loadtasks(): Entering".format(self.username))
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token}
            res = requests.post(BASEURL + "editor/loadtasks", headers=headers, data=json.dumps(data))
            print('SERVER SAYS:', res.text)
            print(res.status_code)
            pkg = res.json()
            if len(pkg['collator']) > 0:
                self.all_tasks = pkg["collator"]
            else:
                print('No tasks to select')
		self.all_tasks = []
                LOG.info("username={}: loadtasks(): No tasks to select!".format(self.username))
        else:
            print("User not logged in!")
            LOG.error("username={}: loadtasks(): User not logged in!".format(self.username))
        print('')

    def gettext(self, projectid, taskid):
        """
            Return the task's text
        """
        LOG.info("username={}: gettext(): Entering".format(self.username))
        if self.user_token is not None:
            headers = {"Content-Type" : "application/json"}
            data = {'token' : self.user_token, 'projectid' : projectid, 'taskid' : taskid}
            res = requests.post(BASEURL + "editor/gettext", headers=headers, data=json.dumps(data))
            LOG.info("username={}: gettext(): {}".format(self.username, res.text))
            print(res.status_code)
            pkg = res.json()
            return pkg['text']
        else:
            print("User not logged in!")
            LOG.error("username={}: gettext(): User not logged in!".format(self.username))
        print('')

if __name__ == "__main__":
    if not os.path.exists('config.json'):
        print('ERROR: cannot load config.json file in current folder')
        sys.exit(1)

    config = json.load(open('config.json'))
    USERS = config['downloader']['USERS']
    BASEURL = config['baseurl']
    downloader = Downloader(config)

    downloader.login_project()
    downloader.listprojects()
    downloader.logout_project()
    project_info = {}
    for project in downloader.project_info:
        project_info[project['projectid']] = project['projectname']

    file = codecs.open("transcriptions.txt", "w", "utf-8")
    for user in USERS:
        downloader.login(user)
        downloader.loadtasks()
        for task in downloader.all_tasks:
            text = downloader.gettext(task['projectid'], task['taskid'])
            projectname = project_info[task['projectid']]
            file.write("{};{}\n".format(projectname, text))
        downloader.logout()
    file.close()

