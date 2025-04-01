import telebot
import json
import datetime
import os

from pyexpat.errors import messages

from handlers import register_handlers, save_polls_to_file
from config import WEEK_ORDER, POLL_FILE
from log_funcs import logger


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
    return ", ".join(f"{key} {value}" for key, value in schedule.items())


def set_schedule(selected_items):
    #print(f"set_schedule {selected_items}")
    schedule = {}
    for item in selected_items:
        day, time = item.split(" ", 1)
        schedule[day] = time

    with open("schedule.json", "w", encoding="utf-8") as schedule_file:
        json.dump(schedule, schedule_file)


def poll_already_exists(polls, question):
    """Проверяет, был ли уже создан опрос с таким вопросом в данном чате."""
    for poll in polls.values():
        if question in poll["question"]:
            return True  # Найден такой же опрос
    return False  # Опрос с таким вопросом не найден


def create_poll(bot, chat_id, question, options, polls):
    poll_msg = bot.send_poll(
        chat_id=chat_id,  # ID чата (группы)
        question=question,  # Вопрос
        options=options,  # Варианты ответов
        is_anonymous=False,  # Не анонимный опрос
        type="regular",  # Тип опроса: обычный (можно выбрать несколько) или quiz (один вариант)
    )

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

            formatted = f"{day_name} {training_date.strftime('%d.%m')} в {training_datetime.strftime('%H:%M')}"
            #datetime.datetime.combine(training_date, training_datetime)  # Возвращаем дату и время тренировки
            return formatted



def add_poll(polls, poll_id, chat_id, message_id, question, users):
    """Добавляет опрос в структуру polls и сохраняет в файл."""
    polls[poll_id] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "question": question,
        "users": users
    }
    save_polls_to_file(polls, POLL_FILE)  # Сохраняем обновленные данные
