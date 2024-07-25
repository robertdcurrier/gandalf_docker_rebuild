# GCOOS DMAC GANDALF_V2 Docker File
FROM robertdcurrier/gandalf
MAINTAINER Bob Currier <robertdcurrier@gmail.com>
ENV REFRESHED_AT 2023-09-08

WORKDIR /var/www/wsgi/gandalf/app
# We need the Dinkum tools
COPY dinkum /opt/dinkum
#ADD letsencrypt /etc/letsencrypt
RUN a2enmod ssl
RUN a2enmod rewrite
ADD apache2.conf /etc/apache2/sites-available/000-default.conf
ADD .vimrc /root/.vimrc
COPY requirements.txt /var/www/wsgi/gandalf/app
RUN pip3 install -r requirements.txt


