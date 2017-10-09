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


# init redis database
database = db.MyDB('localhost', 6379, db=1)


def start(bot, update):
    rd = database.redis_obj
    rd.incr("user_count")

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
    rd = database.redis_obj
    rd.sadd('buttons', button)


def delButton(bot, update, arg):
    button = arg[0]
    rd = database.redis_obj
    try:
        rd.srem('buttons', button)
    except:
        print("this button doesn't exist")


def addAdmin(bot, update, arg):
    admin_name = arg[0]
    rd = database.redis_obj
    if rd.sismember('admin_users', admin_name):
        try:
            rd.sadd('admin_users', admin_name)
        except Exception as e:
            raise Exception


def login(bot, update, arg):
    password = arg[0]
    rd = database.redis_obj
    if password == rd.get("admin_password"):
        # form_user should be user id
        rd.sadd("loginusers", update.message.from_user)
        update.message.reply_text("Login successful")
    else:
        update.message.reply_text("Login Failure.\
                                  wrong password or you're already logged in")


def senddoc(bot, update):
    # TODO: get docs from the user and store them in db
    pass


def set_password(bot, update, arg):
    rd = database.redis_obj
    password = arg[0]
    if rd.sismember("admin_users", update.message.chat_id):
        rd.set("admin_password", password)
