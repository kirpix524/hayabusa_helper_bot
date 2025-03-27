
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS

user_choices_toggle_practice = {}

def get_main_menu(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Показать расписание тренировок", callback_data="show_schedule"))
    keyboard.add(InlineKeyboardButton("Когда следующая тренировка", callback_data="show_next_practice"))
    if user_id in ADMINS:
        keyboard.add(InlineKeyboardButton("Задать расписание тренировок", callback_data="schedule"))
        keyboard.add(InlineKeyboardButton("Создать опрос в группе", callback_data="create_poll"))
    return keyboard

def get_checkbox_menu(chat_id, options, user_choices, callback_prefix, save_btn_callback):
    #print(f"get_checkbox_menu {user_id}")
    selected = user_choices.get(chat_id, set())
    print(f"selected = {selected}")
    markup = InlineKeyboardMarkup()
    for option in options:
        checked="✅" if option in selected else "⬜"
        markup.add(InlineKeyboardButton(f"{checked} {option}", callback_data=f"{callback_prefix}{option}"))
    markup.add(InlineKeyboardButton("Сохранить", callback_data=save_btn_callback))
    print(f"markup = {markup}")
    return markup