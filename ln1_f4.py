#!/usr/bin/python
# coding: utf8

import os
import json
import datetime
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import Encoders
from email.mime.application import MIMEApplication
from openpyxl import Workbook
from openpyxl.styles import colors, Font, Border, Side

database_file_name = "/home/lax/PycharmProjects/learn1/database3"
xcel_table_name = "/home/lax/PycharmProjects/learn1/12 hour sys stats.xlsx"


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

if os.path.isfile(database_file_name) == False:  # Adding new record into database
    with open(database_file_name, "w") as database_file:
        sysinfo_database = {"0": {
            "email_send_hour": 24,
            "emails_sent": 0
        }}
        database_file.write(json.dumps(sysinfo_database))

with open(database_file_name, "r") as database_file:
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
with open(database_file_name, "w") as database_file:
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


class ExcelTable(object):
    def __init__(self):
        self.new_workbook = Workbook()
        self.new_worksheet = self.new_workbook.active
        self.black_font = Font(color=colors.BLACK)
        self.blue_font = Font(color=colors.BLUE)
        self.red_font = Font(color=colors.RED)
        self.border_allthin = Border(left=Side(border_style="thin", color=colors.BLACK),
                                     right=Side(border_style="thin", color=colors.BLACK),
                                     bottom=Side(border_style="thin", color=colors.BLACK),
                                     top=Side(border_style="thin", color=colors.BLACK))
        self.border_LTthik = Border(left=Side(border_style="thick", color=colors.BLACK),
                                    bottom=Side(border_style="thin", color=colors.BLACK),
                                    top=Side(border_style="thick", color=colors.BLACK))
        self.border_Tthik = Border(bottom=Side(border_style="thin", color=colors.BLACK),
                                   top=Side(border_style="thick", color=colors.BLACK))
        self.border_TRthik = Border(right=Side(border_style="thick", color=colors.BLACK),
                                    bottom=Side(border_style="thin", color=colors.BLACK),
                                    top=Side(border_style="thick", color=colors.BLACK))
        self.border_Lthik = Border(left=Side(border_style="thick", color=colors.BLACK),
                                   right=Side(border_style="thin", color=colors.BLACK),
                                   bottom=Side(border_style="thin", color=colors.BLACK),
                                   top=Side(border_style="thin", color=colors.BLACK))
        self.border_Rthik = Border(left=Side(border_style="thin", color=colors.BLACK),
                                   right=Side(border_style="thick", color=colors.BLACK),
                                   bottom=Side(border_style="thin", color=colors.BLACK),
                                   top=Side(border_style="thin", color=colors.BLACK))
        self.border_LBthik = Border(left=Side(border_style="thick", color=colors.BLACK),
                                    right=Side(border_style="thin", color=colors.BLACK),
                                    bottom=Side(border_style="thick", color=colors.BLACK),
                                    top=Side(border_style="thin", color=colors.BLACK))
        self.border_Bthik = Border(left=Side(border_style="thin", color=colors.BLACK),
                                   right=Side(border_style="thin", color=colors.BLACK),
                                   bottom=Side(border_style="thick", color=colors.BLACK),
                                   top=Side(border_style="thin", color=colors.BLACK))
        self.border_BRthik = Border(left=Side(border_style="thin", color=colors.BLACK),
                                    right=Side(border_style="thick", color=colors.BLACK),
                                    bottom=Side(border_style="thick", color=colors.BLACK),
                                    top=Side(border_style="thin", color=colors.BLACK))

        self.active_cell = self.new_worksheet.cell(row=2, column=2)
        self.active_cell.value = "System 12 hour usage stats"
        self.active_cell.font = Font(color=colors.GREEN, italic=True, size=16)
        self.table_row_index = 2

        self.toprow_border_style = [self.border_LTthik, self.border_Tthik, self.border_Tthik,
                                    self.border_Tthik, self.border_TRthik]
        self.middlerow_border_style = [self.border_Lthik, self.border_allthin, self.border_allthin,
                                       self.border_allthin, self.border_Rthik]
        self.botmrow_border_style = [self.border_LBthik, self.border_Bthik, self.border_Bthik,
                                     self.border_Bthik, self.border_BRthik]
        self.row1_data = []
        self.row2_data = []
        self.row3_data = []
        self.row4_data = []

    def table_data_update(self):
        self.row1_data = ["Averaging period " + str(averaging_period_date) + " " + str(averaging_period_time) +
                          ":00 - " + str(averaging_period_time) + ":59", "", "", "", ""]
        self.row2_data = ["CPU", "total: %.2f" % (sysinfo_variables_names[0]), "user: %.2f" %
                          (sysinfo_variables_names[1]), "system: %.2f" % (sysinfo_variables_names[2]),
                          "idle: %.2f" % (sysinfo_variables_names[3])]
        self.row3_data = ["Memory", "total: %.2f" % (sysinfo_variables_names[4]), "used: %.2f" %
                          (sysinfo_variables_names[5]), "free: %.2f" % (sysinfo_variables_names[6]),
                          "cached: %.2f" % (sysinfo_variables_names[7])]
        self.row4_data = ["Hard disk drive", "total: %d" % (sysinfo_variables_names[8]),
                          "used: %d" % (sysinfo_variables_names[9]), "free: %d" % (sysinfo_variables_names[10]), ""]

    def extend_helper(self, exthe_row_data, exthe_border_style, exthe_first_col_font):
        self.table_row_index += 1
        for x in range(0, 5):
            self.active_cell = self.new_worksheet.cell(row=self.table_row_index, column=x+2)
            self.active_cell.value = exthe_row_data[x]
            self.active_cell.border = exthe_border_style[x]
            if x == 0:
                self.active_cell.font = exthe_first_col_font
            else:
                self.active_cell.font = self.black_font

    def extend(self):
        self.table_data_update()  # Update table variables
        self.extend_helper(self.row1_data, self.toprow_border_style, self.blue_font)
        self.extend_helper(self.row2_data, self.middlerow_border_style, self.red_font)
        self.extend_helper(self.row3_data, self.middlerow_border_style, self.red_font)
        self.extend_helper(self.row4_data, self.botmrow_border_style, self.red_font)

    def save(self, filename):
        self.new_worksheet.row_dimensions[2].height = 20
        self.new_worksheet.column_dimensions["A"].width = 5
        self.new_worksheet.column_dimensions["B"].width = 18
        self.new_worksheet.column_dimensions["C"].width = 15
        self.new_worksheet.column_dimensions["D"].width = 15
        self.new_worksheet.column_dimensions["E"].width = 15
        self.new_worksheet.column_dimensions["F"].width = 15
        self.new_workbook.save(filename)


