import sys
import redis
import logging
import redis.exceptions

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self, config, host='127.0.0.1', port=6379, debug=False):
        self._config = config
        self.host = self._config.find_one('$.broker.host', default=host)
        self.port = self._config.find_one('$.broker.port', default=port)
        self._debug = self._config.find_one('$.app.debug', default=debug)
        self._conn = None
        self._uri = f'redis://{self.host}:{self.port}'
        self.connect()

    def connect(self):
        self._conn = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True
        )

    def get(self, key):
        self._conn.get(key)

    def delete(self, key):
        self._conn.delete(key)

    def publish(self, topic, message):
        try:
            self._conn.set(topic, message)
            logger.info('message published successfully')
        except redis.exceptions.ConnectionError as e:
            logger.error(f'unable to send message to {self._uri}, service unavailable')
            pass
