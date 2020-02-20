#!/bin/bash

if [ -z $1 ] 
then
	echo "$0 <mysql-root-password>"
else
	sudo docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=$1 --name mysql mysql
fi

