#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import json
import uuid
import base64
import time
import os
import requests
import threading
import queue
import urllib
import json
import socket

#Hack to get IP:
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#s.connect(("gmail.com",80))
#host_ip = s.getsockname()[0]
#s.close()

host_ip = 'localhost'
HOST_NAME = host_ip # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 9950 # Maybe set this to 9000.

Q = queue.Queue()

# Process speech requests
class dHandle(threading.Thread):

    def __init__(self, q, number):
        threading.Thread.__init__ (self)
        self.q = q
        self.running = True
        self.no = number

    def run(self):
        while self.running:
            if not self.q.empty():
                job = self.q.get()
                print("Thread-{} - Processing job: {}".format(self.no, job))
                job = json.loads(job)

                print('Thread-%s - Fetching: %s -> %s' % (self.no, job["getaudio"], "tmp.tmp.tmp.%s" % self.no))
                urllib.urlretrieve(job["getaudio"], "tmp.tmp.tmp.%s" % self.no)
                print(os.path.getsize("tmp.tmp.tmp.%s" % self.no))
                time.sleep(1)

                print('Thread-%s Uploading result to: %s' % (self.no, job["putresult"]))
                pkg = json.dumps({"CTM" : "0.0\t1.0\tSIL\n1.0\t20.0\tSPK\n"})
                headers = {"Content-Type" : "application/json", "Content-Length" : str(len(pkg))}
                response = requests.put(job["putresult"], headers=headers, data=pkg)
                print(response.status_code, response.text)
                os.remove("tmp.tmp.tmp.%s" % self.no)

                self.q.task_done()
            else:
                time.sleep(0.02)

    def stop(self):
        self.running = False

# Thread the HTTP server
class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

# Handle HTTP requests
class MyHandler(BaseHTTPRequestHandler):
    def do_POST(s):
        """Respond to a GET request."""

        s.send_response(200)
        s.send_header("Content-type", "application/json")
        s.end_headers()

        data = None
        if os.path.basename(s.path) == "login":
            data = {"token" : base64.urlsafe_b64encode(str(uuid.uuid4()).encode()).decode()}
        elif os.path.basename(s.path) == "logout":
            data = {"message" : "User logged out"}
        elif os.path.basename(s.path) == "addjob":
            length = int(s.headers.get('content-length'))
            job = s.rfile.read(length)
            Q.put(job)
            data = {"jobid" : "123"}
        elif os.path.basename(s.path) == "deletejob":
            data = {"message" : "Job deleted"}
        else:
            data = {"message" : "Unknown request"}
            length = int(s.headers.get('content-length'))
            f = open('tmp.dat', 'wb')
            f.write(s.rfile.read(length))
            f.close()
        s.wfile.write(bytes(json.dumps(data), 'utf-8'))


if __name__ == '__main__':
    #server_class = BaseHTTPServer.HTTPServer
    server_class = ThreadedHTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)

    # Create workers
    dH = []
    for n in range(10):
        dH.append(dHandle(Q, n))
        dH[n].start()

    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    # Teardown
    for n in range(10):
        dH[n].stop()
        dH[n].join()

    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))

