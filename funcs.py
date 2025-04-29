import telebot
import json
import datetime
import time
import os

from handlers import register_handlers, save_polls_to_file
from config import WEEK_ORDER, POLL_FILE, TG_GROUP_ID, TIME_FOR_POLL_HOURS, TIME_FOR_POLL_DAYS, SCHEDULE_FILE, \
    CANCELLED_PRACTICES_FILE
from log_funcs import logger
from handlers import polls

def add_menu(bot):
    bot.set_my_commands([
        telebot.types.BotCommand("start", "Старт"),
        telebot.types.BotCommand("help", "Помощь")
    ], scope=telebot.types.BotCommandScopeAllPrivateChats())


def init_bot(bot):
    register_handlers(bot)
    add_menu(bot)


def get_schedule():
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as schedule_file:
        schedule = json.load(schedule_file)
    sorted_schedule = sorted(schedule.items(),
                             key=lambda item: WEEK_ORDER.index(item[0]) if item[0] in WEEK_ORDER else len(WEEK_ORDER))
    return ", ".join(f"{key} {value}" for key, value in sorted_schedule)


def set_schedule(selected_items):
    schedule = {}
    for item in selected_items:
        day, time = item.split(" ", 1)
        schedule[day] = time

    with open(SCHEDULE_FILE, "w", encoding="utf-8") as schedule_file:
        json.dump(schedule, schedule_file)

def get_new_poll_data(practice_date_time):
    return {"question": f"{format_practice_datetime(practice_date_time)} кто?", "options": ['Я', 'Не я']}


def poll_already_exists(polls, question):
    """Проверяет, был ли уже создан опрос с таким вопросом в данном чате."""
    for poll in polls.values():
        if poll["question"].startswith(question):
            logger.debug(f"Poll already exists: {poll['question']}, question: {question}")
            return True  # Найден такой же опрос
    return False  # Опрос с таким вопросом не найден


def create_poll(bot, chat_id, question, options, polls, author=None):
    poll_msg = bot.send_poll(
        chat_id=chat_id,  # ID чата (группы)
        question=question,  # Вопрос
        options=options,  # Варианты ответов
        is_anonymous=False,  # Не анонимный опрос
        type="regular",  # Тип опроса: обычный (можно выбрать несколько) или quiz (один вариант)
    )
    logger.info(f"Poll created: {poll_msg.poll.id}, question: {question} author: {author}")
    # Добавляем опрос в структуру и сохраняем в файл
    add_poll(polls, poll_msg.poll.id, chat_id, poll_msg.message_id, question, [])


def get_next_practice():
    practices = get_next_practices(1)
    if practices:
        return practices[0]
    return None

def get_next_practices(count=1):
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as schedule_file:
        schedule = json.load(schedule_file)

    cancelled = []
    if os.path.exists(CANCELLED_PRACTICES_FILE):
        with open(CANCELLED_PRACTICES_FILE, "r", encoding="utf-8") as file:
            cancelled = json.load(file)

    today = datetime.date.today()
    now_time = datetime.datetime.now().time()
    weekday_today = today.weekday()

    practices = []
    days_checked = 0

    while len(practices) < count and days_checked < 14:
        check_day = (weekday_today + days_checked) % 7
        day_name = WEEK_ORDER[check_day]

        if day_name in schedule:
            training_time = datetime.datetime.strptime(schedule[day_name], "%H:%M").time()
            training_date = today + datetime.timedelta(days=days_checked)

            # Пропускаем сегодняшние прошедшие тренировки
            if days_checked == 0 and now_time > training_time:
                days_checked += 1
                continue

            training_datetime = datetime.datetime.combine(training_date, training_time)
            if training_datetime.isoformat() in cancelled:
                days_checked += 1
                continue

            practices.append(training_datetime)

        days_checked += 1

    return practices


def cancel_practice(practice_iso):
    if os.path.exists(CANCELLED_PRACTICES_FILE):
        with open(CANCELLED_PRACTICES_FILE, "r", encoding="utf-8") as file:
            cancelled = json.load(file)
    else:
        cancelled = []

    if practice_iso not in cancelled:
        cancelled.append(practice_iso)

        with open(CANCELLED_PRACTICES_FILE, "w", encoding="utf-8") as file:
            json.dump(cancelled, file, ensure_ascii=False, indent=2)

def format_practice_datetime(training_datetime):
    """Форматирует дату и время тренировки в строку."""
    if not training_datetime:
        return "Тренировки не запланированы"

    weekday = WEEK_ORDER[training_datetime.weekday()]  # День недели в коротком формате
    return f"{weekday} {training_datetime.strftime('%d.%m')} в {training_datetime.strftime('%H:%M')}"



def add_poll(polls, poll_id, chat_id, message_id, question, users):
    """Добавляет опрос в структуру polls и сохраняет в файл."""
    polls[poll_id] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "question": question,
        "users": users
    }
    save_polls_to_file(polls, POLL_FILE)  # Сохраняем обновленные данные

def schedule_poll(bot):
    """Запускает фоновый процесс, который ждет 17:00 дня перед тренировкой и создает опрос."""
    while True:
        next_practice = get_next_practice()  # Дата следующей тренировки
        logger.debug(f"Next practice: {next_practice}")
        if not next_practice:
            logger.debug(f"no next practice")
            time.sleep(3600)  # Ждем 1 час, если нет тренировки
            continue

        # Определяем время 17:00 за день до тренировки
        scheduled_time = next_practice - datetime.timedelta(days=TIME_FOR_POLL_DAYS, hours=next_practice.hour - TIME_FOR_POLL_HOURS, minutes=next_practice.minute)
        logger.debug(f"scheduled_time = {scheduled_time.strftime('%d.%m %a в %H:%M')}")

        # Текущее время
        now = datetime.datetime.now()

        # Если время уже прошло, переходим к следующей тренировке
        if now < scheduled_time:
            sleep_time = (scheduled_time - now).total_seconds()
            logger.debug(f"now ({now.strftime('%d.%m %a в %H:%M')}) < scheduled_time, time_sleep = {sleep_time}")
            time.sleep(sleep_time)
            continue

        # Создаем опрос
        new_poll_data = get_new_poll_data(next_practice)

        if not poll_already_exists(polls, new_poll_data["question"]):
            create_poll(bot, TG_GROUP_ID, new_poll_data["question"], new_poll_data["options"], polls, "schedule_poll")
        else:
            logger.info(f"Poll already exists: {new_poll_data['question']}")


        # Ждем 1 час перед повторной проверкой
        time.sleep(3600)