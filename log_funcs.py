import logging
import datetime
from logging.handlers import TimedRotatingFileHandler

today = datetime.datetime.now().strftime("%d-%m-%Y")
handler = TimedRotatingFileHandler(f"logs/log_{today}.log",
                                   when="midnight",
                                   interval=1,
                                   backupCount=7,
                                   encoding="utf-8")
handler.suffix = "%d-%m-%Y.log"
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger("MyLogger")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.info("logger activated")
