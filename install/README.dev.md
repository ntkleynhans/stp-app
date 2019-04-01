BUILDING A DEVELOPMENTAL APPLICATION SERVER DOCKER IMAGE
========================================================

This directory contains the files necessary to build a Docker image. To build, place the `Dockerfile.dev` and complete repository in a build location with structure as follows:

```
.
|-- Dockerfile.dev
`-- stp
    |-- app_server
    |   |-- config
    |   |-- service
    |   `-- tools
    `-- install
```

Edit `FSUID` variable found in `Dockerfile.dev`, if needed. This should be the same as your host system UID.
Edit IP addresses found in variables `SPEECHSERVER` and `APPSERVER` - these should be the same as the host system.

To build the docker image run:

```bash
docker build -t stp_base .
```

Testing the built service
-------------------------

Firstly, create a directory on the host filesystem to serve as persistent file storage location (we will use `~/stp` as an example):

```bash
mkdir ~/stp
```

Set up two new authentication databases, for the main (projects, editor) and admin services, in this directory using the `authdb.py` tool (these files should match the setup in `app_server/config/dispatcher.json`:

```bash
python stp/app_server/tools/authdb.py ~/stp/auth.db
python stp/app_server/tools/authdb.py --rootpass <rootpass> ~/stp/admin.db <rootpass>
```

Run the docker image making sure to mount the host directory created above and designate a host port for usage (`9999` in this case):

```bash
docker run --name stp -v ~/stp:/mnt/stp -d -p 9999:80 stp_base:latest
```

Log into the admin service as root:

```bash
curl -i -k -v -H "Content-Type: application/json" -X POST -d '{"username": "root", "password": <rootpass>, "role" : "admin"}' http://127.0.0.1:9999/wsgi/admin/login
```

which should return a token (your token will be different and you must keep track of this token as subsquent requests make use of this token), e.g.:

```json
{"message": "YmVkNWEyNzYtM2IwZS00ZDFmLTg0YjAtYzk0YjU3ZjI2N2I1"}
```

Use this token to add a user to the _projects_ service:

```bash
curl -i -k -v -H "Content-Type: application/json" -X POST -d '{"token": "YmVkNWEyNzYtM2IwZS00ZDFmLTg0YjAtYzk0YjU3ZjI2N2I1", "username": "neil", "password": "neil", "name": "neil", "surname": "kleynhans", "email": "neil@organisation.org", "role" : "project"}' http://127.0.0.1:9999/wsgi/admin/adduser
```

Log into the _projects_ service as the new user:

```bash
curl -i -k -v -H "Content-Type: application/json" -X POST -d '{"username": "neil", "password": "neil", "role" : "project"}' http://127.0.0.1:9999/wsgi/projects/login
```

Use the returned token to access other functions of the _projects_ service.

To stop and remove the docker container run the following:
```bash
docker stop stp
docker rm stp
```
