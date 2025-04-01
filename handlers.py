from buttons import get_main_menu, get_checkbox_menu, user_choices_toggle_practice
import os
import json
import funcs as f
from config import TG_GROUP_ID, AVAIL_PRACTICES, POLL_FILE
from log_funcs import logger

# Загружаем сохраненные опросы из файла
def load_polls_from_file(poll_file):
    if os.path.exists(poll_file):
        try:
            with open(poll_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:  # pylint: disable=broad-except
            logger.error(e)
            return {}
    return {}  # Если файла нет, возвращаем пустой словарь


# Сохраняем опросы в файл
def save_polls_to_file(polls, poll_file):
    with open(poll_file, "w", encoding="utf-8") as file:
        json.dump(polls, file, indent=4, ensure_ascii=False)


def register_handlers(bot):
    @bot.message_handler(commands=["start"])
    def start_message(message):
        if message.chat.type != "private":
            bot.delete_message(message.chat.id, message.message_id)
            return
        try:
            bot.send_message(message.chat.id, f"Выберите действие", reply_markup=get_main_menu(message.from_user.id))
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:  # pylint: disable=broad-except
            logger.error(e)
            bot.send_message(message.chat.id, f"Произошла ошибка {e.__class__.__name__}")
            bot.delete_message(message.chat.id, message.message_id)

    @bot.message_handler(commands=["help"])
    def show_help(message):
        if message.chat.type != "private":
            logger.info(f"not private chat_id={message.chat.id}")
            bot.delete_message(message.chat.id, message.message_id)
            return
        bot.send_message(message.chat.id, f"Это бот-помощник саратовского клуба кендо Хаябуса")
        bot.delete_message(message.chat.id, message.message_id)

    @bot.callback_query_handler(
        func=lambda call: call.data == "schedule" or call.data == "show_schedule" or call.data == "help" or call.data == "show_next_practice")
    def callback_handler(call):
        chat_id = call.message.chat.id
        if call.data == "schedule":
            user_choices_toggle_practice[chat_id] = set()
            markup = get_checkbox_menu(chat_id, AVAIL_PRACTICES, user_choices_toggle_practice, "toggle_practice_", "save_schedule")
            bot.send_message(chat_id, "Выберите тренировки", reply_markup=markup)
            bot.delete_message(chat_id, call.message.message_id)
        elif call.data == "show_schedule":
            bot.send_message(chat_id, f"Расписание тренировок: {f.get_schedule()}")
            bot.delete_message(chat_id, call.message.message_id)
        elif call.data == "help":
            bot.delete_message(chat_id, call.message.message_id)
        elif call.data == "show_next_practice":
            bot.send_message(chat_id, f"Следующая тренировка: {f.get_next_practice()}")
            bot.delete_message(chat_id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "create_poll")
    def callback_handler_create_poll(call):
        # Создание опроса
        next_practice= f.get_next_practice()
        question = f"{next_practice} кто?"
        options = ["Я", "Не я"]
        if f.poll_already_exists(polls, question):
            bot.send_message(call.message.chat.id, "Опрос уже создан")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return

        f.create_poll(bot, TG_GROUP_ID, question, options, polls)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_practice_"))
    def toggle_practice_selection(call):
        #print(f"toggle_practice_selection {call}")
        chat_id = call.message.chat.id
        option = call.data.replace("toggle_practice_", "")

        if chat_id not in user_choices_toggle_practice:
            user_choices_toggle_practice[chat_id] = set()

        if option in user_choices_toggle_practice[chat_id]:
            user_choices_toggle_practice[chat_id].remove(option)
        else:
            user_choices_toggle_practice[chat_id].add(option)

        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_checkbox_menu(chat_id, AVAIL_PRACTICES, user_choices_toggle_practice, "toggle_practice_", "save_schedule"))

    @bot.callback_query_handler(func=lambda call: call.data == "save_schedule")
    def save_schedule(call):
        #print(f"save_schedule {call}")
        chat_id = call.message.chat.id

        selected_items = ", ".join(user_choices_toggle_practice.get(chat_id, [])) or "ничего не выбрано"
        # Удаляем сообщение с меню
        f.set_schedule(user_choices_toggle_practice.get(chat_id, []))
        bot.delete_message(chat_id, call.message.message_id)

        bot.send_message(chat_id, f"Вы выбрали {selected_items}, данные успешно сохранены")
        del user_choices_toggle_practice[chat_id]

    @bot.poll_answer_handler()
    def handle_poll_vote(poll_answer):
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id

        # Проверяем, отслеживаем ли мы этот опрос
        if poll_id not in polls:
            return

        # Если список проголосовавших еще не создан, создаем его
        if "users" not in polls[poll_id]:
            polls[poll_id]["users"] = []

        # Если пользователь выбрал 1-й пункт (индекс 0)
        if 0 in poll_answer.option_ids:
            chat_id = polls[poll_id]["chat_id"]

            # Добавляем пользователя в список проголосовавших
            if user_id not in polls[poll_id]["users"]:
                polls[poll_id]["users"].append(user_id)
        else:
            # Пользователь убрал голос -> удаляем его из списка
            if user_id in polls[poll_id]["users"]:
                polls[poll_id]["users"].remove(user_id)
        save_polls_to_file(polls, POLL_FILE)

polls = load_polls_from_file(POLL_FILE)