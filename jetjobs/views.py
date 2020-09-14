from django.conf.urls import url
from django.contrib import messages
from jet.dashboard import dashboard
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest
from django.http import JsonResponse
from django.contrib.auth import get_user_model, authenticate, login
from dashboard_modules import JobModule
from django.db.models import Q

from .models import Advanced_Job

from datetime import datetime
from threading import Thread
import yfinance as yf
import pandas as pd
import requests
import telegram
import json
import uuid
import time

global tele_token, token
tele_token = '1026004095:AAExRCu6FxrEdaax8cjSOaB231CszAs9Iqw'
token = 'pk_b2888572a402481fbf8a6c047abdadda'

# Create your views here.
def home(request):
    return render(request, 'admin/base.html')


def historical_data(symbol, interval='1h', period='5y'):
	columns = ['Symbol', 'Datetime', 'Open', 'High', 'Low', 'Close']
	try:
		ticker = yf.Ticker(symbol)
		if interval=='1m':
			df = ticker.history(interval=interval, period='5d')
		elif 'mo' in interval or 'wk' in interval:
			df = ticker.history(interval=interval, period='5y')
			df = df.dropna()
		else:
			df = ticker.history(interval=interval)
		df = df.reset_index(col_level=0)
		df['Symbol'] = symbol
		columns = df.columns.tolist()
		columns[0] = 'Datetime'
		df.columns = columns
		columns = ['Symbol', 'Datetime', 'Open', 'High', 'Low', 'Close']
		df = df[columns]
		print(df.iloc[0])
	except:
		root_url = 'https://api.binance.com/api/v1/klines'
		url = root_url + '?symbol=' + symbol + '&interval=' + interval
		data = json.loads(requests.get(url).text)
		df = pd.DataFrame(data)
		df.columns = ['open_time',
			'Open', 'High', 'Low', 'Close', 'v',
			'Datetime', 'qav', 'num_trades',
			'taker_base_vol', 'taker_quote_vol', 'ignore']
		df['Symbol'] = symbol
		df = df[columns]
		df['Datetime'] = [datetime.fromtimestamp(x/1000.0) for x in df['Datetime']]

	df['Datetime'] = pd.to_datetime(df['Datetime'])
	df = df.tail(50).reset_index(drop=True)
	df['Close'] = df['Close'].fillna(method='ffill')
	df['Close'] = df['Close'].astype(float)

	return df


def calculate_rsi_old(df, n=14):
    delta = df['Close'].diff()
    dUp, dDown = delta.copy(), delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0

    RolUp = dUp.rolling(window=n).mean()
    RolDown = dDown.rolling(window=n).mean().abs()

    RS = RolUp / RolDown
    df['RSI']= 100.0 - (100.0 / (1.0 + RS))
    return df


def calculate_rsi(df, time_window=14):
    data = df['Close']
    diff = data.diff(1).dropna()
    
    up_chg = 0 * diff
    down_chg = 0 * diff
    up_chg[diff > 0] = diff[ diff>0 ]
    down_chg[diff < 0] = diff[ diff < 0 ]
    
    up_chg_avg   = up_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    down_chg_avg = down_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    df['RSI'] = rsi

    return df


def bollingerbands(df, n=20, bb_std=2):
	print(n)
	print(bb_std)
	df['MA20'] = df['Close'].rolling(window=n).mean()
	df['20dSTD'] = df['Close'].rolling(window=n).std()
	df['Upper'] = df['MA20'] + (df['20dSTD'] * bb_std)
	df['Lower'] = df['MA20'] - (df['20dSTD'] * bb_std)

	return df


def sendAlertToChannel(msg):
    chat_id = '@jackie_stock_channel'
    url = 'https://api.telegram.org/bot{}/'.format(tele_token)
    params = {
        'chat_id': chat_id,
        'text': msg
    }

    res = requests.post(url+'sendMessage', data=params)
    print(res.json())


