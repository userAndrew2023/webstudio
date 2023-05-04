import enum
import threading

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData

from config import TOKEN
import datetime
import time
import sqlite3 as sl

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

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
    def __init__(self, url, title, time_pref, sort, user_id):
        self.url = url
        self.title = title
        self.time_pref = time_pref
        self.sort = sort
        self.user_id = user_id


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


@dp.message_handler(lambda message: message.text == "📱Контакты")
async def contacts(message: types.Message):
    await message.reply("Контакты: \nперечисление")


@dp.message_handler(lambda message: message.text == "😎Аккаунт")
async def account(message: types.Message):
    await message.reply(f"ID: {message.from_user.id}\nАктивных задач: {len(tasks[message.from_user['username']])}")


delete_callback = CallbackData("delete", "id")


@dp.message_handler(lambda message: message.text == "Удалить задачу")
async def create_task(message: types.Message):
    try:
        for id, i in enumerate(tasks[message.from_user['username']]):
            builder = types.InlineKeyboardButton("Удалить эту задачу: ", callback_data=delete_callback.new(id=id))
            await message.reply("*URL: *" + i.task.url + "\n"
                                + "*Название: *" + i.task.title + "\n"
                                + "*Время обновления: *" + i.task.time_pref + "\n"
                                + "*Сортировка: *" + i.task.sort, parse_mode="Markdown",
                                reply_markup=types.InlineKeyboardMarkup().add(builder))
    except KeyError:
        await message.reply("Нет текущих задач")


@dp.callback_query_handler(delete_callback.filter())
async def delete_message(query: types.CallbackQuery, callback_data: dict):
    id = callback_data["id"]
    try:
        threading.Thread(target=tasks[query.from_user['username']][int(id)].stop_tracking).start()
        del tasks[query.from_user['username']][int(id)]
        await query.answer("Успешно")
    except Exception:
        await query.answer("Ошибка!")


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
            tasks[username].append(
                Tracking(Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort,
                              message.from_user.id)))
        except KeyError:
            tasks[username] = [
                Tracking(Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort,
                              message.from_user.id))]
        th = threading.Thread(target=tasks[username][-1].start_tracking)
        th.start()
    elif message.text == SortedPrice.EXPENSIVE and current_user.time_pref is not None:
        current_user.sort = SortedPrice.EXPENSIVE
        await message.reply("Задача создана", reply_markup=keyboard)
        try:
            tasks[username].append(
                Tracking(Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort,
                              message.from_user.id)))
        except KeyError:
            tasks[username] = [
                Tracking(Task(current_user.url, current_user.title, current_user.time_pref, current_user.sort,
                              message.from_user.id))]
        th = threading.Thread(target=tasks[username][-1].start_tracking)
        th.start()


### TRACKING SERVICE


def recursive_space(param):
    if param[0] == " ":
        param = param[1:]
        return recursive_space(param)
    else:
        return param


