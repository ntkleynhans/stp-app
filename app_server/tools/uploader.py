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

class Uploader:

    def __init__(self, config):
        self.user_password = config['user_password']
        self.user_token = None
        self.editor_user_token = None
        self.project_user = config['project_user']
        self.projectmanager = config['projectmanager']
        self.collator = config['collator']
        self.project_id = None

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

    def createproject(self, name):
        """
            Create a new project
            Save returned projectid in self.projectid
        """
        if self.user_token is not None:
            LOG.info("Creating project")
            res = self._requests("projects/createproject", {"token": self.user_token, "projectname" : name, "category" : "General", "projectmanager" : self.projectmanager })
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

    def saveproject(self, projectname, tasks):
        """
            Save tasks for a specific project
            tasks should be a list of dicts with these elements:
            tasks = [(editor<string:20>, start<float>, end<float>), (), ...]
        """
        if self.user_token is not None and self.projectid is not None:
            LOG.info("Saving project")
            data = {"token": self.user_token, "projectid" : self.projectid, "tasks": tasks, "project": {"projectname": projectname}}
            res = self._requests("projects/saveproject", data)
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
            res = self._requests("projects/assigntasks", {"token": self.user_token, "projectid" : self.projectid, "collator" : self.collator})
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
            res = self._requests("projects/deleteproject", {"token": self.user_token, "projectid" : self.projectid})
            LOG.info('deletepoject(): SERVER SAYS:{}'.format(res.text))
            LOG.info(res.status_code)
            self.projectid = None
        else:
            LOG.info("User not logged in!")

    def editor_login(self, user, password):
        """
            Login as user
            Place user 'token' in self.user_token
        """
        if self.editor_user_token is None:
            LOG.info("{} logging in".format(user))
            res = self._requests("editor/login", {"username": user, "password": password, "role" : 'editor'})
            LOG.info('login(): SERVER SAYS:{}'.format(res.text))
            if res.status_code != 200:
                print('Assigntasks Failed -- deleting project')
                self.deleteproject()
            else:
                pkg = res.json()
                self.editor_user_token = pkg['token']
        else:
            LOG.info("User logged in already!")

    def editor_logout(self):
        """
            Logout as user
        """
        if self.editor_user_token is not None:
            res = self._requests("editor/logout", {"token": self.editor_user_token})
            LOG.info('logout(): SERVER SAYS:{}'.format(res.text))
            self.editor_user_token = None
        else:
            LOG.info("User not logged in!")

    def savetext(self, taskid, text):
        """
            Save text to task text file
        """
        LOG.info("Saving task text")
        if self.editor_user_token is not None and self.projectid is not None:
            #TASKID hard coded as we are creating single tasks per file
            res = self._requests("editor/savetext", {'token' : self.editor_user_token, 'projectid' : self.projectid, 'taskid' : taskid, "text" : text})
            print('SERVER SAYS:', res.text)
            LOG.info("savetext() done")
            LOG.info(res.status_code)
            if res.status_code != 200:
                print('Savetext Failed -- deleting project')
                self.deleteproject()
        else:
            print("User not logged in!")
            LOG.error("savetext(): User not logged in!")
        print('')

    def _requests(self, path, data):
        headers = {"Content-Type" : "application/json"}
        return requests.post(BASEURL + path, headers=headers, data=json.dumps(data))

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print('{}: config_file input_info_file'.format(sys.argv[0]))
        sys.exit(1)

    config = json.load(open(sys.argv[1]))
    data = json.load(open(sys.argv[2]))
  
    BASEURL = config['baseurl']
    USERS = config['uploader']['USERS']
    uploader = Uploader(config)
    uploader.login()

    uploader.createproject(data['project_name'])
    if uploader.projectid is not None:
        uploader.uploadaudio(data['ogg_file'])
    if uploader.projectid is not None:       
        uploader.saveproject(data['project_name'], data['tasks'])
    if uploader.projectid is not None:
        uploader.assigntasks()
    if uploader.projectid is not None:
        try:
            for ndx, text in enumerate(data['text']):
                task = data['tasks'][ndx]
                uploader.editor_login(USERS[task['editor']]['username'],
                    USERS[task['editor']]['password'])
                uploader.savetext(ndx, text)
                uploader.editor_logout()
        except Exception as e:
            print('Error', str(e))
            uploader.deleteproject()

    uploader.logout()
