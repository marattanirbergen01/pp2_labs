import datetime

#Task1:
x = datetime.datetime.today()
y = datetime.datetime.today() - datetime.timedelta(5)
print("5 days before: ", y)
print("Today: ", x)

#Task2:
today = datetime.datetime.today()
yesterday = today - datetime.timedelta(1)
tomorrow = today + datetime.timedelta(1)
print("Yesterday: ", yesterday)
print("Today: ", today)
print("Tomorrow ", tomorrow)

#Task3:
today = datetime.datetime.today().replace(microsecond=0)
print(today)

#Task4:
x = datetime.datetime.today().replace(microsecond=0)
date1 = x
y = input() #2024-01-26 00:00:00
date2 = datetime.datetime.strptime(y, '%Y-%m-%d %H:%M:%S')
def dif(date1, date2):
    difference = date1 - date2
    return difference.days * 24 * 3600 + difference.seconds
print(date1)
print(date2)
print(dif(date1, date2))