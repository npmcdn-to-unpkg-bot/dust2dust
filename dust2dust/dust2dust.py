# dust2dust.py
# dust2dust

# author: kil9 <krieiter@gmail.com>

import asyncio
import datetime
import functools
import json
import timeit

from flask import Flask
from flask import render_template
from bs4 import BeautifulSoup
import pika
import requests

from config import *

app = Flask(__name__)

async def get_ijimobile_data():
    loop = asyncio.get_event_loop()
    start = timeit.default_timer()
    ijimobile_url = 'http://ijistance.herokuapp.com/report/kil9'
    try:
        resp = await loop.run_in_executor(None, requests.get, ijimobile_url)
    except requests.exceptions.ConnectionError as e:
        log.error('connection error to EZMobile')
        return { 'status': 'failed' }
    if not resp.ok:
        return 'not ok'

    data_iji = json.loads(resp.text)

    duration = timeit.default_timer() - start
    log.info('ijimobile: {0:.2f} seconds elapsed'.format(duration))
    return data_iji

async def get_dust_data():
    loop = asyncio.get_event_loop()
    start = timeit.default_timer()

    dust_url = 'http://m.airkorea.or.kr/sub_new/sub41.jsp'
    cookies_suzi = { 'isGps': 'N', 'station': '131412' } # TODO: 코드 중복 제거
    cookies_baekhyun = { 'isGps': 'N', 'station': '131120' }

    try:
        result_suzi = await loop.run_in_executor(None, functools.partial(requests.get, dust_url, cookies=cookies_suzi))
        result_baekhyun = await loop.run_in_executor(None, functools.partial(requests.get, dust_url, cookies=cookies_baekhyun))
    except requests.exceptions.ConnectionError as e:
        log.error('connection error to AirKorea')
        return {'pm10': {'24h': '0', '1h': '0'}, 'pm25': {'24h': '0', '1h': '0'}}

    if not result_suzi.ok or not result_baekhyun.ok:
        log.error('failed to get results')
        return {'pm10': {'24h': '0', '1h': '0'}, 'pm25': {'24h': '0', '1h': '0'}}

    soup_suzi = BeautifulSoup(result_suzi.text, 'html.parser')
    soup_baekhyun = BeautifulSoup(result_baekhyun.text, 'html.parser')

    tag_pm10 = soup_suzi.find('div', id='detailContent') \
                        .findAll('table')[1] \
                        .findAll('tr')[1] \
                        .findAll('td')[1] \
                        .div.text

    tag_pm25 = soup_baekhyun.find('div', id='detailContent') \
                            .findAll('table')[1] \
                            .findAll('tr')[2] \
                            .findAll('td')[1] \
                            .div.text
    dust_pm10 = dict(zip(('24h', '1h'), tag_pm10.replace('(1h)', '').replace(' ㎍/㎥', '').split('(24h)')))
    dust_pm25 = dict(zip(('24h', '1h'), tag_pm25.replace('(1h)', '').replace(' ㎍/㎥', '').split('(24h)')))

    data_dust = { 'pm10': dust_pm10, 'pm25': dust_pm25 }
    duration = timeit.default_timer() - start
    log.info('dust(airkorea): {0:.2f} seconds elapsed'.format(duration))
    return data_dust

async def get_weather_data():
    loop = asyncio.get_event_loop()
    start = timeit.default_timer()
    weather_url = 'http://www.kma.go.kr/wid/queryDFSRSS.jsp?zone=4146556000'
    result = await loop.run_in_executor(None, requests.get, weather_url)
    if not result.ok:
        return { 'status': 'failed' }

    soup = BeautifulSoup(result.text, 'html.parser')

    #seq = soup.rss.channel.item.description.body.find('data', seq='0')
    seqs = map(lambda i: soup.rss.channel.item.description.body.find('data', seq=str(i)), range(5))

    def repack(seq):
        data_time = int(seq.hour.text)
        weather_en = seq.wfen.text

        is_day = data_time >= 6 and data_time <= 18 # TODO: 실제 일출/일몰 시간 읽도록 변경
        day_str = 'DAY' if is_day else 'NIGHT'
        weather_icon = get_weather_icon(weather_en, day_str)

        return { 'hour': seq.hour.text,
                 'temp': seq.temp.text,
                 'r06': seq.r06.text,
                 'weather': seq.wfkor.text,
                 'weather_en': weather_en,
                 'weather_icon': weather_icon,
                 'wet': seq.reh.text
                }

    duration = timeit.default_timer() - start
    log.info('weather(kma): {0:.2f} seconds elapsed'.format(duration))
    data_weather = { 'date': soup.rss.channel.pubdate.text, 'data': list(map(repack, seqs)) }
    return data_weather

async def fetch_data():
    tasks = [
        asyncio.Task(get_weather_data()),
        asyncio.Task(get_ijimobile_data()),
        asyncio.Task(get_dust_data()) ]

    return await asyncio.gather(*tasks)

@app.route('/')
def main():
    start = timeit.default_timer()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    results = loop.run_until_complete(fetch_data())
    weather_payload, ijimobile_payload, dust_payload = results

    payload = {
        'weather': weather_payload,
        'iji': ijimobile_payload,
        'dust': dust_payload
    }

    duration = timeit.default_timer() - start

    log.info('main: {0:.2f} elapsed'.format(duration))

    loop.close()

    return render_template('index.html', payload=payload)

# weather_eng: 'Clear', 'Partly Cloudy', 'Mostly Cloudy', 'Cloudy', 'Rain', 'Snow/Rain'
def get_weather_icon(weather_en, day_str):
    if weather_en == 'Clear':
        return 'CLEAR_' + day_str
    elif weather_en == 'Partly Cloudy':
        return 'PARTLY_CLOUDY_' + day_str
    elif weather_en == 'Mostly Cloudy':
        return 'CLOUDY'
    elif weather_en == 'Cloudy':
        return 'CLOUDY'
    elif weather_en == 'Rain':
        return 'RAIN'
    elif 'Snow' in weather_en:
        return 'SNOW'
    else:
        return 'FOG'


def enqueue_activate(message):
    log.debug('received event to publish: {}'.format(message))

    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_TX_URL))
    channel = connection.channel()

    channel.queue_declare(queue=RABBITMQ_QUEUE)

    channel.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE, body=message)

    connection.close()

    return 'published {}'.format(message)

@app.route('/activate')
def activate():
    log.info('dust2dust activated')
    try:
        msg = enqueue_activate('dust2dust go')
    except:
        msg = 'failed to enqueue dust2dust event'
        log.exception(msg)
        return msg
    return msg

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=21000, debug=True)
