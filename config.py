import json
import os
from dotenv import load_dotenv

def load_config():
    #Загружаем конфиг из файла
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    load_dotenv(".env")
    config["tg_api_key"] = os.getenv("HAYA_TG_API_KEY")
    config["debug_tg_api_key"] = os.getenv("TEST_BOT_API_KEY")
    return config



config = load_config()
TG_API_KEY = config["tg_api_key"]
TG_GROUP_ID = config["tg_group_id"]
ADMINS = config["admins"]
AVAIL_PRACTICES = config["avail_practices"]
WEEK_ORDER = config["week_order"]
LOGS_DIRECTORY = config["logs_directory"]
POLL_FILE = config["polls_file"]
TIME_FOR_POLL_DAYS = int(config["time_for_poll_days"])
TIME_FOR_POLL_HOURS = int(config["time_for_poll_hours"])
SCHEDULE_FILE = config["schedule_file"]
CANCELLED_PRACTICES_FILE = config["cancelled_practices_file"]
debug_mode = config["debug_mode"]
if debug_mode==1:
    TG_API_KEY = config["debug_tg_api_key"]
    LOGS_DIRECTORY = config["logs_directory_deb"]
    POLL_FILE = config["polls_file_deb"]
    TG_GROUP_ID = config["tg_group_id_deb"]
    TIME_FOR_POLL_HOURS = int(config["time_for_poll_hours_deb"])
    CANCELLED_PRACTICES_FILE = config["cancelled_practices_file_deb"]
