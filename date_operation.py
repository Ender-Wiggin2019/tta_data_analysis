from datetime import datetime, timedelta
from logging import currentframe
from dateutil.relativedelta import relativedelta
'''
A module for date operation in form of 'YYYYmmdd'
'''

def to_date(date,offset_month=0,offset_day=0,offset_hour=0):
    return datetime.strptime(date,'%Y%m%d')  + relativedelta(months=+offset_month) + timedelta(days=offset_day,hours=offset_hour)

def date(date,offset_month=0,offset_day=0,offset_hour=0):
    return (datetime.strptime(date,'%Y%m%d') + relativedelta(months=+offset_month) + timedelta(days=offset_day,hours=offset_hour)).strftime('%Y%m%d')

def first_date(date):
    return ((to_date(date)).replace(day=1)).strftime('%Y%m%d')

def last_date(date):
    return ((to_date(date)+relativedelta(months=1)).replace(day=1)-timedelta(days=1)).strftime('%Y%m%d')

def subtractTwoDates(date1,date2): # string, string -> int
    return (datetime.strptime(date1,'%Y%m%d')-datetime.strptime(date2,'%Y%m%d')).days

def jdyDateToString(jdy_data,jdy_date,modified_day = 0, modified_hours = 0): # string -> string
    return (datetime.strptime(jdy_data[jdy_date][0:jdy_data[jdy_date].find('T')],'%Y-%m-%d')+timedelta(days=modified_day,hours=modified_hours)).strftime('%Y%m%d')

def jdyDateFormatToString(jdy_date,modified_day = 0, modified_hours = 0): # string -> string
    return (datetime.strptime(jdy_date[0:jdy_date.find('T')],'%Y-%m-%d')+timedelta(days=modified_day,hours=modified_hours)).strftime('%Y%m%d')

def toFullName(p_date):
    return to_date(p_date).strftime("%B")

def toAbbrName(p_date):
    return to_date(p_date).strftime("%b")

today = datetime.today().strftime('%Y%m%d')
yesterday = date(today,0,-1,0)
first_date_with_curr_date = (datetime.today().replace(day=1)).strftime('%Y%m%d')
last_date_with_curr_date = ((datetime.today()+relativedelta(months=1)).replace(day=1)-timedelta(days=1)).strftime('%Y%m%d')

