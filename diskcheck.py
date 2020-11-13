import subprocess
import datetime
import socket
import smtplib
import json
import pwd
import grp
import os
from email.mime.text import MIMEText


with open("/var/lib/spadegent/metadata.json") as f:
  env = json.load(f)

partition = "/"
hostname = socket.gethostname()

#found in variables file
threshold = int(os.environ['THRESHOLD'])
mail_port = os.environ['MAIL_PORT']
sender_address = os.environ['SENDER_ADDRESS']
sender_password = os.environ['SENDER_PASSWORD']
email_recipients = os.environ['EMAIL_RECIPIENTS']

#found in metadata.json
datacenter = env["datacenter"]
deploy_env = env["deploy_env"]

#determine smtp server based on environment
if datacenter == "mia":
    smtp_server = os.environ['SMTP_SERVER_CORP']
else:
    smtp_server = os.environ['SMTP_SERVER_SAAS']

#logging
def log_me(log):
    now = datetime.datetime.now()
    now = now.strftime("%m-%d-%Y %H:%M:%S")
    path = "/var/log/"
    file = "vault_resource_status.log"

    f = open(path + file, "a")
    f.write(now + " - " + log + "\n")
    f.close()
    print(now + " - " + log)

#smtp login
def smtp_login():
    server = smtplib.SMTP(smtp_server, mail_port)
    if sender_password != '':
        server.login(sender_address, sender_password)
    return server

#email structure
def compose_notification(message, recipient_address, subject=None):
    if subject == None:
        subject = "ALERT - Hashicorp Vault Notification - " + datacenter + "-" + deploy_env
    else:
        subject = "ALERT - Hashicorp Vault Notification - " + datacenter + "-" + deploy_env

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender_address
    msg['To'] = recipient_address

    return msg.as_string()

#send email
def send_email(message, subject):
    server = smtp_login()
    for recipient_address in recipient_addresses:
        message = compose_notification(message, recipient_address, subject)
        server.sendmail(sender_address, [recipient_address], message)
    server.quit()

def service_action():
    subprocess.check_output(['sudo', 'systemctl', 'restart', 'vault.service'])

def create_audit_file(owner):
    owner = owner
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(owner).gr_gid
    path = "/var/log/"
    file = "vault_audit.log"
    status = "INFO"

    open(path + file, "w+")
    os.chown(path + file, uid, gid)
    log_me("[" + status + "] " + path + file + " created and owner changed to " + owner)

#check disk usage
def disk_check():
    df = subprocess.Popen(["df","-h"], stdout=subprocess.PIPE)
    for line in df.stdout:
        splitline = line.decode().split()
        status = "INFO"
        if splitline[5] == partition:

            #log disk usage periodically for metrics
            log_me("[" + status + "] Disk usage is at " + splitline[4][:-1] + "% and " + splitline[2][:-1] + "G on " + hostname)

            #log disk errors and send email notifications
            if int(splitline[4][:-1]) == 100:
                status = "CRITICAL"
                send_email("Host: " + hostname + "\nStatus: " + status + "\nDetails: Disk percent usage at 100%", status + " - Check disk usage")
                log_me("[" + status + "] Disk percent usage at 100% on " + hostname)
                service_action()
                create_audit_file("vault")
            elif int(splitline[4][:-1]) >= threshold:
                status = "WARNING"
                send_email("Host: " + hostname + "\nStatus: " + status + "\nDetails: Disk percent usage is above " + str(threshold) + "%", status + " - Check disk usage")
                log_me("[" + status + "] Disk percent usage is above " + str(threshold) + "%")
                service_action()
                create_audit_file("vault")
            if int(splitline[3][:-1]) == int(splitline[1][:-1]):
                status = "CRITICAL"
                send_email("Host: " + hostname + "\nStatus: " + status + "\nDetails: Disk is at max usage - " + splitline[1][:-1] + "G/" + splitline[1][:-1] + "G", status + " - Check disk usage")
                log_me("[" + status + "] Disk is at max usage - " + splitline[1][:-1] + "G/" + splitline[1][:-1] + "G")
                service_action()
                create_audit_file("vault")
            elif float(splitline[2][:-1]) >= threshold:
                status = "WARNING"
                send_email("Host: " + hostname + "\nStatus: " + status + "\nDetails: Disk usage is above " + str(threshold) + "G/" + splitline[1][:-1] + "G", status + " - Check disk usage")
                log_me("[" + status + "] Details: Disk usage is above " + str(threshold) + "G/" + splitline[1][:-1] + "G")
                service_action()
                create_audit_file("vault")

def main():
    disk_check()

main()
