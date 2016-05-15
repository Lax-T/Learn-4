#!/usr/bin/python
# coding: utf8

import datetime

import ln1_f4_31

DATABASE_FILE_NAME = '/home/lax/PycharmProjects/learn1/database4'
ADD_DATABASE_FILE_NAME = '/home/lax/PycharmProjects/learn1/add_database4'
EXCEL_TABLE_NAME = '/home/lax/PycharmProjects/learn1/new method test.xlsx'
SENDER_EADRESS = '***@gmail.com'
SENDER_EPASSWORD = '***'
RECEIVER_EADRESS = '***@gmail.com'

system_usage_info = ln1_f4_31.get_cpu_info() + ln1_f4_31.get_mem_info() + ln1_f4_31.get_hdd_info()
print system_usage_info
systime_customformat = datetime.datetime.now()
systime_customformat = systime_customformat.strftime('%Y,%m,%d,%H,%M,%S')

systeminfo_database = ln1_f4_31.SysinfoDatabase(DATABASE_FILE_NAME)

select_result, periods_in_sel_result = systeminfo_database.select()

additional_database = ln1_f4_31.load_additionad_database(ADD_DATABASE_FILE_NAME)
last_em_send_hour = additional_database['last_em_send_hour']
emails_sent = additional_database['emails_sent']
current_system_hour = int(systime_customformat.split(',')[3])

html_table = ln1_f4_31.start_html_table()

if last_em_send_hour != current_system_hour+1:  # check if averaging period changed and need to send email
    index = 0
    while index < periods_in_sel_result and index < 5:  # 5 - table size limit
        html_table = ln1_f4_31.extend_html_table(html_table, select_result[index])
        index += 1
    html_table = ln1_f4_31.end_html_table(html_table)
    if emails_sent >= 11:  # 11 - is to include excel table in every 12th email (every 12 hours)
        new_excel_table = ln1_f4_31.ExcelTable()
        index = 0
        while index < periods_in_sel_result and index < 12:  # 12 - table size limit
            new_excel_table.extend(select_result[index])
            index += 1
        new_excel_table.save(EXCEL_TABLE_NAME)
        ln1_f4_31.send_email(html_table, EXCEL_TABLE_NAME, SENDER_EADRESS, SENDER_EPASSWORD, RECEIVER_EADRESS)
        emails_sent = 0

    else:
        ln1_f4_31.send_email(html_table, None, SENDER_EADRESS, SENDER_EPASSWORD, RECEIVER_EADRESS)
        emails_sent += 1

    additional_database['emails_sent'] = emails_sent
    additional_database['last_em_send_hour'] = current_system_hour
    ln1_f4_31.update_additional_database(ADD_DATABASE_FILE_NAME, additional_database)

systeminfo_database.new_record(systime_customformat, system_usage_info)
systeminfo_database.clean()
