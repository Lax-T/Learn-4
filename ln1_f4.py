#!/usr/bin/python
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

raw = get_sysresinfo("free -m")  # обробка даних по завантаженості оперативної памяті
mem_total = int(raw[7])
mem_used = int(raw[8])
mem_free = int(raw[9])
mem_cached = int(raw[12])

raw = get_sysresinfo("df -m --total")  # обробка данних по жорсткому диску
hdd_total = int(raw[50])
hdd_used = int(raw[51])
hdd_free = int(raw[52])

systime_customformat = datetime.datetime.now()
systime_customformat = systime_customformat.strftime("%d,%m,%Y,%H,%M,%S")

sysinfo_variables_names = [cpu_total, cpu_user, cpu_sys, cpu_idle, mem_total, mem_used, mem_free,
                           mem_cached, hdd_total, hdd_used, hdd_free]
sysinfo_database_keys = ["cpu_total", "cpu_user", "cpu_sys", "cpu_idle", "mem_total", "mem_used", "mem_free",
                         "mem_cached", "hdd_total", "hdd_used", "hdd_free"]

###############################################################################################################

if os.path.isfile("/home/lax/PycharmProjects/learn1/database_cron") == False:  # Adding new record into database
    with open("/home/lax/PycharmProjects/learn1/database_cron", "w") as database_file:
        sysinfo_database = {"0": {
            "email_send_hour": 24
        }}
        database_file.write(json.dumps(sysinfo_database))

with open("/home/lax/PycharmProjects/learn1/database_cron", "r") as database_file:
    data = database_file.read().strip()
sysinfo_database = json.loads(data)
sysdb_totalrecords = len(sysinfo_database)
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
with open("/home/lax/PycharmProjects/learn1/database_cron", "w") as database_file:
    database_file.write(json.dumps(sysinfo_database))

###############################################################################################################
dynamic_html_table = """
    <html>
        <head></head>
        <body>
            <h1>System hour usage stats</h1>
            <table border = "1">
            """  # table start


def extend_dynamic_table(edh_table):
    edh_table += """
                <tr>
                    <td>Averaging period {11} {12}:00 - {12}:59</td>
                </tr>
                <tr>
                    <td>CPU</td>
                    <td>total:{0:.2f}</td>
                    <td>user:{1:.2f}</td>
                    <td>system:{2:.2f}</td>
                    <td>idle:{3:.2f}</td>
                </tr>
                <tr>
                    <td>Memory</td>
                    <td>total:{4:.2f}</td>
                    <td>used:{5:.2f}</td>
                    <td>free:{6:.2f}</td>
                    <td>cached:{7:.2f}</td>
                </tr>
                <tr>
                    <td>Hard disk drive</td>
                    <td>total:{8:.2f}</td>
                    <td>used:{9:.2f}</td>
                    <td>free:{10:.2f}</td>
                </tr>
    """.format(sysinfo_variables_names[0], sysinfo_variables_names[1], sysinfo_variables_names[2],
               sysinfo_variables_names[3], sysinfo_variables_names[4], sysinfo_variables_names[5],
               sysinfo_variables_names[6], sysinfo_variables_names[7], sysinfo_variables_names[8],
               sysinfo_variables_names[9], sysinfo_variables_names[10], str(averaging_period_date),
               str(averaging_period_time))

    return edh_table


def get_db_record_datetime(index):
    datetime_combine = sysinfo_database[str(index)]["record_time"].split(",")
    date_astext = "%s:%s:%s" % (str(datetime_combine[0]), str(datetime_combine[1]), str(datetime_combine[2]))
    time = datetime_combine[3]
    return date_astext, time


def get_db_record_time(index):
    datetime_combine = sysinfo_database[str(index)]["record_time"].split(",")
    return datetime_combine[3]

email_send_hour = sysinfo_database["0"]["email_send_hour"]
system_time_hour = systime_customformat.split(",")[3]

if sysdb_totalrecords >= 4 and email_send_hour != system_time_hour:  # check if DB has enough records and hour changed
    sysdb_recordindex = sysdb_totalrecords-1  # setting up record index for DB addressing (skipping last record)
    table_lenght_counter = 0
    next_record_time = get_db_record_time(sysdb_recordindex)

    while sysdb_recordindex > 0 and table_lenght_counter < 5:  # by "5" limiting max table size
        averaging_period_date, averaging_period_time = get_db_record_datetime(sysdb_recordindex)
        for x in range(0, len(sysinfo_variables_names)):  # cleaning variables before data averaging
            sysinfo_variables_names[x] = 0
        records_averaged = 0

        while averaging_period_time == next_record_time:
            for string_index, x in enumerate(sysinfo_database_keys):
                x = sysinfo_database[str(sysdb_recordindex)][x]
                x = float(x)
                sysinfo_variables_names[string_index] += x
            records_averaged += 1
            sysdb_recordindex -= 1
            if sysdb_recordindex < 1:
                break
            next_record_time = get_db_record_time(sysdb_recordindex)

        for x in range(0, len(sysinfo_variables_names)):  # averaging data
            sysinfo_variables_names[x] /= records_averaged
        dynamic_html_table = extend_dynamic_table(dynamic_html_table)
        table_lenght_counter += 1

    dynamic_html_table += """
                </tr>
            </table>
        </body>
    </html>
    """  # end (close) table

    sysinfo_database["0"] = {  # Updating last email send hour
            "email_send_hour": system_time_hour
        }
    with open("/home/lax/PycharmProjects/learn1/database_cron", "w") as database_file:
        database_file.write(json.dumps(sysinfo_database))

    ###############################################################################################################
    mail = MIMEMultipart("alternative")  # forming E-mail
    mail["Subject"] = "Test message"
    mail["From"] = "Python interpreter"
    mail["To"] = "To Lax-T"

    em_part2 = MIMEText(dynamic_html_table, "html")
    mail.attach(em_part2)

    em_client = smtplib.SMTP_SSL("smtp.gmail.com", "465")
    em_client.ehlo()
    em_client.login("irlml4313@gmail.com", "**********")  # password deleted
    em_client.sendmail("irlml4313@gmail.com", "******@gmail.com", mail.as_string())  # e-mail deleted
    em_client.close()
