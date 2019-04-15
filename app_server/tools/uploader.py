#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function

import requests
import sys
import json
import os
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
LOGNAME = "UPLOADER"
LOGFNAME = "uploader.log"
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
ULIZA = None

class Uploader:

    def __init__(self, config):
        self.admin_password = config['admin_password']
        self.user_password = config['user_password']
        self.admin_token = None
        self.user_token = None
        self.project_user = config['project_user']
        self.project_id = None

    def adminlin(self):
        """
            Login as admin
            Place admin 'token' in self.admin_token
        """
        if self.admin_token is None:
            LOG.info("Admin logging in")
            headers = {"Content-Type" : "application/json"}
            data = {"username": "root", "password": self.admin_password, "role" : "admin"}
            res = requests.post(BASEURL + "admin/login", headers=headers, data=json.dumps(data))
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
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token}
            res = requests.post(BASEURL + "admin/logout", headers=headers, data=json.dumps(data))
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
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.admin_token, "username": USERS[user]["username"], "password": USERS[user]["password"],
             "name": USERS[user]["name"], "surname": USERS[user]["surname"], "email": USERS[user]["email"],
             "role": USERS[user]["role"]}
            res = requests.post(BASEURL + "admin/adduser", headers=headers, data=json.dumps(data))
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
            headers = {"Content-Type" : "application/json"}
            data = {"username": self.project_user, "password": self.user_password, "role" : 'project'}
            res = requests.post(BASEURL + "projects/login", headers=headers, data=json.dumps(data))
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
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token}
            res = requests.post(BASEURL + "projects/logout", headers=headers, data=json.dumps(data))
            LOG.info('logout(): SERVER SAYS:{}'.format(res.text))
            self.user_token = None
        else:
            LOG.info("User not logged in!")

    def createproject(self, name):
        """
            Create a new project
            Save returned projectid in self.projectid
        """
        if self.user_token is not None:
            LOG.info("Creating project")
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "projectname" : name, "category" : "General", "projectmanager" : 'cvheerden' }
            res = requests.post(BASEURL + "projects/createproject", headers=headers, data=json.dumps(data))
            LOG.info('createproject(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            pkg = res.json()
            self.projectid = pkg['projectid']
        else:
            LOG.info("User not logged in!")

    def uploadaudio(self, oggfile):
        """
            Upload audio to project
            Requires tallship.ogg to be located in current location
        """
        if not os.path.exists(oggfile):
            LOG.error('Cannot run UPLOADAUDIO as {} does not exist in current path'.format(oggfile))
            return

        if self.user_token is not None and self.projectid is not None:
            files = {'file' : open(oggfile, 'rb'), 'filename' : os.path.basename(oggfile), 'token' : self.user_token, 'projectid' : self.projectid}
            res = requests.post(BASEURL + "projects/uploadaudio", files=files)
            LOG.info('uploadaudio(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            if res.status_code != 200:
                print('Uploadaudio Failed -- deleting project')
                self.deleteproject()
        else:
            LOG.info("User not logged in!")

    def saveproject(self, projectname, duration, editor):
        """
            Save tasks for a specific project
            tasks should be a list of dicts with these elements:
            tasks = [(editor<string:20>, start<float>, end<float>), (), ...]
        """
        if self.user_token is not None and self.projectid is not None:
            LOG.info("Saving project")
            headers = {"Content-Type" : "application/json"}
            tasks = [{"editor" : editor, "start" : 0.0, "end" : float(duration), "language" : 'English', "speaker" : 'Speaker'}]
            project = {"projectname": projectname}
            data = {"token": self.user_token, "projectid" : self.projectid, "tasks": tasks, "project": project}
            res = requests.post(BASEURL + "projects/saveproject", headers=headers, data=json.dumps(data))
            LOG.info('saveproject(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            if res.status_code != 200:
                print('Saveproject Failed -- deleting project')
                self.deleteproject()
        else:
            LOG.info("User not logged in!")

    def assigntasks(self):
        """
            Assign tasks to editors
        """
        if self.user_token is not None and self.projectid is not None:
            LOG.info("Assigning tasks")
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "projectid" : self.projectid, "collator" : 'cvheerden'}
            res = requests.post(BASEURL + "projects/assigntasks", headers=headers, data=json.dumps(data))
            LOG.info('assigntasks(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            if res.status_code != 200:
                print('Assigntasks Failed -- deleting project')
                self.deleteproject()
        else:
            LOG.info("User not logged in!")

    def deleteproject(self):
        """
            Delete Project
        """
        if self.user_token is not None and self.projectid is not None:
            LOG.info("Deleting Project")
            headers = {"Content-Type" : "application/json"}
            data = {"token": self.user_token, "projectid" : self.projectid}
            res = requests.post(BASEURL + "projects/deleteproject", headers=headers, data=json.dumps(data))
            LOG.info('deletepoject(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            self.projectid = None
        else:
            LOG.info("User not logged in!")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print('{}: input_info_file'.format(sys.argv[0]))
        sys.exit(1)

    if not os.path.exists('config.json'):
        print('ERROR: cannot load config.json file in current folder')
        sys.exit(1)

    config = json.load(open('config.json'))
    USERS = config['uploader']['USERS']
    ULIZA = config['uploader']['ULIZA']

    uploader = Uploader(config)

    """
    uploader.adminlin()
    for user in USERS.keys():
        print('Adding user: {}'.format(user))
        uploader.adduser(user)
    uploader.adminlout()
    for user in ULIZA.keys():
        print('Adding user: {}'.format(user))
        uploader.adduser(user)
    uploader.adminlout()
    exit() 
    """

    uploader.login()
    for line in open(sys.argv[1], "r"):
        print("Processing: {}".format(line.rstrip()))
        ogg_file, duration, project_name, editor_username = line.rstrip().split(";")
        uploader.createproject(project_name)
        if uploader.projectid is not None:
            uploader.uploadaudio(ogg_file)
        if uploader.projectid is not None:       
            uploader.saveproject(project_name, duration, editor_username)
        if uploader.projectid is not None:
            uploader.assigntasks()

    uploader.logout()

