#!/usr/bin/env bash

#Launch disk_check.py
source /home/ubuntu/vault_resource_check/bin/activate
python3 /home/ubuntu/monitoring/vault_resource_check/disk_check.py >> /var/log/vault_resource_status.log
