import pika
import requests

from config import *

def dust_callback(ch, method, properties, body):
    log.info('dust callback!')

    AIRKOREA_ENDPOINT = 'http://m.airkorea.or.kr/sub_new/sub41.jsp'
    cookies = dict( isGps='N',
                    station='131120',
                    lat='37.3681575',
                    lng='127.10022305')

    r = requests.get(AIRKOREA_ENDPOINT, cookies=cookies)
    print(r.text)

def consume():
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_RX_URL))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    channel.basic_consume(dust_callback, queue=RABBITMQ_QUEUE, no_ack=True)
    log.info(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

    return 'consume finished'

if __name__ == '__main__':
    consume()

