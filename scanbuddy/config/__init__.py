import yaml
import logging
from jsonpath_ng import parse

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, file):
        self._file = file
        self.parse()

    def parse(self):
        with open(self._file) as fo:
            self._config = yaml.safe_load(fo)
        
    def update_or_create(self, key, value):
        jp = parse(key)
        jp.update_or_create(self._config, value)

    def find_one(self, expr, default=None):
        jsonpath = parse(expr)
        match = jsonpath.find(self._config)  
        if not match:
            return default
        return match.pop().value

class ConfigError(Exception):
    pass

