#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import json
import os
import logging
import logging.handlers
import codecs

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
LOGNAME = "CREATEUSERS"
LOGFNAME = "createusers.log"
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

class Uploader:

    def __init__(self, config):
        self.admin_password = config['admin_password']
        self.user_password = config['user_password']
        self.admin_token = None
        self.user_token = None
        self.editor_user_token = None
        self.project_user = config['project_user']
        self.projectmanager = config['projectmanager']
        self.collator = config['collator']
        self.project_id = None

    def adminlin(self):
        """
            Login as admin
            Place admin 'token' in self.admin_token
        """
        if self.admin_token is None:
            LOG.info("Admin logging in")
            res = self._requests("admin/login", {"username": "root", "password": self.admin_password, "role" : "admin"})
            LOG.info('adminlin(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            pkg = res.json()
            self.admin_token = pkg['token']
        else:
            LOG.info("Admin logged in already!")

    def adminlout(self):
        """
            Logout as admin
        """
        if self.admin_token is not None:
            LOG.info("Admin logging out")
            res = self._requests("admin/logout", {"token": self.admin_token})
            LOG.info('adminlout(): SERVER SAYS:{}'.format(res.text))
            self.admin_token = None
        else:
            LOG.info("Admin not logged in!")

    def adduser(self, user):
        """
            Add automatically generated users to database
        """
        if self.admin_token is not None:
            LOG.info("Adding user {}".format(user))
            data = {"token": self.admin_token, "username": USERS[user]["username"], "password": USERS[user]["password"],
             "name": USERS[user]["name"], "surname": USERS[user]["surname"], "email": USERS[user]["email"],
             "role": USERS[user]["role"]}
            res = self._requests("admin/adduser", data)
            LOG.info('adduser(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
        else:
            LOG.info("Admin not logged in!")

    def login(self):
        """
            Login as user
            Place user 'token' in self.user_token
        """
        if self.user_token is None:
            LOG.info("{} logging in".format(self.project_user))
            res = self._requests("projects/login", {"username": self.project_user, "password": self.user_password, "role" : 'project'})
            LOG.info('login(): SERVER SAYS:{}'.format(res.text))
            pkg = res.json()
            self.user_token = pkg['token']
        else:
            LOG.info("User logged in already!")

    def logout(self):
        """
            Logout as user
        """
        if self.user_token is not None:
            res = self._requests("projects/logout", {"token": self.user_token})
            LOG.info('logout(): SERVER SAYS:{}'.format(res.text))
            self.user_token = None
        else:
            LOG.info("User not logged in!")

    def _requests(self, path, data):
        headers = {"Content-Type" : "application/json"}
        return requests.post(BASEURL + path, headers=headers, data=json.dump(data))

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print('{}: input_info_file'.format(sys.argv[0]))
        sys.exit(1)

    if not os.path.exists('config.json'):
        print('ERROR: cannot load config.json file in current folder')
        sys.exit(1)

    config = json.load(open('config.json'))
    USERS = config['uploader']['USERS']
    BASEURL = config['baseurl']

    uploader = Uploader(config)
    uploader.adminlin()
    for user in USERS.keys():
        print('Adding user: {}'.format(user))
        uploader.adduser(user)
    uploader.adminlout()
