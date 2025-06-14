import os
import yaml


class Config:
    config = {}

    def __init__(self):
        cwd = os.path.dirname(os.path.abspath(__file__))

        with open(cwd + "/config.yaml", 'r') as config_file:
            try:
                self.config = yaml.safe_load(config_file)
            except yaml.YAMLError as e:
                print("Failed to load config: %s" % e)

    def get(self, key, default=None):
        ret = self.config.get(key, default)

        if isinstance(ret, str) and ret.startswith('[ENV]'):
            ret = self._getFromEnviron(ret.strip('[ENV]'))

        return ret

    def dump(self):
        return self.config

    def _getFromEnviron(self, name: str) -> str:
        """
        Read a config variable from the environment if set

        :param name: The name of the environment variable to check for. This is
                     expected to be in ALL CAPS for the environment variable

        :return String the value of the value from environment variable, empty
                string if not found or not set
        """
        if (os.environ[name.upper()]):
            return os.environ[name.upper()]

        return ''
