# config.py
# dust2dust

# author: kil9 <krieiter@gmail.com>

import logging
import os
import sys

RABBITMQ_QUEUE = 'dust2dust_jobqueue'

RABBITMQ_RX_URL = os.environ['RABBITMQ_BIGWIG_RX_URL']
RABBITMQ_TX_URL = os.environ['RABBITMQ_BIGWIG_TX_URL']
#rabbitmq_url = os.environ['RABBITMQ_BIGWIG_URL']

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger(__name__)
#log.addHandler(LogentriesHandler(logentries_key))


