#!/bin/sh
echo 'Updating apt'
apt-get update
echo 'Removing existing docker'
apt-get remove docker docker-engine docker.io
echo 'Installing required dependencies for apt https transport'
apt-get install --assume-yes \
	    apt-transport-https \
	        ca-certificates \
		    curl \
		        software-properties-common
echo 'Downloading docker gpg key'
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
echo 'Adding docker repo'
add-apt-repository \
	   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
	      $(lsb_release -cs) \
	         stable"
echo 'Updating apt again with docker repo'
apt-get update
echo 'Installing docker'
apt-get install --assume-yes docker-ce
