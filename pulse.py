import pandas as pd
from urllib import request
import date_operation as dp
from mysql.connector import connect, Error
from sqlalchemy import create_engine
import toml
import json
db_config = toml.load('./.streamlit/secrets.toml')
host=db_config['mysql']['host']
user=db_config['mysql']['user']
password=db_config['mysql']['password']
database=db_config['mysql']['database']
# conn = connect(
#     host=db_config['mysql']['host'],
#     user=db_config['mysql']['user'],
#     password=db_config['mysql']['password'],
#     database=db_config['mysql']['database']
# )
# cursor = conn.cursor()
engine = create_engine("mysql+mysqlconnector://{user}:{pw}@{host}/{db}"
				.format(host=host, db=database, user=user, pw=password))

start_date = '20200718'
end_date = '20210101'
retry = 3

def convert_json_2_df(html,date):
        df1 = pd.json_normalize(json.loads(html), record_path=['results', 'opponents'])
        df2 = pd.json_normalize(json.loads(html), record_path=['results'])
        df3 = pd.concat([df2,df2], axis=0).sort_index().reset_index(drop=True)
        res = (df3.join(df1, how='left')).loc[:,['code', 'startDate', 'endDate', 'id', 'cgeUsername', 'position', 'division', 'level', 'score',
                'isWin', 'country', 'isResigned', 'isExpired', 'ratingDelta',
                'decayValue']]
        res['startDate'] = pd.to_datetime(res['startDate'])
        res['endDate'] = pd.to_datetime(res['endDate'])
        res.insert(1, 'inc_day',date)
        return res

for i in range(dp.subtractTwoDates(end_date, start_date) + 1):
        date = dp.date(start_date, 0, i)
        start_format = date[4:6] + '%2F' + date[6:8] + '%2F' + date[2:4]
        next_date = dp.date(date, 0, 1)
        end_format = next_date[4:6] + '%2F' + next_date[6:8] + '%2F' + next_date[2:4]
        # print(date,start_format,next_date,end_format)

        url = 'https://ttapulse-backend.azurewebsites.net/v2/match?player=&skip=0&take=100000&opponent=&startDate='+start_format+'&endDate='+end_format
        print(url)
        headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
        'Authorization': 'YOUR BEARER CODE ',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Host': 'ttapulse-backend.azurewebsites.net',
        'Origin': 'https://app.ttapulse.com',
        'Referer': 'https://app.ttapulse.com/',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
        }
        req = request.Request(url, headers = headers)
        html = request.urlopen(req).read().decode()
        df = convert_json_2_df(html, date)

        engine.execute('delete from tta_pulse_data where inc_day = {}'.format(date))
        df.to_sql('tta_pulse_data', con=engine,if_exists='append',index=False)

        print (date, 'get successfully')