def get_db_record_datetime(index):
    datetime_combine = sysinfo_database[str(index)]["record_time"].split(",")
    date_astext = "%s:%s:%s" % (str(datetime_combine[0]), str(datetime_combine[1]), str(datetime_combine[2]))
    time = datetime_combine[3]
    return date_astext, time


def get_db_record_time(index):
    datetime_combine = sysinfo_database[str(index)]["record_time"].split(",")
    return datetime_combine[3]

email_send_hour = sysinfo_database["0"]["email_send_hour"]
emails_sent_counter = sysinfo_database["0"]["emails_sent"]
system_time_hour = systime_customformat.split(",")[3]
new_Excel_Table = ExcelTable()

if sysdb_totalrecords >= 4 and email_send_hour != system_time_hour:  # check if batabase has enough records
    sysdb_recordindex = sysdb_totalrecords - 1  # setting up record index for database addressing
    htmltable_lenght_counter = 0
    exceltable_lenght_counter = 0
    next_record_time = get_db_record_time(sysdb_recordindex)

    while sysdb_recordindex > 0 and (htmltable_lenght_counter < 5 or
                                         (exceltable_lenght_counter < 12 and emails_sent_counter >= 11)):
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

        if htmltable_lenght_counter < 5:
            dynamic_html_table = extend_dynamic_table(dynamic_html_table)
            htmltable_lenght_counter += 1

        if emails_sent_counter >= 11:
            new_Excel_Table.extend()
            exceltable_lenght_counter += 1

    dynamic_html_table += """
                </tr>
            </table>
        </body>
    </html>
    """  # end (close) table

    mail = MIMEMultipart()  # forming E-mail
    mail["Subject"] = "Test message"
    mail["From"] = "Python interpreter"
    mail["To"] = "To Lax-T"

    if emails_sent_counter >= 11:  # check if attachment and counter reset is needed
        emails_sent_counter = 0
        new_Excel_Table.save(xcel_table_name)
        em_file1 = MIMEBase("application", "octet-stream")
        with open(xcel_table_name, "rb") as fp:
            em_file1.set_payload(fp.read())
            Encoders.encode_base64(em_file1)

        em_file1.add_header('Content-Disposition', 'attachment', filename="stats.xlsx")
        mail.attach(em_file1)
    else:
        emails_sent_counter += 1

    sysinfo_database["0"] = {
        "email_send_hour": system_time_hour,
        "emails_sent": emails_sent_counter
    }
    with open(database_file_name, "w") as database_file:
        database_file.write(json.dumps(sysinfo_database))

    em_part2 = MIMEText(dynamic_html_table, "html")
    mail.attach(em_part2)
    em_client = smtplib.SMTP_SSL("smtp.gmail.com", "465")
    em_client.ehlo()
    em_client.login("irlml4313@gmail.com", "*******")  # password deleted
    em_client.sendmail("irlml4313@gmail.com", "*******@gmail.com", mail.as_string())  # e-mail deleted
    em_client.close()
