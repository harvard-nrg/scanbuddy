import sys
import redis
import logging
import redis.exceptions

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self, config, host='localhost', port=6379):
        self._config = config
        self._host = self._config.find_one('$.broker.host', default=host)
        self._port = self._config.find_one('$.broker.port', default=port)
        self._conn = None
        self._uri = f'redis://{self._host}:{self._port}'
        self.connect()

    def connect(self):
        self._conn = redis.Redis(
            host=self._host,
            port=self._port,
            decode_responses=True
        )

    def publish(self, topic, message):
        try:
            self._conn.set(topic, message)
            logger.info('message published successfully')
        except redis.exceptions.ConnectionError as e:
            logger.error(f'unable to send message to {self._uri}, service unavailable')
            pass
