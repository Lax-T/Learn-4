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
from openpyxl import Workbook
from openpyxl.styles import colors, Font, Border, Side

database_file_name = "/home/lax/PycharmProjects/learn1/database4"
add_database_file_name = "/home/lax/PycharmProjects/learn1/add_database4"
excel_table_name = "/home/lax/PycharmProjects/learn1/new method test.xlsx"


def get_sysresinfo(command):  # Executes console command and returns data as list
    command_data = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (command_data, err) = command_data.communicate()
    return command_data.replace(",", ".").split()


def get_cpu_info():  # return list format - cpu_user, cpu_sys, cpu_total, cpu_idle
    cpu_usage_info = []
    cpu_console_data = get_sysresinfo("mpstat")
    cpu_usage_info.append(float(cpu_console_data[21]))
    cpu_sys = 0
    for x in cpu_console_data[22:29]:
        cpu_sys += float(x)
    cpu_usage_info.append(cpu_sys)
    cpu_usage_info.append(cpu_usage_info[0] + cpu_usage_info[1])
    cpu_usage_info.append(float(cpu_console_data[30]))
    return cpu_usage_info


def get_mem_info():  # return list format - mem_total, mem_used, mem_free, mem_cached
    mem_usage_info = []
    mem_console_data = get_sysresinfo("free -m")
    mem_usage_info.append(int(mem_console_data[7]))
    mem_usage_info.append(int(mem_console_data[8]))
    mem_usage_info.append(int(mem_console_data[9]))
    mem_usage_info.append(int(mem_console_data[12]))
    return mem_usage_info


def get_hdd_info():  # return list format - hdd_total, hdd_used, hdd_free
    hdd_usage_info = []
    hdd_console_data = get_sysresinfo("df -m --total")
    hdd_usage_info.append(int(hdd_console_data[50]))
    hdd_usage_info.append(int(hdd_console_data[51]))
    hdd_usage_info.append(int(hdd_console_data[52]))
    return hdd_usage_info

system_usage_info = get_cpu_info() + get_mem_info() + get_hdd_info()
print system_usage_info
systime_customformat = datetime.datetime.now()
systime_customformat = systime_customformat.strftime("%Y,%m,%d,%H,%M,%S")

###############################################################################################################


class SysinfoDatabase(object):
    def __init__(self, db_file_name):
        self.db_file_name = db_file_name
        if not os.path.isfile(self.db_file_name):
            self.sysinfo_database = {}
            with open(self.db_file_name, "w") as self.database_file:
                self.database_file.write(json.dumps(self.sysinfo_database))
            self.db_is_empty = True

        else:
            self.db_is_empty = False

        with open(self.db_file_name, "r") as self.database_file:
            self.sysinfo_database = self.database_file.read().strip()
            self.sysinfo_database = json.loads(self.sysinfo_database)

        self.database_keywords = self.sysinfo_database.keys()
        self.database_keywords.sort(reverse=True)

        self.lastrh = None  # Variable definitions
        self.periods_averaged = None
        self.select_result = None
        self.averaging_period_result = None
        self.records_in_period = None
        self.single_record_data = None
        self.averaged_in_period = 0
        self.current_period_timestamp = None
        self.temp = None
        self.database_size = 0

    def lastrecordhour(self):  # Returns hour of last record in database
        self.lastrh = self.database_keywords[0]
        return int(self.lastrh.split(",")[3])

    def select(self, start=None, end=None, limit=12, groupbyhour=True):  # Select and average data from database
        self.periods_averaged = 0
        self.select_result = []
        if self.db_is_empty:
            return self.select_result, self.periods_averaged
        if start is None:
            start = self.database_keywords[0]
        if end is None:
            end = self.database_keywords[len(self.database_keywords)-1]

        self.averaging_period_result = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.current_period_timestamp = None
        self.averaged_in_period = 0
        self.single_record_data = None

        for current_key in self.database_keywords:
            if start >= current_key >= end:
                if self.current_period_timestamp is None:  # Setting up first avg period
                    self.current_period_timestamp = current_key[0:13]

                if groupbyhour:
                    if self.current_period_timestamp != current_key[0:13]:
                        for index in range(0, len(self.averaging_period_result)):  # Avg and Add data to sel. result
                            self.averaging_period_result[index] /= self.averaged_in_period
                        self.averaging_period_result += self.current_period_timestamp.split(",")
                        self.select_result.append(self.averaging_period_result)
                        self.periods_averaged += 1
                        self.averaging_period_result = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                        self.averaged_in_period = 0
                        if self.periods_averaged >= limit:
                            break
                        self.current_period_timestamp = current_key[0:13]

                self.single_record_data = self.sysinfo_database[current_key]  # Summing average
                for index, value in enumerate(self.single_record_data):
                    self.averaging_period_result[index] += value
                self.averaged_in_period += 1
            else:
                if current_key < end:
                    break
        if self.averaged_in_period != 0:
            for index in range(0, len(self.averaging_period_result)):  # Avg and Add data to sel. result
                self.averaging_period_result[index] /= self.averaged_in_period
            self.averaging_period_result += self.current_period_timestamp.split(",")
            self.select_result.append(self.averaging_period_result)
            self.periods_averaged += 1
        return self.select_result, self.periods_averaged

    def new_record(self, timestamp, data):  # Adding new record into database
        self.sysinfo_database[timestamp] = data
        with open(self.db_file_name, "w") as self.database_file:
            self.database_file.write(json.dumps(self.sysinfo_database))
        self.database_keywords = self.sysinfo_database.keys()
        self.database_keywords.sort(reverse=True)

    def erase(self):  # Database full erase
        self.sysinfo_database = {}
        self.db_is_empty = True
        with open(self.db_file_name, "w") as self.database_file:
            self.database_file.write(json.dumps(self.sysinfo_database))

    def clean(self, size_limit=500):  # Cleans database from old records (default is 500 record limit)
        self.database_size = len(self.database_keywords)
        while self.database_size > size_limit:
            del self.sysinfo_database[self.database_keywords[self.database_size - 1]]
            self.database_size -= 1
        with open(self.db_file_name, "w") as self.database_file:
            self.database_file.write(json.dumps(self.sysinfo_database))
        self.database_keywords = self.sysinfo_database.keys()
        self.database_keywords.sort(reverse=True)