def sendAlertToGroupOrUser(msg):
    tele_token = '1026004095:AAExRCu6FxrEdaax8cjSOaB231CszAs9Iqw'

    bot = telegram.Bot(tele_token)
    chat_id = '-446515297'
    msg = msg
    print(bot.send_message(chat_id=chat_id, text=msg))


def send_alert(alerts):
	for alert in alerts:
		msg = json.dumps(alert, indent=4)
		msg = ""
		for key in alert.keys():
			msg += "{}: {}\n".format(key, alert[key])

		sendAlertToChannel(msg)
		# sendAlertToGroupOrUser(msg)


def run_monitoring(job, user_id):
	current_time = datetime.now().time()
	prev_hour = current_time.hour
	prev_minute = current_time.minute
	isCheck = True
	while True:

		if isCheck:
			symbol = job.symbol
			interval = job.interval
			rsi_period = job.rsi_period
			rsi_value = job.rsi_value
			bb_period = job.bb_period
			bb_option = job.bb_option
			# bb_upperband = job.bb_upperband
			# bb_lowerband = job.bb_lowerband
			bb_std = job.bb_std_num

			interval = interval.replace(' min', 'm')
			interval = interval.replace(' hour', 'h')
			interval = interval.replace(' day', 'd')
			interval = interval.replace(' week', 'wk')
			interval = interval.replace(' month', 'mo')

			print(symbol, interval, rsi_period)
			
			df = historical_data(symbol, interval=interval)
			df = calculate_rsi(df, time_window=rsi_period)
			df = bollingerbands(df, n=bb_period, bb_std=bb_std)
			print(df)

			lastvalue = df.iloc[-1]
			print(lastvalue)
			rsi = lastvalue['RSI']
			upper = lastvalue['Upper']
			lower = lastvalue['Lower']
			close = lastvalue['Close']
			bb_value = {'Upperband': upper, 'Lowerband': lower}
			alerts = []

			if rsi >= rsi_value:
				alert = {
					'Job name': job.name,
					'Symbol': symbol,
					'Time': datetime.now().time().strftime("%H:%M:%S"),
					'Alert': 'Crossed over defined RSI value!',
					'RSI value': rsi,
				}
				alerts.append(alert)
			if bb_option=='Upperband':
				if close >= upper:
					alert = {
						'Job_name': job.name,
						'Symbol': symbol,
						'Time': datetime.now().time().strftime("%H:%M:%S"),
						'Alert': 'Reached bollingerbands upperband!',
						'Current close': close,
					}
					alerts.append(alert)
			if bb_option=='Lowerband':
				if close <= lower:
					alert = {
						'Job_name': job.name,
						'Symbol': symbol,
						'Time': datetime.now().time().strftime("%H:%M:%S"),
						'Alert': 'Reached bollingerbands lowerband!',
						'Current close': close,
					}
					alerts.append(alert)
			if len(alerts) == 0:
				alert = {
					'Job_name': job.name,
					'Symbol': job.symbol,
					'Time': datetime.now().time().strftime("%H:%M:%S"),
					'Alert': 'No alert!',
					'RSI value': rsi,
					'Current close': close,
				}
				alerts.append(alert)
				
			# sending alert to telegram
			send_alert(alerts)

			print(json.dumps(alerts, indent=4))
			with open('data.json', 'w') as f:
				json.dump(alerts, f, indent=4)
				time.sleep(1)
		# else:
		# 	alerts = []
		# 	alert = {
		# 		'Job_name': job.name,
		# 		'Symbol': job.symbol,
		# 		'Time': datetime.now().time().strftime("%H:%M:%S"),
		# 		'Alert': 'No alert!'
		# 	}
		# 	alerts.append(alert)
		# 	send_alert(alerts)
		# 	print(json.dumps(alerts, indent=4))
		# 	with open('data.json', 'w') as f:
		# 		json.dump(alerts, f, indent=4)
		# 		time.sleep(1)

		# determine if we need to check again the historical data		
		my_jobs = Advanced_Job.objects.filter(Q(user_id=user_id))
		if not my_jobs:
			data = {
				'job_name': job.name,
				'time': datetime.now().time().strftime("%H:%M:%S"),
				'status': 'Stopped'
			}
			print(data)
			with open('data.json', 'w') as f:
				json.dump(data, f, indent=4)
			print('Job stopped or db not found. Exiting now...')
			break
		else:
			current_time = datetime.now().time()
			print(current_time)
			current_hour = current_time.hour
			current_minute = current_time.minute
			if 'h' in job.interval:
				print('hourly')
				time_interval = int(job.interval.split('h')[0].strip(' '))
				if current_hour - prev_hour >= time_interval:
					prev_hour = current_hour
					prev_minute = current_minute
					isCheck = True
				else:
					isCheck = False
			elif 'min' in job.interval:
				print('minutely')
				time_interval = int(job.interval.split('m')[0].strip(' '))
				if current_minute - prev_minute >= time_interval or (current_minute < prev_minute and current_minute+60 > prev_minute):
					prev_hour = current_hour
					prev_minute = current_minute
					isCheck = True
				else:
					isCheck = False

		print(isCheck)
		time.sleep(2)

