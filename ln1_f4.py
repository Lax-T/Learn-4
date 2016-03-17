#!/usr/bin/python
#coding: utf8
#Програма повинна запускатися кожних 5хв (12 запусків за год) і записувати статистику використання ресурсів в БД, через годину 
#дані з БД усереднюються та відправляються на електронку у вигляді таблиці з статистикою

import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

data_string = [] #Усі дані зберігаються у форматі cpu_total,cpu_user,cpu_sys,cpu_idle,mem_total,mem_used,mem_free,mem_cached,hdd_total,hdd_used,hdd_free

def get_raw_data(command): #функція виконує консольну команду та повертає результат
    command_data = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (command_data, err) = command_data.communicate()
    command_data = command_data.replace(",",".") #Заміна ком на крапки для коректного виконання float()
    return command_data.split()

raw = get_raw_data("mpstat") #обробка даних по завантаженості процесора
cpu_user = float(raw[21])
cpu_sys = 0
for x in raw[22:29]:
    cpu_sys = cpu_sys + float(x)
cpu_total = cpu_user + cpu_sys
cpu_idle = float(raw[30])
cpu_string = ("CPU - Total used:%s%%, User:%s%%, System:%s%%, Idle:%s%%" % (cpu_total, cpu_user, cpu_sys, cpu_idle))
print (cpu_string) #в принципі виводити проміжні дані в консоль непотрібно але я залишив це

raw = get_raw_data("free -m") #обробка даних по завантаженості оперативної памяті
mem_total = int(raw[7])
mem_used = int(raw[8])
mem_free = int(raw[9])
mem_cached = int(raw[12])
mem_string = ("MEMORY - Total:%sMb, Used:%sMb, Free:%sMb, Cached:%sMb" % (mem_total, mem_used, mem_free, mem_cached))
print (mem_string)

raw = get_raw_data("df -m --total") #обробка данних по жорсткому диску
hdd_total = int(raw[50])
hdd_used = int(raw[51])
hdd_free = int(raw[52])
hdd_string = ("Hard disk drive - Total:%sMb, Used:%sMb, Free:%sMb" % (hdd_total, hdd_used, hdd_free))
print (hdd_string)

                        #формування єдиного рядка з данними для запису в файл
var_names_list = [cpu_total,cpu_user,cpu_sys,cpu_idle,mem_total,mem_used,mem_free,mem_cached,hdd_total,hdd_used,hdd_free]
for x in var_names_list:
    data_string.append(x)

###############################################################################################################

try:
    database_file = open("database.txt", "r") #пробую відкрити файл БД
    db_lines_count = int(database_file.readline())

except IOError:
    database_file = open("database.txt", "w") #якщо помилка то створюю чистий
    database_file.write("0"+"\n")
    db_lines_count = 0

finally:
    database_file.close() #закриваю файл

database_file = open("database.txt", "a") #відкриваю файл та добавляю рядок з данними в БД
database_file.write(str(data_string) + "\n")
database_file.close()
db_lines_count += 1
database_file = open("database.txt", "r+") #перезаписую лічильник кількості рядків в БД
database_file.seek(0,0)
database_file.write(str(db_lines_count) + "\n")
database_file.close()

###############################################################################################################

if db_lines_count >= 12: #перевіряю чи записана достатня кількість рядків, якщо так то починаю обробку
    database_file = open("database.txt", "r")
    dump = database_file.readline() #"пуста" процедура зчитування щоб пропустити рядок з лічильником

    for x in range(0,len(var_names_list)): #попередньо очищаю комірки cpu_total... та інші перед початком виборки з БД
        var_names_list[x] = 0

    ckl_counter = 0
    while ckl_counter < db_lines_count: #цикл виборки рядків з БД
        data_string = database_file.readline()
        data_string = data_string.translate(None,"[]") #позбуваюся квадратних душок на початку та кінці рядка (кращого способу поки не придумав)
        data_string = data_string.split(",") #розбиваю рядок в список і заодно позбуваюся ком
        for string_index,x in enumerate(data_string): #в даному циклі претворюю данні з списку в int та float та розфасовую по комірках CPU_total... і т.д.
            try:
                x = int(x)
            except:
                x = float(x)
            var_names_list[string_index] = var_names_list[string_index] + x #сумую онотипні дані щоб в результаті отримати усереднене значення
        ckl_counter += 1

    database_file.close() #очищаю файл БД
    database_file = open("database.txt", "w")
    database_file.write("0"+"\n")
    database_file.close()

    for x in range(0,len(var_names_list)): #розділяю підсумовані значення на кількість зчитаних рядків (получаю усереднене значення)
        var_names_list[x] = var_names_list[x] / db_lines_count
    print (var_names_list)


###############################################################################################################
    mail = MIMEMultipart("alternative") #формую емайл
    mail["Subject"] = "Test message"
    mail["From"] = "Python interpreter"
    mail["To"] = "To Lax-T"

    #em_part1 = MIMEText(cpu_string+"\n"+hdd_string+"\n"+mem_string, "plain") тестовий рядок (вже непотрібен)

                    #формую просту HTML таблицю, з шрифтами та кольором поки не заморочувався
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
    """.format(str(cpu_total),str(cpu_user),str(cpu_sys),str(cpu_idle),str(mem_total),str(mem_used),str(mem_free),str(mem_cached),str(hdd_total),str(hdd_used),str(hdd_free))

    em_part2 = MIMEText(em_html, "html")
    mail.attach(em_part2)
                    #відправляю лист на свою електронку
    em_client = smtplib.SMTP_SSL("smtp.gmail.com", "465")
    em_client.ehlo()
    em_client.login("irlml4313@gmail.com", "************") #пароль затертий
    em_client.sendmail("irlml4313@gmail.com", "**********@gmail.com", mail.as_string()) #емейл затертий
    em_client.close()