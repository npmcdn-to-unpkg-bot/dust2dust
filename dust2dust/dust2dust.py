# dust2dust.py
# dust2dust

# author: kil9 <krieiter@gmail.com>

import datetime

from flask import Flask
from flask import render_template
from bs4 import BeautifulSoup
import pika
import requests

from config import *

app = Flask(__name__)

@app.route('/')
def main():

    weather_url = 'http://www.kma.go.kr/wid/queryDFSRSS.jsp?zone=4146556000'
    result = requests.get(weather_url)
    if not result.ok:
        return render_template('index.html', payload='failed')

    soup = BeautifulSoup(result.text, 'html.parser')

    seq = soup.rss.channel.item.description.body.find('data', seq='0')

    # weather_eng: 'Clear', 'Partly Cloudy', 'Mostly Cloudy', 'Cloudy', 'Rain', 'Snow/Rain'
    now = datetime.datetime.now()

    is_day = now.hour >= 6 and now.hour <= 18 # TODO: 실제 일출/일몰 시간 읽도록 변경
    day_str = 'DAY' if is_day else 'NIGHT'

    weather_en = seq.wfen.text

    if weather_en == 'Clear':
        weather_icon = 'CLEAR_' + day_str
    elif weather_en == 'Partly Cloudy':
        weather_icon = 'PARTLY_CLOUDY_' + day_str
    elif weather_en == 'Mostly Cloudy':
        weather_icon = 'CLOUDY'
    elif weather_en == 'Cloudy':
        weather_icon = 'CLOUDY'
    elif weather_en == 'Rain':
        weather_icon = 'RAIN'
    elif 'Snow' in weather_en:
        weather_icon = 'SNOW'
    else:
        weather_icon = 'FOG'

    payload = {
        'date': soup.rss.channel.pubdate.text,
        'hour': seq.hour.text,
        'temp': seq.temp.text,
        'weather': seq.wfkor.text,
        'weather_en': weather_en,
        'weather_icon': weather_icon,
        'wet': seq.reh.text,
        'now': now.strftime('%Y/%m/%d %H:%M:%S')
    }

    return render_template('index.html', payload=payload)

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
