import sys
import redis
import logging
from pubsub import pub
import redis.exceptions


logger = logging.getLogger(__name__)

class MessageBroker:
    KEY_PREFIX = 'scanbuddy_message:'
    MESSAGE_TTL = 3600

    def __init__(self, config, host='127.0.0.1', port=6379, debug=False):
        self._config = config
        self.host = self._config.find_one('$.broker.host', default=host)
        self.port = self._config.find_one('$.broker.port', default=port)
        self._debug = self._config.find_one('$.app.debug', default=debug)
        self._conn = None
        self._uri = f'redis://{self.host}:{self.port}'
        self.connect()
        pub.subscribe(self.on_reset, 'reset')

    def connect(self):
        self._conn = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True
        )

    def get(self, key):
        return self._conn.get(key)

    def delete(self, key):
        self._conn.delete(key)

    def publish(self, key, message):
        full_key = f'{self.KEY_PREFIX}{key}'
        try:
            self._conn.set(full_key, message, ex=self.MESSAGE_TTL)
            logger.info(f'message published successfully with key {full_key}')
        except redis.exceptions.ConnectionError as e:
            logger.error(f'unable to send message to {self._uri}, service unavailable')

    def get_all_messages(self):
        try:
            keys = self._conn.keys(f'{self.KEY_PREFIX}*')
            return {key: self._conn.get(key) for key in keys}
        except redis.exceptions.ConnectionError as e:
            logger.error(f'unable to get messages from {self._uri}, service unavailable')
            return {}

    def delete_all_messages(self):
        try:
            keys = self._conn.keys(f'{self.KEY_PREFIX}*')
            if keys:
                self._conn.delete(*keys)
                logger.info(f'deleted {len(keys)} messages from redis')
        except redis.exceptions.ConnectionError as e:
            logger.error(f'unable to delete messages from {self._uri}, service unavailable')

    def on_reset(self):
        logger.info('reset received, deleting all messages from redis')
        self.delete_all_messages()