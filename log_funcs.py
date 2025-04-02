import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
from config import LOGS_DIRECTORY

today = datetime.datetime.now().strftime("%d-%m-%Y")
handler = TimedRotatingFileHandler(f"{LOGS_DIRECTORY}log_{today}.log",
                                   when="midnight",
                                   interval=1,
                                   backupCount=7,
                                   encoding="utf-8")
handler.suffix = "%d-%m-%Y.log"
formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s] - %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger("MyLogger")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
