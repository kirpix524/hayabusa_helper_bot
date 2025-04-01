import telebot
from funcs import init_bot
from config import TG_API_KEY
from log_funcs import logger

bot=telebot.TeleBot(TG_API_KEY)
init_bot(bot)


#print("bot is running")
logger.info("bot is running")
bot.polling()