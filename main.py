import telebot
import threading
from funcs import init_bot, schedule_poll
from config import TG_API_KEY
from log_funcs import logger

bot=telebot.TeleBot(TG_API_KEY)
init_bot(bot)
# Запуск в отдельном потоке, чтобы не блокировать работу бота
threading.Thread(target=lambda: schedule_poll(bot), daemon=True).start()

#print("bot is running")
logger.info("bot is running")
bot.infinity_polling(timeout=10, long_polling_timeout=5)