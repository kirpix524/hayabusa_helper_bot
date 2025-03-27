from buttons import get_main_menu, get_checkbox_menu, user_choices_toggle_practice
import funcs as f
from config import TG_GROUP_ID, AVAIL_PRACTICES
from log_funcs import logger


def register_handlers(bot):
    @bot.message_handler(commands=["start"])
    def start_message(message):
        if message.chat.type != "private":
            bot.delete_message(message.chat.id, message.message_id)
            return
        try:
            bot.send_message(message.chat.id, f"Hello, {message.from_user.first_name}!", reply_markup=get_main_menu(message.from_user.id))
        except Exception as e:  # pylint: disable=broad-except
            logger.error(e)
            bot.send_message(message.chat.id, f"Произошла ошибка {e.__class__.__name__}")

    @bot.message_handler(commands=["help"])
    def show_help(message):
        if message.chat.type != "private":
            bot.delete_message(message.chat.id, message.message_id)
            return
        bot.send_message(message.chat.id, f"Это бот-помощник саратовского клуба кендо Хаябуса")

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
        f.create_poll(bot, TG_GROUP_ID)
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