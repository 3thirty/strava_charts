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

        if (os.environ['STRAVA_CLIENT_ID']):
            self.config['strava_client_id'] = os.environ['STRAVA_CLIENT_ID']

        if (os.environ['STRAVA_CLIENT_SECRET']):
            self.config['strava_client_secret'] = os.environ['STRAVA_CLIENT_SECRET']

    def get(self, key):
        return self.config[key]

    def dump(self):
        return self.config
