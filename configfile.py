import logging
import os

import redis
import yaml

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG, filename='telegbot.log', filemode='w'
)
logger = logging.getLogger(__name__)

# Set some db vars, getting from the config file


def botBasicConfig(database: redis.client.Redis, config_fname="config.yaml"):
    with open(config_fname, 'r') as config:
        data = yaml.safe_load(config)
        admin_password = data['database']['password']
        if not database.exists('admin_password'):
            database.set('admin_password', admin_password)
        default_admin = data['database']['default_admin']
        database.sadd('admin_users', default_admin[1:])
    # set the route path of project for using as a base for changing folder
    database.set('projectpath', os.getcwd())


def get_token(config_fname="config.yaml", shell_var="Bot_token"):
    try:
        with open(config_fname, 'r') as fobj:
            data = yaml.safe_load(fobj)
        token = data['bot']['bot_token']
        # print(token)
        return token
    except:
        return None


# tkn = get_token(config_fname="config.yaml")
# print(tkn)


def help_msg(config_fname="config.yaml"):
    try:
        with open(config_fname, 'r') as fobj:
            data = yaml.safe_load(fobj)
            return data['bot']['help_message']
    except:
        raise "config file error"


def admin_help_msg(config_fname="config.yaml"):
    try:
        with open(config_fname, 'r') as fobj:
            data = yaml.safe_load(fobj)
            return data['bot']['admin_help_message']
    except:
        raise "config file error"
# help_message = help_msg(config_fname="config.yaml")
# print(help_message)
