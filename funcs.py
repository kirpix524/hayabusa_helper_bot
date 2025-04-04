import telebot
import json
import datetime
import time

from handlers import register_handlers, save_polls_to_file
from config import WEEK_ORDER, POLL_FILE, TG_GROUP_ID
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
    with open("schedule.json", "r", encoding="utf-8") as schedule_file:
        schedule = json.load(schedule_file)
    sorted_schedule = sorted(schedule.items(),
                             key=lambda item: WEEK_ORDER.index(item[0]) if item[0] in WEEK_ORDER else len(WEEK_ORDER))
    return ", ".join(f"{key} {value}" for key, value in sorted_schedule)


def set_schedule(selected_items):
    #print(f"set_schedule {selected_items}")
    schedule = {}
    for item in selected_items:
        day, time = item.split(" ", 1)
        schedule[day] = time

    with open("schedule.json", "w", encoding="utf-8") as schedule_file:
        json.dump(schedule, schedule_file)

def get_new_poll_data(practice_date_time):
    return {"question": f"{format_practice_datetime(practice_date_time)} кто?", "options": ["Я", "Не я"]}


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
    with open("schedule.json", "r", encoding="utf-8") as schedule_file:
        schedule = json.load(schedule_file)

    today = datetime.date.today()  # Сегодняшняя дата
    weekday_today = today.weekday()  # Номер дня недели (0 = Понедельник, 6 = Воскресенье)

    # Перебираем дни недели по расписанию
    for i in range(7):
        check_day = (weekday_today + i) % 7  # Определяем номер дня, который проверяем
        day_name = WEEK_ORDER[check_day]  # Получаем название дня

        if day_name in schedule:
            training_time = schedule[day_name]
            training_datetime = datetime.datetime.strptime(training_time, "%H:%M").time()
            training_date = today + datetime.timedelta(days=i)

            # Если тренировка сегодня, проверяем текущее время
            if i == 0 and datetime.datetime.now().time() > training_datetime:
                continue  # Пропускаем, если уже прошло

            #formatted = f"{day_name} {training_date.strftime('%d.%m')} в {training_datetime.strftime('%H:%M')}"
            return datetime.datetime.combine(training_date, training_datetime)  # Возвращаем дату и время тренировки

    return None

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
        scheduled_time = next_practice - datetime.timedelta(days=1, hours=next_practice.hour - 17, minutes=next_practice.minute)
        logger.debug(f"scheduled_time = {scheduled_time.strftime("%d.%m %a в %H:%M")}")

        # Текущее время
        now = datetime.datetime.now()

        # Если время уже прошло, переходим к следующей тренировке
        if now < scheduled_time:
            sleep_time = (scheduled_time - now).total_seconds()
            logger.debug(f"now ({now.strftime("%d.%m %a в %H:%M")}) < scheduled_time, time_sleep = {sleep_time}")
            time.sleep(sleep_time)
            continue

        # Создаем опрос
        new_poll_data = get_new_poll_data(next_practice)

        if not poll_already_exists(polls, new_poll_data["question"]):
            create_poll(bot, TG_GROUP_ID, new_poll_data["question"], new_poll_data["options"], polls, "schedule_poll")
        else:
            logger.info(f"Poll already exists: {new_poll_data["question"]}")


        # Ждем 1 час перед повторной проверкой
        time.sleep(3600)