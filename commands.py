import logging
import os

import telegram
from telegram import ReplyKeyboardMarkup
from telegram.error import NetworkError, Unauthorized
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, RegexHandler, Updater)

import configfile
import db
import redis
import telegramhelper

# adding a logger to monitor crashes and easier debugging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='./telegbot.log',
                    format=LOG_FORMAT,
                    filemode='w',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)


# init redis database
database = db.MyDB('localhost', 6379, db=1)
projectpath = database.redis_obj.get('projectpath')
projectpath = projectpath.decode('utf-8')


def start(bot: telegram.bot.Bot, update: telegram.update.Update):
    rd = database.redis_obj
    rd.incr("user_count")

    logger.info("start command used by {} "
                .format(update.message.from_user.first_name))
    logger.debug("new user << {} >> started the bot"
                 .format(update.effective_user.username))
    # add all regular users to the database
    rd.hset("users_hash", key=update.effective_user.username,
            value=update.message.chat_id)
    rd.sadd("users_set", update.effective_user.username)

    # show keyboard
    buttons_in_db = list(rd.smembers('buttons'))
    buttons_in_db = telegramhelper.utf_decode(rd.smembers('buttons'))
    keyboard_buttons = telegramhelper.regularButtonsMenu(buttons_in_db,
                                                         n_cols=3)
    reply_keyboard = telegram.ReplyKeyboardMarkup(keyboard_buttons,
                                                  resize_keyboard=True)
    bot.send_message(chat_id=update.message.chat_id,
                     text="خوش آمدید!",
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
        reply_keyboard = telegram.ReplyKeyboardMarkup(keyboard_buttons,
                                                      resize_keyboard=True)
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
        os.chdir(projectpath)
        os.chdir(os.path.join(projectpath, 'data'))
        doc_file = open(os.path.join(os.getcwd(), doc_name), mode='wb')
        # returning to the original dir
        os.chdir(projectpath)
        document.download(out=doc_file)
        doc_file.close()
        print("Got a file")
        update.message.reply_text("Ok I got it.")
    else:
        update.message.reply_text("Only admins can send files")
        print("Only admins can send files")


def delButton(bot: telegram.bot.Bot,
              update: telegram.update.Update, args):
    button = args[0]
    rd = database.redis_obj
    current_user = update.effective_user.username
    isadmin = rd.sismember('admin_users', current_user)
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isadmin and isloggedin:
        if not rd.sismember('buttons', button):
            update.message.reply_text("{} doesn't exist".format(button))
        # checking if the button got deleted
        elif rd.sismember('buttons', button):
            rd.srem('buttons', button)
            rd.hdel('buttons_hash', button)
            bot.send_message(text="Button deleted successfully",
                             reply_markup=telegramhelper.KeyboardMarkupBuilder(rd),
                             chat_id=update.message.chat_id)
    else:
        update.message.reply_text("Login first! only admins can delete button")


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
    rd = database.redis_obj
    admin = database.get("admin_users")
    admin_str = str(telegramhelper.utf_decode(admin))

    users = rd.scard("users_set")
    user_count = str(users)
    update.message.reply_text(admin_str +
                              "\n And also,The User Count:\n" +
                              user_count)


def listButton(bot: telegram.bot.Bot,
               update: telegram.update.Update):
        rd = database.redis_obj
        buttons_dic = rd.hgetall('buttons_hash')
        buttons_dic = telegramhelper.utf_decode(buttons_dic)
        update.message.reply_text(str(buttons_dic))


def login(bot: telegram.bot.Bot,
          update: telegram.update.Update, args):
    entered_password = str(args[0])
    rd = database.redis_obj
    pssword = rd.get("admin_password").decode("utf-8")
    current_user = update.effective_user.username
    isloggedin = rd.sismember('loggedin_users', current_user)
    if isloggedin:
        update.message.reply_text("You're already logged in")
        update.message.reply_text(configfile.admin_help_msg())
    elif entered_password == pssword:
        # form_user should be user id
        rd.sadd("loggedin_users", update.effective_user.username)
        update.message.reply_text("Login successful")
        update.message.reply_text(configfile.admin_help_msg())
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


def keyboard_press(bot, update):
    button_text = update.message.text
    rd = database.redis_obj
    # print(button_text)

    rd = database.redis_obj
    if rd.sismember('buttons', button_text):
        file_name = rd.hget('buttons_hash', button_text)
        file_name = file_name.decode('utf-8')

        os.chdir(os.path.join(projectpath, 'data'))
        button_text = telegramhelper.docExtractor(file_name, sheet_index=0)
        os.chdir(projectpath)
    bot.send_message(chat_id=update.message.chat_id,
                     text=button_text)


# Functions for handling a conversation about time.

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [['Hour', 'Minute', 'Month', 'Day'],
                  ['Num of Repeats', 'Full Date...'],
                  ['Done']]
stmk = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def data2str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def settime(bot, update):
    update.message.reply_text(
        "set a date and time for sending your message in groups and "
        " chats\n"
        "Complete each section for me...",
        reply_markup=stmk)

    return CHOOSING


def regular_choice(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    update.message.reply_text(
        "The {}? Ok, I'm ready. Enter!".format(text.lower()))

    return TYPING_REPLY


def custom_choice(bot, update):
    update.message.reply_text('Okay. Send the date in correct format'
                              'for example "2017-10-21 02:39:47"')

    return TYPING_CHOICE


def received_information(bot, update, user_data):
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text("What you Already told me:"
                              "{}"
                              "tell me more,"
                              "or change something you have told.".format(
                                  data2str(user_data)), reply_markup=stmk)

    return CHOOSING


def done(bot, update, user_data):
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text("Configuration completed:"
                              "{}"
                              "Until next time :)".format(data2str(user_data)))

    user_data.clear()
    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def setlang(bot: telegram.bot.Bot,
            update: telegram.update.Update,
            args):
    # TODO: Implement this
    pass
