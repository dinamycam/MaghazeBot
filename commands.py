import db
import os
import redis
import logging
import configfile
import telegram
from telegram.error import NetworkError, Unauthorized
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
                 .format(update.effective_user.username))
    # add all regular users to the database
    rd.hset("users_hash", key=update.effective_user.username,
            value=update.message.chat_id)
    rd.set("users_set", update.message.from_user)

    # show keyboard
    buttons_in_db = list(rd.smembers('buttons'))
    buttons_in_db = telegramhelper.utf_decode(rd.smembers('buttons'))
    keyboard_buttons = telegramhelper.regularButtonsMenu(buttons_in_db,
                                                         n_cols=3)
    reply_keyboard = telegram.ReplyKeyboardMarkup(keyboard_buttons)
    bot.send_message(chat_id=update.message.chat_id,
                     reply_markup=reply_keyboard)


def help(bot: telegram.bot.Bot, update: telegram.update.Update):
    message = configfile.help_msg(config_fname="config.yaml")
    update.message.reply_text(message)


def addButton(bot: telegram.bot.Bot,
              update: telegram.update.Update, args):
    button = args[0]
    filename = args[1]
    rd = database.redis_obj
    current_user = update.effective_user.username
    isadmin = rd.sismember('admin_users', current_user)
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isadmin and isloggedin:
        rd.sadd('buttons', button)
        rd.hset('buttons_hash', button, filename)
        buttons_in_db = telegramhelper.utf_decode(rd.smembers('buttons'))
        keyboard_buttons = telegramhelper.regularButtonsMenu(buttons_in_db,
                                                             n_cols=3)
        reply_keyboard = telegram.ReplyKeyboardMarkup(keyboard_buttons)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Button added. now send the file:",
                         reply_markup=reply_keyboard)
    else:
        update.message.reply_text("Login First! only admins can add buttons")


def getdoc(bot: telegram.Bot,
           update: telegram.Update):
    rd = database.redis_obj
    current_user = update.effective_user.username
    isadmin = rd.sismember('admin_users', current_user)
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isadmin and isloggedin:
        # update.message.reply_text("got it! now going for the database")
        docid = update.message.document.file_id
        # store original filename
        doc_name = update.message.document.file_name
        document = bot.get_file(docid)
        # chanding to the data directory
        os.chdir("./data")
        doc_file = open(os.path.join(os.getcwd(), doc_name), mode='wb')
        # returning to the original dir
        os.chdir("..")
        document.download(out=doc_file)
        update.message.reply_text("Ok I got it.")
    else:
        update.message.reply_text("Only admins can send files")


def delButton(bot: telegram.bot.Bot,
              update: telegram.update.Update, args):
    button = args[0]
    rd = database.redis_obj
    current_user = update.effective_user.username
    isadmin = rd.sismember('admin_users', current_user)
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isadmin and isloggedin:
        try:
            rd.srem('buttons', button)
        except:
            print("button {button} doesn't exist".format(button=button))
    else:
        update.message.reply_text("Login First!only admins can delete buttons")


def addAdmin(bot: telegram.bot.Bot,
             update: telegram.update.Update, args):
    admin_name = args[0][1:]
    # current_admin_uid = update.effective_user.id
    current_user = update.effective_user.username
    rd = database.redis_obj
    isadmin = rd.sismember('admin_users', current_user)
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isadmin and isloggedin:
        try:
            # where admins get created
            logger.warning("{current_user} tried to add a new admin")
            rd.sadd('admin_users', admin_name)
            update.message.reply_text("User {} added successfully"
                                      .format(admin_name))
            logger.warn("User {admin_name} was added successfully")
        except Exception as e:
            logger.error("{} failed to ADD an admin: {}"
                         .format(current_user, admin_name))
    else:
        update.message.reply_text("Fuck off, weirdo!")


def deleteAdmin(bot: telegram.Bot,
                update: telegram.Update, args):

    entered_user = args[0][1:]
    current_user = update.effective_user.username
    rd = database.redis_obj
    isadmin = rd.sismember('admin_users', current_user)
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isadmin and isloggedin:
        logger.warning("{current_user} tried to remove an admin"
                       .format(current_user=current_user))
        print("{current_user} tried to remove an admin"
              .format(current_user=current_user))
        try:
            # where admins get created
            stat = rd.srem('admin_users', entered_user)
            if stat == 1:
                update.message.reply_text("User @{} was deleted"
                                          .format(entered_user))
                logger.warn("User {entered_user} was deleted")
            else:
                update.message.reply_text("there was a problem doing that...")
                logger.error("{} failed to REMOVE an admin: {}"
                             .format(current_user, entered_user))
        except Exception as e:
            print(e)


def listAdmin(bot: telegram.bot.Bot,
              update: telegram.update.Update):
    admin = database.get("admin_users")
    update.message.reply_text(str(admin))


def login(bot: telegram.bot.Bot,
          update: telegram.update.Update, args):
    entered_password = str(args[0])
    rd = database.redis_obj
    pssword = rd.get("admin_password").decode("utf-8")
    current_user = update.effective_user.username
    isloggedin = rd.sismember('loggedin_users', current_user)
    if entered_password == pssword:
        # form_user should be user id
        rd.sadd("loggedin_users", update.effective_user.username)
        update.message.reply_text("Login successful")
    elif isloggedin:
        update.message.reply_text("You're already logged in")
    else:
        update.message.reply_text("Login Failure. wrong password")


def logout(bot: telegram.bot.Bot,
           update: telegram.update.Update):
    rd = database.redis_obj
    current_user = update.effective_user.username
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isloggedin:
        rd.srem('loggedin_users', current_user)
        update.message.reply_text("successfully logged out")
    else:
        update.message.reply_text("you weren't logged in. RIP")


def set_password(bot: telegram.bot.Bot,
                 update: telegram.update.Update, args):
    rd = database.redis_obj
    password = args[0]
    current_user = update.effective_user.username
    isloggedin = rd.sismember('loggedin_users', current_user)
    isadmin = rd.sismember('admin_users', current_user)
    if isloggedin and isadmin:
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
        update.message.reply_text("you are not an admin. FUCK OFF")


def setlang(bot: telegram.bot.Bot,
            update: telegram.update.Update,
            args):
    # TODO: Implement this
    pass
