import commands
import logging

import telegram
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

import configfile

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='./telegbot.log',
                             format=LOG_FORMAT,
                             filemode='w',
                             level=logging.DEBUG)

logger = logging.getLogger(__name__)

token = configfile.get_token(config_fname="config.yaml")
updates = Updater(token)

redis_db = commands.database.redis_obj
configfile.botBasicConfig(redis_db, config_fname="config.yaml")

logger.info("adding dispatchers")

# document receiver
document_handler = MessageHandler(Filters.document,
                                  commands.getdoc)
keyboard_handler = MessageHandler(Filters.text,
                                  commands.keyboard_press)
updates.dispatcher.add_handler(document_handler)
updates.dispatcher.add_handler(keyboard_handler)

# adding command handlers
updates.dispatcher.add_handler(CommandHandler("start", commands.start))
updates.dispatcher.add_handler(CommandHandler("help", commands.help))
updates.dispatcher.add_handler(CommandHandler(
    "addbutton", commands.addButton, pass_args=True))
updates.dispatcher.add_handler(CommandHandler(
    "delbutton", commands.delButton, pass_args=True))
updates.dispatcher.add_handler(CommandHandler(
    "login", commands.login, pass_args=True))
updates.dispatcher.add_handler(CommandHandler(
    "logout", commands.logout))
updates.dispatcher.add_handler(CommandHandler(
    "setpass", commands.set_password, pass_args=True))
updates.dispatcher.add_handler(CommandHandler(
    "addadmin", commands.addAdmin, pass_args=True))
updates.dispatcher.add_handler(CommandHandler(
    "deladmin", commands.deleteAdmin, pass_args=True))
updates.dispatcher.add_handler(CommandHandler(
    "admins", commands.listAdmin))
updates.dispatcher.add_handler(CommandHandler(
    "buttons", commands.listButton))


logger.info("all commands configured")


updates.start_polling()
updates.idle()
