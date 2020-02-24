# [HOMS Dockerfile]
FROM ubuntu:16.04
MAINTAINER [ETRI] WOOK HYUN <whyun@etri.re.kr>

# default setting
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y --no-install-recommends apt-utils

# install KR language-pack
RUN apt-get install -y language-pack-ko

# set locale KR
RUN locale-gen ko_KR.UTF-8
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8

# install python3.7 && pip3.7
RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y python3.7
RUN apt-get install -y python3-pip
RUN python3.7 -m pip install --upgrade pip
# RUN alias python=python3.7
# RUN alias pip=pip3

# install mariadb-server
# RUN echo "mysql-server mysql-server/root_password password root" | debconf-set-selections
# RUN echo "mysql-server mysql-server/root_password_again password root" | debconf-set-selections
# RUN echo "mariadb-server mariadb-server/root_password password root" | debconf-set-selections
# RUN echo "mariadb-server mariadb-server/root_password_again password root" | debconf-set-selections
RUN apt-get update
RUN apt-get install -y mariadb-server

# set mariadb character-set utf8 
RUN echo "\n\
collation-server = utf8_unicode_ci\n\
init-connect='SET NAMES utf8'\n\
character-set-server = utf8\n\
\n\
[mysql]\n\
default-character-set=utf8\n\
\n\
[client]\n\
default-character-set=utf8\n\
" >> /etc/mysql/mariadb.conf.d/50-server.cnf

# Add Files
RUN mkdir /data_collector
ADD src/. /data_collector/.

# install packages
RUN pip3.7 install requests
RUN pip3.7 install schedule
RUN pip3.7 install pymysql

# set MariaDB User
RUN service mysql start && mysql -uroot mysql -e "flush privileges;UPDATE user SET plugin='' where user='root';UPDATE user SET password=PASSWORD('root') WHERE user='root';flush privileges;"

# set entrypoint
# ENTRYPOINT service mysql restart
