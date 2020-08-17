import os
import yaml


class Config:
    config = {}

    def __init__(self):
        with open("config.yaml", 'r') as config_file:
            try:
                self.config = yaml.safe_load(config_file)
            except yaml.YAMLError as e:
                print("Failed to load config: %s" % e)

        self._getFromEnviron('strava_client_id')
        self._getFromEnviron('strava_client_secret')

    def get(self, key):
        return self.config[key]

    def dump(self):
        return self.config

    def _getFromEnviron(self, name: str) -> bool:
        """
        Read a config variable from the environment if set

        :param name: The name of the environment variable to check for. This is
                     expected to be in ALL CAPS for the environment variable,
                     and will be recorded in this name in all lowercase within
                     this class

        :return True if an environment variable with the given name was found,
                False otherwise
        """
        if (os.environ[name.upper()]):
            self.config[name.lower()] = os.environ[name.upper()]
            return True

        return False
