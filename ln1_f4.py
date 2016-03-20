# !/usr/bin/python
# coding: utf8

import os
import json
import datetime
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def get_sysresinfo(command):  # функція виконує консольну команду та повертає результат
    command_data = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (command_data, err) = command_data.communicate()
    command_data = command_data.replace(",", ".")  # Заміна ком на крапки для коректного виконання float()
    return command_data.split()


raw = get_sysresinfo("mpstat")  # обробка даних по завантаженості процесора
cpu_user = float(raw[21])
cpu_sys = 0
for x in raw[22:29]:
    cpu_sys += float(x)
cpu_total = cpu_user + cpu_sys
cpu_idle = float(raw[30])
print ("CPU - Total used:%s%%, User:%s%%, System:%s%%, Idle:%s%%" % (cpu_total, cpu_user, cpu_sys, cpu_idle))

raw = get_sysresinfo("free -m")  # обробка даних по завантаженості оперативної памяті
mem_total = int(raw[7])
mem_used = int(raw[8])
mem_free = int(raw[9])
mem_cached = int(raw[12])
print ("MEMORY - Total:%sMb, Used:%sMb, Free:%sMb, Cached:%sMb" % (mem_total, mem_used, mem_free, mem_cached))

raw = get_sysresinfo("df -m --total")  # обробка данних по жорсткому диску
hdd_total = int(raw[50])
hdd_used = int(raw[51])
hdd_free = int(raw[52])
print ("Hard disk drive - Total:%sMb, Used:%sMb, Free:%sMb" % (hdd_total, hdd_used, hdd_free))

systime_customformat = datetime.datetime.now()
systime_customformat = systime_customformat.strftime("%d,%m,%Y,%H,%M,%S")

sysinfo_variables_names = [cpu_total, cpu_user, cpu_sys, cpu_idle, mem_total, mem_used, mem_free,
                           mem_cached, hdd_total, hdd_used, hdd_free]
sysinfo_database_keys = ["cpu_total", "cpu_user", "cpu_sys", "cpu_idle", "mem_total", "mem_used", "mem_free",
                         "mem_cached", "hdd_total", "hdd_used", "hdd_free"]

###############################################################################################################

if os.path.isfile("database2") == False:
    with open("database2", "w") as database_file:
        sysinfo_database = {}
        database_file.write(json.dumps(sysinfo_database))

with open("database2", "r") as database_file:
    data = database_file.read().strip()
sysinfo_database = json.loads(data)
sysdb_totalrecords = len(sysinfo_database) + 1
sysinfo_database[str(sysdb_totalrecords)] = {
    "record_time": systime_customformat,
    "cpu_total": cpu_total,
    "cpu_user": cpu_user,
    "cpu_sys": cpu_sys,
    "cpu_idle": cpu_idle,
    "mem_total": mem_total,
    "mem_used": mem_used,
    "mem_free": mem_free,
    "mem_cached": mem_cached,
    "hdd_total": hdd_total,
    "hdd_used": hdd_used,
    "hdd_free": hdd_free
}
with open("database2", "w") as database_file:
    database_file.write(json.dumps(sysinfo_database))

###############################################################################################################

if sysdb_totalrecords >= 4:  # check if batabase has enough records

    for x in range(0, len(sysinfo_variables_names)):  # cleaning variables before data averaging
        sysinfo_variables_names[x] = 0

    sysdb_recordindex = sysdb_totalrecords
    while sysdb_recordindex > 0:
        for string_index, x in enumerate(sysinfo_database_keys):
            x = sysinfo_database[str(sysdb_recordindex)][x]
            x = float(x)
            sysinfo_variables_names[string_index] += x
        sysdb_recordindex -= 1

    for x in range(0, len(sysinfo_variables_names)):  # averaging data
        sysinfo_variables_names[x] /= sysdb_totalrecords
    print (sysinfo_variables_names)

    with open("database2", "w") as database_file:  # database clean
        sysinfo_database = {}
        database_file.write(json.dumps(sysinfo_database))

    ###############################################################################################################
    mail = MIMEMultipart("alternative")  # forming E-mail
    mail["Subject"] = "Test message"
    mail["From"] = "Python interpreter"
    mail["To"] = "To Lax-T"

    em_html = """
    <html>
        <head></head>
        <body>
            <h1>System hour usage stats</h1>
            <table border = "1">
                <tr>
                    <td>CPU</td>
                </tr>
                <tr>
                    <td>total:{0}</td>
                    <td>user:{1}</td>
                    <td>system:{2}</td>
                    <td>idle:{3}</td>
                </tr>
                <tr>
                    <td>Memory</td>
                </tr>
                <tr>
                    <td>total:{4}</td>
                    <td>used:{5}</td>
                    <td>free:{6}</td>
                    <td>cached:{7}</td>
                </tr>
                <tr>
                    <td>Hard disk drive</td>
                </tr>
                <tr>
                    <td>total:{8}</td>
                    <td>used:{9}</td>
                    <td>free:{10}</td>
                </tr>
            </table>
        </body>
    </html>
    """.format(str(cpu_total), str(cpu_user), str(cpu_sys), str(cpu_idle), str(mem_total), str(mem_used), str(mem_free),
               str(mem_cached), str(hdd_total), str(hdd_used), str(hdd_free))

    em_part2 = MIMEText(em_html, "html")
    mail.attach(em_part2)

    em_client = smtplib.SMTP_SSL("smtp.gmail.com", "465")
    em_client.ehlo()
    em_client.login("irlml4313@gmail.com", "hardpass13101991")  # password deleted
    em_client.sendmail("irlml4313@gmail.com", "laxtec@gmail.com", mail.as_string())  # e-mail deleted
    em_client.close()
