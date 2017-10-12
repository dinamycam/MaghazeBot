import db
import redis
import logging
import configfile
import telegram
import telegramhelper

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
    logger.debug("new user << {} >> started the bot"
                 .format(update.message.from_user))
    # add all regular users to the database
    rd.hset("users_hash", key=update.message.from_user,
            value=update.message.chat_id)
    rd.set("users_set", update.message.from_user)


def help(bot: telegram.bot.Bot, update: telegram.update.Update):
    message = configfile.help_msg(config_fname="config.yaml")
    update.message.reply_text(message)


def addButton(bot: telegram.bot.Bot,
              update: telegram.update.Update, args):
    button = args[0]
    rd = database.redis_obj
    if rd.sismember('admin_users', update.message.from_user):
        rd.sadd('buttons', button)
        buttons_in_db = rd.get('buttons')
        keyboard_buttons = telegramhelper.regularButtonsMenu(buttons_in_db)
        reply_keyboard = telegram.ReplyKeyboardMarkup([keyboard_buttons])
        # TODO: add a part where the sent document would get saved in db
    else:
        update.message("Login First! only admins can add buttons")


def delButton(bot: telegram.bot.Bot,
              update: telegram.update.Update, args):
    button = args[0]
    rd = database.redis_obj
    if rd.sismember('admin_users', update.message.from_user):
        try:
            rd.srem('buttons', button)
        except:
            print("this button doesn't exist")
    else:
        update.message.reply_text("Login First!only admins can delete buttons")


def addAdmin(bot: telegram.bot.Bot,
             update: telegram.update.Update, args):
    admin_name = args[0]
    # current_admin_uid = update.effective_user.id
    current_admin_username = update.effective_user.username
    rd = database.redis_obj
    if rd.sismember('admin_users', current_admin_username):
        try:
            # where admins get created
            logger.warning("{current_admin_username} tried to add a new admin")
            rd.sadd('admin_users', admin_name)
            update.message.reply_text("User {} added successfully"
                                      .format(admin_name))
            logger.warn("User {admin_name} was added successfully")
        except Exception as e:
            logger.error("{} failed to add an admin: {}"
                         .format(current_admin_username, admin_name))


def login(bot: telegram.bot.Bot,
          update: telegram.update.Update, args):
    entered_password = str(args[0])
    rd = database.redis_obj
    pssword = rd.get("admin_password").decode("utf-8")
    if entered_password == pssword:
        # form_user should be user id
        rd.sadd("loggedin_users", update.message.from_user)
        update.message.reply_text("Login successful")
    else:
        update.message.reply_text("Login Failure." +
                                  "wrong password or you're already logged in")


def set_password(bot: telegram.bot.Bot,
                 update: telegram.update.Update, args):
    rd = database.redis_obj
    password = args[0]
    print(password)
    if rd.sismember("admin_users", update.effective_user.username):
        print(update.message.chat_id)
        stat = rd.set("admin_password", password)
        if stat == 1:
            logger.info("admin password updated successfully")
            update.message.reply_text("admin password updated successfully")
        else:
            logger.warn("Database was not able to change password?!")
            update.message.reply_text("Failed for some reason.try again later")
    else:
        logger.warn("non-admin user: {} tried to add admin!"
                    .format(update.effective_user.username))


def setlang(bot: telegram.bot.Bot,
            update: telegram.update.Update,
            args):
    # TODO: Implement this
    pass
