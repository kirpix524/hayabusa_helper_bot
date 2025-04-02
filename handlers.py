from buttons import get_main_menu, get_checkbox_menu, user_choices_toggle_practice
import os
import json
import funcs as f
from config import TG_GROUP_ID, AVAIL_PRACTICES, POLL_FILE
from log_funcs import logger

pending_polls = {}

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
            bot.send_message(message.chat.id, f"Произошла ошибка {str(e)}")
            bot.delete_message(message.chat.id, message.message_id)

    @bot.message_handler(commands=["help"])
    def show_help(message):
        if message.chat.type != "private":
            logger.info(f"not private chat_id={message.chat.id}")
            bot.delete_message(message.chat.id, message.message_id)
            return
        bot.send_message(message.chat.id, f"Это бот-помощник саратовского клуба кендо Хаябуса")
        bot.delete_message(message.chat.id, message.message_id)

    @bot.message_handler(func=lambda message: message.from_user.id in pending_polls)
    def handle_additional_poll_message(message):
        """Обрабатывает дополнительное сообщение перед созданием опроса."""
        user_id = message.from_user.id

        if user_id not in pending_polls:
            return  # Если вдруг пользователя нет в списке, ничего не делаем

        chat_id = pending_polls[user_id]["chat_id"]
        group_id = pending_polls[user_id]["group_id"]
        question = pending_polls[user_id]["question"]
        options = pending_polls[user_id]["options"]
        additional_text = message.text.strip()

        # Если пользователь отправил "-", то доп. сообщение не добавляем
        if additional_text != "-":
            question = f"{question}\n{additional_text}"

        # Создаем опрос
        f.create_poll(bot, group_id, question, options, polls, "handle_additional_poll_message")
        # Убираем пользователя из списка ожидания
        del pending_polls[user_id]

        bot.send_message(chat_id, "Опрос создан!")


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
            bot.send_message(chat_id, f"Следующая тренировка: {f.format_practice_datetime(f.get_next_practice())}")
            bot.delete_message(chat_id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "create_poll")
    def callback_handler_create_poll(call):
        """Запрашивает у пользователя дополнительный текст перед созданием опроса."""
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        # Создание опроса
        next_practice= f.get_next_practice()
        new_poll_data = f.get_new_poll_data(next_practice)
        if f.poll_already_exists(polls, new_poll_data["question"]):
            bot.send_message(call.message.chat.id, "Опрос уже создан")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return

        # Запоминаем, что этот пользователь должен отправить дополнительное сообщение
        pending_polls[user_id] = {"chat_id": chat_id, "group_id": TG_GROUP_ID, "question": new_poll_data["question"], "options": new_poll_data["options"]}

        bot.send_message(chat_id, "Отправьте дополнительное сообщение для опроса или напишите '-' для пропуска.")
        bot.delete_message(chat_id, call.message.message_id)

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
        # logger.debug(f"handle_poll_vote {poll_answer}")
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id

        # Проверяем, отслеживаем ли мы этот опрос
        if poll_id not in polls:
            # logger.debug(f"poll_id {poll_id} not in polls")
            return

        # Если список проголосовавших еще не создан, создаем его
        if "users" not in polls[poll_id]:
            polls[poll_id]["users"] = []

        # Если пользователь выбрал 1-й пункт (индекс 0)
        if 0 in poll_answer.option_ids:
            chat_id = polls[poll_id]["chat_id"]
            # logger.debug(f"0 in poll_answer.option_ids")
            # Добавляем пользователя в список проголосовавших
            if user_id not in polls[poll_id]["users"]:
                polls[poll_id]["users"].append(user_id)
        else:
            # Пользователь убрал голос -> удаляем его из списка
            # logger.debug(f"0 not in poll_answer.option_ids")
            if user_id in polls[poll_id]["users"]:
                polls[poll_id]["users"].remove(user_id)
        save_polls_to_file(polls, POLL_FILE)

    @bot.message_handler(content_types=["delete"])
    def handle_deleted_poll(message):
        """Обработчик удаления опроса"""
        logger.debug(f"handle_deleted_poll {message}")
        if message.content_type == "delete":
            poll_id = message.poll.id if message.poll else None

            if poll_id and poll_id in polls:
                del polls[poll_id]  # Удаляем из структуры
                save_polls_to_file(polls, POLL_FILE)  # Сохраняем обновленный файл
                logger.info(f"Опрос {poll_id} удален из структуры и файла.")

polls = load_polls_from_file(POLL_FILE)
