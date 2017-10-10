import db
import redis
import logging
import configfile
import telegram

# adding a logger to monitor crashes and easier debugging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='./telegbot.log',
                    format=LOG_FORMAT,
                    filemode='w',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


# init redis database
database = db.MyDB('localhost', 6379, db=1)


def start(bot: telegram.bot.Bot, update: telegram.update.Update):
    rd = database.redis_obj
    rd.incr("user_count")

    update.message.reply_text('خوش آمدید!')
    logger.info("start command used by {} "
                .format(update.message.from_user.first_name))
    logger.debug("new user << {} >>started the bot"
                 .format(update.message.from_user))


def help(bot: telegram.bot.Bot, update: telegram.update.Update):
    message = configfile.help_msg(config_fname="config.yaml")
    update.message.reply_text(message)


def addButton(bot: telegram.bot.Bot, update: telegram.update.Update, arg):
    button = arg[0]
    rd = database.redis_obj
    if rd.sismember('admin_users', update.message.from_user):
        rd.sadd('buttons', button)
    else:
        update.message("Login First! only admins can add buttons")


def delButton(bot: telegram.bot.Bot, update: telegram.update.Update, arg):
    button = arg[0]
    rd = database.redis_obj
    if rd.sismember('admin_users', update.message.from_user):
        try:
            rd.srem('buttons', button)
        except:
            print("this button doesn't exist")
    else:
        update.message.reply_text("Login First!only admins can delete buttons")


def addAdmin(bot: telegram.bot.Bot, update: telegram.update.Update, arg):
    admin_name = arg[0]
    current_admin_uid = update.effective_user.id
    current_admin_username = update.effective_user.username
    rd = database.redis_obj
    if rd.sismember('admin_users', current_admin_uid):
        try:
            logger.warning("{current_admin_username} tried to add a new admin")
            rd.sadd('admin_users', admin_name)
            update.message.reply_text("User {admin_name} added successfully")
            logger.warn("User {admin_name} was added successfully")
        except Exception as e:
            raise Exception


def login(bot, update: telegram.update.Update, arg):
    password = arg[0]
    rd = database.redis_obj
    if password == rd.get("admin_password"):
        # form_user should be user id
        rd.sadd("loginusers", update.message.from_user)
        update.message.reply_text("Login successful")
    else:
        update.message.reply_text("Login Failure.\
                                  wrong password or you're already logged in")


def senddoc(bot: telegram.bot.Bot, update: telegram.update.Update):
    # TODO: get docs from the user and store them in db
    pass


def set_password(bot, update: telegram.update.Update, arg):
    rd = database.redis_obj
    password = arg[0]
    if rd.sismember("admin_users", update.message.chat.id):
        rd.set("admin_password", password)
