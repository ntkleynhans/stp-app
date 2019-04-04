# DAC Speech Transcription Platform
FROM ubuntu:18.04

MAINTAINER Neil Kleynhans <neil@nktek.co.za>
LABEL Description="Basic STP platform served over HTTP using Apache"

#Install standard tools from Ubuntu repo
#RUN apt-get clean all && apt-get update && apt-get install -y --force-yes software-properties-common
RUN apt-get clean all && apt-get update && apt-get install -y --force-yes apache2 uwsgi uwsgi-plugin-python3 patch python3 python3-bcrypt python3-requests python3-git sox libsox-fmt-all mp3splt pandoc vorbis-tools

#Configure Apache to forward requests (uWSGI)
COPY stp/install/* /etc/apache2/sites-available/
RUN patch /etc/apache2/sites-available/000-default.conf /etc/apache2/sites-available/000-default.conf.patch
RUN a2enmod proxy proxy_http headers

#Setup user and source code for platform
# IF NEEDED: Change FSUID to harmonize with host system user's UID (mounted file system)
ARG UID
ARG GID

RUN groupadd -g $GID dac
RUN useradd -u $UID -g $GID -ms /bin/bash dac
ENV HOME=/home/dac

#Next line should correspond to definitions in `app_server/config/*`
ENV PERSISTENT_FS=/mnt/stp
# Set the following on commandline

WORKDIR $HOME

#Install application server
COPY stp $HOME/source/stp/
RUN chown -R dac:dac source

#Need to set this for GitPython
#See: https://home.regit.org/2014/05/playing-with-python-git/
ENV USERNAME=dac

#Run application server

# You must set following environment variables when running docker
#ENV UID=
#ENV GID=
#ENV SPEECHSERVER=
#ENV APPSERVER=
#ENV SO_SNDTIMEO=

USER root
WORKDIR $HOME/source/stp/app_server
CMD chown -R dac:dac $PERSISTENT_FS && \
    /usr/sbin/apache2ctl start & \
    uwsgi --uid $UID --gid $GID -l 10 -p 5 -z 600 -t 600 --master --enable-threads --protocol=http --plugin /usr/lib/uwsgi/plugins/python3_plugin.so --socket 127.0.0.1:9090 --wsgi-file wsgi.py  --env services_config=config/dispatcher.json