@csrf_exempt
def start_monitor(request):
	base_url = request.build_absolute_uri('/').strip("/")
	try:
		titles = request.POST.getlist("title")
		symbols = request.POST.getlist("symbol")
		intervals = request.POST.getlist("interval")
		rsi_periods = request.POST.getlist("rsi_period")
		rsi_values = request.POST.getlist("rsi_value")
		bb_periods = request.POST.getlist("bb_period")
		bb_options = request.POST.getlist("bb_option")
		# bb_upperbands = request.POST.getlist("bb_upperband")
		# bb_lowerbands = request.POST.getlist("bb_lowerband")
		bb_stds = request.POST.getlist("bb_std")
		user_id = request.user.id
	except:
		print('No jobs defined')
		return redirect('/admin/')

	print(titles)
	for i in range(len(titles)):
		title = titles[i]
		symbol = symbols[i]
		interval = intervals[i]
		rsi_period = int(rsi_periods[i])
		rsi_value = float(rsi_values[i])
		bb_period = int(bb_periods[i])
		bb_option = bb_options[i]
		# bb_upperband = float(bb_upperbands[i])
		# bb_lowerband = float(bb_lowerbands[i])
		bb_std = int(bb_stds[i])
		print(title, interval)
		try:
			result = Advanced_Job.objects.filter(Q(user_id=user_id) & Q(name=title))
			if result:
				print('There is a record', result)
				pass
			else:
				print('There was no record')
				print("{} is being inserted...".format(title))
				job_instance = Advanced_Job.objects.create(
					user_id = user_id,
					name = title,
					symbol = symbol,
					interval = interval,
					rsi_period = rsi_period,
					rsi_value = rsi_value,
					bb_period = bb_period,
					bb_option = bb_option,
					# bb_upperband = bb_upperband,
					# bb_lowerband = bb_lowerband,
					bb_std_num=bb_std
				)
		except:
			print("{} is being inserted...".format(title))
			job_instance = Advanced_Job.objects.create(
				user_id = user_id,
				name = title,
				symbol = symbol,
				interval = interval,
				rsi_period = rsi_period,
				rsi_value = rsi_value,
				bb_period = bb_period,
				bb_option = bb_option,
				# bb_upperband = bb_upperband,
				# bb_lowerband = bb_lowerband,
				bb_std_num=bb_std
			)

	my_jobs = Advanced_Job.objects.filter(Q(user_id=user_id))
	for job in my_jobs:
		print(job.name)
		th = Thread(target=run_monitoring, args=(job, user_id))
		th.start()

	return redirect('/admin/')


def view_monitor(request):
	try:
		with open('data.json') as f:
			data = json.load(f)
	except:
		data = 'Alert not ready!'
	params = {'data': data}
	
	return render(request, 'admin/monitor.html', params)


def stop_monitor(request):
	user_id = request.user.id
	Advanced_Job.objects.filter(Q(user_id=user_id)).delete()

	my_jobs = Advanced_Job.objects.filter(Q(user_id=user_id))
	print(my_jobs)
	
	return redirect('/admin/')
