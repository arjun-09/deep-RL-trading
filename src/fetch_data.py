import datetime
import subprocess

def months_between(start_date, end_date):
    if start_date > end_date:
        raise ValueError(f"Start date {start_date} is not before end date {end_date}")

    year = start_date.year
    month = start_date.month

    while (year, month) <= (end_date.year, end_date.month):
        yield datetime.date(year, month, 1)

        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

def fetch_data(coin_name, interval, month, daily=False):
    if not daily:
        time = month.strftime("%Y-%m")
    else:
        time = month
    
    date_time = interval + '-' + time

    file_name_zip = '{}-{}.zip'.format(coin_name, date_time)
    file_name = file_name_zip.split('.')[0]
    cmd = 'curl -O https://data.binance.vision/data/futures/um/monthly/klines/{}/{}/{}'.format(coin_name, interval, file_name_zip)

    print(cmd)

    subprocess.call('rm {}'.format(file_name_zip), shell=True)
    subprocess.call('rm -rf {}'.format(file_name), shell=True)
    subprocess.call(cmd, shell=True)
    subprocess.call('unzip {}'.format(file_name_zip), shell=True) #.format(file_name_zip), shell=True)
    
    return file_name

def fetch_coin_data(coin_name="BTCUSDT", interval="1m", start_year_month="2020-06", end_year_month="2021-07", daily=False):
    start_time = datetime.datetime.strptime(start_year_month, '%Y-%m')
    end_time = datetime.datetime.strptime(end_year_month, '%Y-%m')

    files = []

    if daily:
        files.append(fetch_data(coin_name, intevral, start_year_month, daily))
        return files

    for month in months_between(start_time, end_time):
        files.append(fetch_data(coin_name, interval, month, daily))

    return files
