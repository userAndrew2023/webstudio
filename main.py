import enum
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData

from config import TOKEN

bot = Bot(TOKEN)
dp = Dispatcher(bot)


class Actions(enum.Enum):
    ACTION_START = 0
    ACTION_CREATE_TASK = 1
    ACTION_URL_UPLOADED = 2
    ACTION_TITLE_UPLOADED = 3
    ACTION_TASK_CREATED = 4


class User:
    def __init__(self, action):
        self.action = action
        self.url = None
        self.title = None
        self.time_pref = None
        self.sort = None

    def __str__(self):
        return f"{self.action}, {self.url}, {self.title}, {self.time_pref}, {self.sort}"


class Task:
    def __init__(self, url, title, time_pref, sort):
        self.url = url
        self.title = title
        self.time_pref = time_pref
        self.sort = sort


class TimePreferences:
    NOW = "Сразу, когда появится объявление"
    MORNING = "В 9.00"
    EVENING = "В 19.00"
    ONCE_A_WEEK = "Один раз в неделю"


class SortedPrice:
    EXPENSIVE = "Сначала дорогие"
    CHEAP = "Сначала дешевые"


MAX_TASKS = 5

users = {}
tasks = {}


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    button = [
        [types.KeyboardButton(text="Создать задачу")],
        [types.KeyboardButton(text="Удалить задачу")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)
    await message.reply(f"Приветствую, {message.from_user['first_name']}!", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Создать задачу")
async def create_task(message: types.Message):
    markup = types.ReplyKeyboardRemove()
    try:
        if len(tasks[message.from_user['username']]) == MAX_TASKS:
            await message.reply("Нельзя создать больше 5 задач на одного юзера")
        else:
            users[message.from_user['username']] = User(Actions.ACTION_CREATE_TASK)
            await message.reply("Дайте ссылку на страницу с объявлениями Avito", reply_markup=markup)
    except KeyError:
        users[message.from_user['username']] = User(Actions.ACTION_CREATE_TASK)
        await message.reply("Дайте ссылку на страницу с объявлениями Avito", reply_markup=markup)


delete_callback = CallbackData("delete", "id")


@dp.message_handler(lambda message: message.text == "Удалить задачу")
async def create_task(message: types.Message):
    try:
        for id, i in enumerate(tasks[message.from_user['username']]):
            builder = types.InlineKeyboardButton("Удалить эту задачу: ", callback_data=delete_callback.new(id=id))
            await message.reply("*URL: *" + i.url + "\n"
                                + "*Название: *" + i.title + "\n"
                                + "*Время обновления: *" + i.time_pref + "\n"
                                + "*Сортировка: *" + i.sort, parse_mode="Markdown",
                                reply_markup=types.InlineKeyboardMarkup().add(builder))
    except KeyError:
        await message.reply("Нет текущих задач")


@dp.callback_query_handler(delete_callback.filter())
async def delete_message(query: types.CallbackQuery, callback_data: dict):
    id = callback_data["id"]
    try:
        del tasks[query.from_user['username']][int(id)]
        await query.answer("text")
    except IndexError:
        await query.answer("Ошибка!")


@dp.message_handler(lambda message: message.text == "Отмена")
async def del_not_ok(message: types.Message):
    await message.reply("Удаление отменено")


@dp.message_handler(lambda message: message.text == "Частота обновлений")
async def frequency(message: types.Message):
    kb = [
        [types.KeyboardButton(text=TimePreferences.NOW)],
        [types.KeyboardButton(text=TimePreferences.MORNING)],
        [types.KeyboardButton(text=TimePreferences.EVENING)],
        [types.KeyboardButton(text=TimePreferences.ONCE_A_WEEK)]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await message.reply("Укажите настройки новой задачи", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Сортировка")
async def sorting(message: types.Message):
    kb = [
        [types.KeyboardButton(text=SortedPrice.EXPENSIVE)],
        [types.KeyboardButton(text=SortedPrice.CHEAP)]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    await message.reply("Укажите настройки новой задачи", reply_markup=keyboard)


def print_sort():
    kb = [
        [
            types.KeyboardButton(text="Сортировка")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


@dp.message_handler()
async def create_task_message(message: types.Message):
    button = [
        [types.KeyboardButton(text="Создать задачу")],
        [types.KeyboardButton(text="Удалить задачу")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)
    username = message.from_user['username']
    current_user = users[username]
    if current_user.action == Actions.ACTION_CREATE_TASK:
        current_user.url = message.text
        current_user.action = Actions.ACTION_URL_UPLOADED
        await message.reply("Укажите имя новой задачи")
    elif current_user.action == Actions.ACTION_URL_UPLOADED:
        current_user.title = message.text
        current_user.action = Actions.ACTION_TITLE_UPLOADED

        kb = [
            [
                types.KeyboardButton(text="Частота обновлений")
            ]
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True
        )

        await message.reply("Укажите настройки новой задачи", reply_markup=keyboard)
    elif message.text == TimePreferences.NOW:
        current_user.time_pref = TimePreferences.NOW
        await message.reply("Укажите сортировку новой задачи", reply_markup=print_sort())
    elif message.text == TimePreferences.MORNING:
        current_user.time_pref = TimePreferences.MORNING
        await message.reply("Укажите сортировку новой задачи", reply_markup=print_sort())
    elif message.text == TimePreferences.EVENING:
        current_user.time_pref = TimePreferences.EVENING
        await message.reply("Укажите сортировку новой задачи", reply_markup=print_sort())
    elif message.text == TimePreferences.ONCE_A_WEEK:
        current_user.time_pref = TimePreferences.ONCE_A_WEEK
        await message.reply("Укажите сортировку новой задачи", reply_markup=print_sort())
    elif message.text == SortedPrice.CHEAP:
        current_user.sort = SortedPrice.CHEAP
        await message.reply("Задача создана", reply_markup=keyboard)
        try:
            tasks[username] \
                .append(Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort))
        except KeyError:
            tasks[username] = [Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort)]
    elif message.text == SortedPrice.EXPENSIVE:
        current_user.sort = SortedPrice.EXPENSIVE
        await message.reply("Задача создана", reply_markup=keyboard)
        try:
            tasks[username] \
                .append(Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort))
        except KeyError:
            tasks[username] = [Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort)]


if __name__ == "__main__":
    executor.start_polling(dp)