class Tracking:
    service = Service(executable_path="chromedriver.exe")

    def __init__(self, task: Task):
        self.task = task
        self.products = list()

    def track(self, first_launch=False):
        try:
            self.products = []
            driver = webdriver.Chrome()
            driver.get(self.task.url)
            if bool(driver.find_elements(By.CLASS_NAME, "items-extraTitle-JFe8_")):
                elem = driver.find_elements(By.XPATH, "//div[contains(concat(' ', @class, ' '), 'items-items-kAJAg')]")
                list_ = elem[0].text.split("\n")
                list_2 = elem[0].find_elements(By.CLASS_NAME, "iva-item-sliderLink-uLz1v")
                for index, i in enumerate(list_):
                    try:
                        if "₽" in list_[index + 1] and type(
                                int(list_[index + 1].replace("₽", "").replace(" ", ""))) == int:
                            self.products.append(Product(recursive_space(list_[index]), list_[index + 1], list_2[index]))
                    except Exception:
                        pass
            else:
                elem = driver.find_element(By.CLASS_NAME, "styles-module-root-OK422")
                for i in range(3):
                    driver.get(self.task.url + "&p=" + str(i + 1))
                    if bool(driver.find_elements(By.CLASS_NAME, "items-extraTitle-JFe8_")):
                        elem = driver.find_elements(By.XPATH,
                                                    "//div[contains(concat(' ', @class, ' '), 'items-items-kAJAg')]")
                        list_ = elem[0].text.split("\n")
                        list_2 = elem[0].find_elements(By.CLASS_NAME, "iva-item-sliderLink-uLz1v")
                        for index, i in enumerate(list_):
                            try:
                                if "₽" in list_[index + 1] and type(
                                        int(list_[index + 1].replace("₽", "").replace(" ", ""))) == int:
                                    self.products.append(Product(recursive_space(list_[index]), list_[index + 1],
                                                                 list_2[index]))
                            except Exception:
                                pass
            con = sl.connect('database.db')
            if first_launch:
                sql = 'INSERT INTO PRODUCTS (name, price, url, user_id) values (?, ?, ?, ?)'
                data = []
                for i in self.products:
                    data.append((i.title, i.price, i.url, self.task.user_id))
                with con:
                    con.executemany(sql, data)

            else:
                with con:
                    data = list(con.execute(f"SELECT * FROM PRODUCTS WHERE user_id = '{self.task.user_id}'"))
                    data = data[1:]

                ins = 'INSERT INTO PRODUCTS (name, price, url, user_id) values (?, ?, ?, ?)'
                new_data = []
                for i in self.products:
                    new_data.append((i.title, i.price, i.url, self.task.user_id))

                to_ret = [i for i in new_data if i not in data]

                with con:
                    con.execute(f"DELETE FROM PRODUCTS WHERE user_id = '{self.task.user_id}")

                with con:
                    con.executemany(ins, data)
                return to_ret
            con.close()
            driver.quit()
        except Exception:
            self.track(first_launch=first_launch)
            print("SSSS")

    def check_task_in_db(self):
        con = sl.connect("database.db")

        sql = f"SELECT * FROM tasks WHERE " \
              f"(url = {self.task.url}) AND (user_id = {self.task.user_id}) AND (title = {self.task.title})"
        data = con.execute(sql)

        con.close()

        if len(list(data)) == 0:
            return False
        return True

    def start_tracking(self):
        self.track(first_launch=True)

        con = sl.connect('database.db')
        con.executemany("INSERT INTO TASKS (title, url, user_id) values (?, ?, ?)", [(self.task.title, self.task.url,
                                                                                      self.task.user_id)])

        con = sl.connect('database.db')
        sql = "INSERT INTO tasks (url, title, time_pref, sort, user_id) VALUES (?, ?, ?, ?, ?)"

        task = self.task
        data = [
            (task.url, task.title, task.time_pref, task.sort, task.user_id)
        ]

        con.executemany(sql, data)

        con.close()

        if self.task.time_pref == TimePreferences.NOW:
            while True:

                if not self.check_task_in_db():
                    break

                track = self.track()
                if type(track) == list:
                    for i in track:
                        bot.send_message(i[-1], f"Появилось новое объявление\nНазвание: {i[0]}\nЦена: {i[1]}\nCсылка:{i[2]}")
                time.sleep(60 * 15)
        elif self.task.time_pref == TimePreferences.EVENING:
            while self.active:

                if not self.check_task_in_db():
                    break

                current_time = datetime.time()
                if current_time.hour == 19 and current_time.minute == 0:
                    count = 1
                    track = self.track()
                    if type(track) == list:
                        for i in track:
                            bot.send_message(i[-1], f"Появилось новое объявление\nНазвание: {i[0]}\nЦена: {i[1]}\nCсылка:{i[2]}")
                    time.sleep(86400)

        elif self.task.time_pref == TimePreferences.MORNING:
            while self.active:

                if not self.check_task_in_db():
                    break

                current_time = datetime.time()
                if current_time.hour == 9 and current_time.minute == 0:
                    track = self.track()
                    if type(track) == list:
                        for i in track:
                            bot.send_message(i[-1], f"Появилось новое объявление\nНазвание: {i[0]}\nЦена: {i[1]}\nCсылка:{i[2]}")
                    time.sleep(86400)
        elif self.task.time_pref == TimePreferences.ONCE_A_WEEK:
            while self.active:

                if not self.check_task_in_db():
                    break

                track = self.track()
                if type(track) == list:
                    for i in track:
                        bot.send_message(i[-1], f"Появилось новое объявление\nНазвание: {i[0]}\nЦена: {i[1]}\nCсылка:{i[2]}")
                time.sleep(604800)


def grouper(iterable, n):
    args = [iter(iterable)] * n
    return zip(*args)


class Product:
    def __init__(self, title, price, url):
        self.title = title
        self.price = price
        self.url = url

    def __str__(self):
        return self.title + " " + self.price


async def send_message(chat_id, message):
    await bot.send_message(chat_id, message)


### STARTING BOT


if __name__ == "__main__":
    executor.start_polling(dp)
