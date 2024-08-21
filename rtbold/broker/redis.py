import sys
import redis
import logging
import redis.exceptions

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self, host='localhost', port=6379):
        self._host = host
        self._port = port
        self._connstr = f'redis://{self._host}:{self._port}'
        self.connect()
        self._connected = False

    def connect(self):
        logger.info(f'connecting to {self._connstr}')
        self._conn = redis.Redis(
            host=self._host,
            port=self._port,
            decode_responses=True
        )

    def publish(self, topic, message):
        try:
            self._conn.set(topic, message)
        except redis.exceptions.ConnectionError as e:
            logger.error(f'unable to send message to {self._connstr}, service unavailable')
            pass