systeminfo_database = SysinfoDatabase(database_file_name)

###################################################################################################################

html_table = """
    <html>
        <head></head>
        <body>
            <h1>System hour usage stats</h1>
            <table border = "1">
            """  # table start


def extend_html_table(e_html_table, table_data):
    e_html_table += """
                <tr>
                    <td>Averaging period {13}.{12}.{11} {14}:00 - {14}:59</td>
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
                    <td>total:{4:d}</td>
                    <td>used:{5:d}</td>
                    <td>free:{6:d}</td>
                    <td>cached:{7:d}</td>
                </tr>
                <tr>
                    <td>Hard disk drive</td>
                    <td>total:{8:d}</td>
                    <td>used:{9:d}</td>
                    <td>free:{10:d}</td>
                </tr>
    """.format(table_data[0], table_data[1], table_data[2],
               table_data[3], table_data[4], table_data[5],
               table_data[6], table_data[7], table_data[8],
               table_data[9], table_data[10], table_data[11],
               table_data[12], table_data[13], table_data[14])

    return e_html_table

#######################################################################################################################


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

    def table_data_update(self, table_data):
        self.row1_data = ["Averaging period %s.%s.%s %s:00 - %s:59" % (table_data[13], table_data[12], table_data[11],
                                                                       table_data[14], table_data[14]), "", "", "", ""]
        self.row2_data = ["CPU", "total: %.2f" % (table_data[0]), "user: %.2f" % (table_data[1]), "system: %.2f"
                          % (table_data[2]), "idle: %.2f" % (table_data[3])]
        self.row3_data = ["Memory", "total: %d" % (table_data[4]), "used: %d"
                          % (table_data[5]), "free: %d" % (table_data[6]), "cached: %d" % (table_data[7])]
        self.row4_data = ["Hard disk drive", "total: %d" % (table_data[8]), "used: %d"
                          % (table_data[9]), "free: %d" % (table_data[10]), ""]

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

    def extend(self, table_data):
        self.table_data_update(table_data)  # Update table variables
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

#######################################################################################################################


def send_email(attach_table, excel_file):
    mail = MIMEMultipart()
    mail["Subject"] = "Test message new select"
    mail["From"] = "Python interpreter"
    mail["To"] = "To Lax-T"

    em_table_part = MIMEText(attach_table, "html")

    if excel_file is not None:
        em_excel_file = MIMEBase("application", "octet-stream")
        with open(excel_file, "rb") as ef:
            em_excel_file.set_payload(ef.read())
            Encoders.encode_base64(em_excel_file)
        em_excel_file.add_header('Content-Disposition', 'attachment', filename="stats.xlsx")
        mail.attach(em_excel_file)

    mail.attach(em_table_part)
    em_client = smtplib.SMTP_SSL("smtp.gmail.com", "465")
    em_client.ehlo()
    em_client.login("****@gmail.com", "****")  # password deleted
    em_client.sendmail("****@gmail.com", "****@gmail.com", mail.as_string())  # e-mail deleted
    em_client.close()

######################################################################################################################

select_result, periods_in_sel_result = systeminfo_database.select()

if not os.path.isfile(add_database_file_name):  # Check if additional database exists
    with open(add_database_file_name, "w") as additional_database_file:
        additional_database = {"last_em_send_hour": 24,
                               "emails_sent": 0}
        additional_database_file.write(json.dumps(additional_database))

with open(add_database_file_name, "r") as additional_database_file:
    additional_database = additional_database_file.read().strip()
    additional_database = json.loads(additional_database)
last_em_send_hour = additional_database["last_em_send_hour"]
emails_sent = additional_database["emails_sent"]
current_system_hour = int(systime_customformat.split(",")[3])

if last_em_send_hour != current_system_hour+1:  # check if averaging period changed and need to send email
    index = 0
    while index < periods_in_sel_result and index < 5:  # 5 - table size limit
        html_table = extend_html_table(html_table, select_result[index])
        index += 1
    html_table += """
                </tr>
            </table>
        </body>
    </html>
    """
    if emails_sent >= 11:  # 11 - is to include excel table in every 12th email (every 12 hours)
        new_excel_table = ExcelTable()
        index = 0
        while index < periods_in_sel_result and index < 12:  # 12 - table size limit
            new_excel_table.extend(select_result[index])
            index += 1
        new_excel_table.save(excel_table_name)
        send_email(html_table, excel_table_name)
        emails_sent = 0

    else:
        send_email(html_table, None)
        emails_sent += 1

    additional_database["emails_sent"] = emails_sent
    additional_database["last_em_send_hour"] = current_system_hour
    with open(add_database_file_name, "w") as additional_database_file:
        additional_database_file.write(json.dumps(additional_database))

systeminfo_database.new_record(systime_customformat, system_usage_info)
systeminfo_database.clean()
