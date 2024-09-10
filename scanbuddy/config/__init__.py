import yaml
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, file):
        self._file = file
        self.parse()

    def parse(self):
        with open(self._file) as fo:
            self._config = yaml.safe_load(fo)
        
    def section(self, name):
        try:
            return self._config[name]
        except KeyError:
            raise ConfigError(f'section "{name}" not found within config file {self._file}')
       
class ConfigError(Exception):
    pass

