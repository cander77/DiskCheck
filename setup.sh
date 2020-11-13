#!/usr/bin/env bash

#This will be used for all monitoring scripts
if [ -z "$1" ]
    then
    echo ""
    echo "No check interval provided!"
    echo "ex. ./setup.sh [CHECK_INTERVAL]"
    echo ""
    exit
fi

check_interval=$1

#Run updates and install python3
sudo apt-get update
sudo apt-get install python3 -y
sudo apt-get install python-virtualenv -y
sudo apt-get install nullmailer -y

#Modify directories and files if needed
virtualenv -p python3 /home/ubuntu/vault_resource_check
source /home/ubuntu/vault_resource_check/bin/activate
python3 -m pip install requests
mkdir /home/ubuntu/monitoring
mkdir /home/ubuntu/monitoring/vault_resource_check
mv ./disk_check.py /home/ubuntu/monitoring/vault_resource_check/disk_check.py
mv ./run.sh /home/ubuntu/monitoring/vault_resource_check/run.sh

#If cronjob does not exist, create it by the hour
job="sudo bash /home/ubuntu/monitoring/vault_resource_check/run.sh"

if crontab -l | grep "$job"; then
    echo "cronjob exists!"
else
    (crontab -l 2>/dev/null; echo "* $check_interval * * 0-6 sudo bash /home/ubuntu/monitoring/vault_resource_check/run.sh") | crontab -
fi
