import db
import redis
import logging
import configfile
from telegram.update import Message

# adding a logger to monitor crashes and easier debugging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='./telegbot.log',
                    format=LOG_FORMAT,
                    filemode='w',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


def start(bot, update):
    rd = db.redis_obj
    rd.incr("numOfUsers")

    update.message.reply_text('خوش آمدید!')
    logger.info("start command used by {} "
                .format(update.message.from_user.first_name))
    logger.debug("new user << {} >>started the bot"
                 .format(update.message.from_user))


def help(bot, update):
    message = configfile.help_msg(config_fname="config.yaml")
    update.message.reply_text(message)


def addButton(bot, update, arg):
    button = arg[0]
    rd = redis.Redis()
    rd.sadd('buttons', button)
