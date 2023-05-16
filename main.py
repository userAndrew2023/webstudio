import enum
import types
from datetime import timedelta

import pymysql

from selenium import webdriver
from selenium.webdriver.common.by import By
from telebot import *

users = {}


class Sell:
    def __init__(self, name, price, url):
        self.name = name
        self.price = price
        self.url = url

    def __eq__(self, other):
        return self.name == other.name and self.price == other.price and self.url == other.url


class Actions(enum.Enum):
    ACTION_START = 0
    ACTION_CREATE_TASK = 1
    ACTION_URL_UPLOADED = 2
    ACTION_TITLE_UPLOADED = 3
    ACTION_TIME_UPLOADED = 4
    ACTION_SORT_UPLOADED = 5
    ACTION_TASK_DELETE = 6


class User:
    def __init__(self, action, id):
        self.id = id
        self.action = action
        self.url = None
        self.title = None
        self.time_pref = None
        self.sort = None

    def __str__(self):
        return f"{self.action}, {self.url}, {self.title}, {self.time_pref}, {self.sort}"


class TimePreferences:
    NOW = "Сразу, когда появится объявление"
    MORNING = "В 9.00"
    EVENING = "В 19.00"
    ONCE_A_WEEK = "Один раз в неделю"


class SortedPrice:
    EXPENSIVE = "Сначала дорогие"
    CHEAP = "Сначала дешевые"


def get_sales(url):
    try:
        driver = webdriver.Chrome()
        driver.get(url)
        elem2 = driver.find_element(By.XPATH, "//div[@data-marker='catalog-serp']")
        links = driver.find_elements(By.XPATH, "//a[@class='link-link-MbQDP link-design-default-_nSbv title-root-zZCwT "
                                               "iva-item-title-py3i_ title-listRedesign-_rejR "
                                               "title-root_maxHeight-X6PsH']")
        elem = elem2.find_elements(By.CLASS_NAME, "iva-item-body-KLUuy")
        to_list = []
        for index, i in enumerate(elem):
            to_list.append((i.text.split("\n")[0], i.text.split("\n")[1], links[index].get_attribute("href")))
        return to_list
    except Exception:
        return get_sales(url)


bot = TeleBot("5979613690:AAGREX4z-atI5hchjXJZk5jPTeiPF8zlqS4")
con = pymysql.connect(host="sql8.freesqldatabase.com", user="sql8618457", password="2WlpnRqI9a", database="sql8618457")
con.ping()


def main_menu(message):
    buttons = [
        types.KeyboardButton(text="😎 Аккаунт"),
        types.KeyboardButton(text="📱 Контакты"),
        types.KeyboardButton(text="🆕 Создать задачу"),
        types.KeyboardButton(text="🔑 Подписка"),
        types.KeyboardButton(text="❌ Удалить задачу"),
        types.KeyboardButton(text="ℹ Инструкция")
    ]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*buttons, row_width=2)
    bot.send_message(message.chat.id, f"Приветствую, @{message.from_user.username}", reply_markup=markup)


def track(task: User):
    sales = get_sales(task.url)
    if task.time_pref == TimePreferences.NOW:
        while True:
            con.ping()
            with con.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `tasks` WHERE id = '{task.id}'")
                if len(cursor.fetchall()) == 0:
                    break
                con.commit()
            new = get_sales(url=task.url)
            for j in [i for i in new if i not in sales]:
                bot.send_message(task.id, j[0] + " - " + j[1] + " - " + j[2])
            time.sleep(10)
            sales = new
    elif task.time_pref == TimePreferences.MORNING:
        while True:
            con.ping()
            with con.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `tasks` WHERE id = '{task.id}'")
                if len(cursor.fetchall()) == 0:
                    break
                con.commit()
            d = datetime.now()
            if d.hour == 9:
                new = get_sales(url=task.url)
                for j in [i for i in new if i not in sales]:
                    bot.send_message(task.id, j[0] + " - " + j[1] + " - " + j[2])
                    time.sleep(60 * 60 * 24)
                sales = new

    elif task.time_pref == TimePreferences.EVENING:
        while True:
            con.ping()
            with con.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `tasks` WHERE id = '{task.id}'")
                if len(cursor.fetchall()) == 0:
                    break
                con.commit()
            d = datetime.now()
            if d.hour == 19:
                new = get_sales(url=task.url)
                for j in [i for i in new if i not in sales]:
                    bot.send_message(task.id, j[0] + " - " + j[1] + " - " + j[2])
                    time.sleep(60 * 60 * 24)
                sales = new
    elif task.time_pref == TimePreferences.ONCE_A_WEEK:
        while True:
            con.ping()
            with con.cursor() as cursor:
                cursor.execute(f"SELECT * FROM `tasks` WHERE id = '{task.id}'")
                if len(cursor.fetchall()) == 0:
                    break
                con.commit()
            new = get_sales(url=task.url)
            for j in [i for i in new if i not in sales]:
                bot.send_message(task.id, j[0] + " - " + j[1] + " - " + j[2])
                time.sleep(60 * 60 * 24 * 7)
            sales = new


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    main_menu(message)


@bot.message_handler()
def handler(message: types.Message):
    if message.text == "😎 Аккаунт":
        con.ping()
        with con.cursor() as cursor:

            q = f"SELECT * FROM `users` WHERE tg_id = '{message.chat.id}'"
            cursor.execute(q)
            fetchall = cursor.fetchall()
            if len(fetchall) == 0:
                tasks_last = 5
            else:
                tasks_last = 5 - int(fetchall[0][-1])

            bot.send_message(message.chat.id, f"Аккаунт: {message.from_user.id}\nОсталось задач: {tasks_last}")
        con.commit()
    elif message.text == "❌ Удалить задачу":
        kb = [
            types.KeyboardButton("Главное меню")
        ]
        con.ping()
        with con.cursor() as cursor:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            q = f"SELECT * FROM `tasks` WHERE tg_id = '{message.chat.id}'"
            cursor.execute(q)
            fetchall = cursor.fetchall()
            for index, i in enumerate(fetchall):
                markup.add(f"{str(index)}. {i[1]} ({i[0]})")
            markup.add(*kb, row_width=1)
        bot.send_message(message.chat.id, "Выберите из пункта и удалите")
        users[message.chat.id] = Actions.ACTION_TASK_DELETE

    elif message.text == "🆕 Создать задачу":
        kb = [
            types.KeyboardButton("Главное меню")
        ]
        con.ping()
        with con.cursor() as cursor:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(*kb, row_width=1)
            q = f"SELECT * FROM `users` WHERE tg_id = '{message.chat.id}'"
            cursor.execute(q)
            fetchall = cursor.fetchall()
            if len(fetchall) == 0:
                bot.send_message(message.chat.id, "Укажите имя новой задачи", reply_markup=markup)
                users[message.chat.id] = User(action=Actions.ACTION_CREATE_TASK, id=message.chat.id)
            else:
                tasks = int(fetchall[0][-1])
                if tasks == 5:
                    bot.send_message(message.chat.id, "Нельзя создать больше 5 задач")
                else:
                    bot.send_message(message.chat.id, "Укажите имя новой задачи", reply_markup=markup)
                    users[message.chat.id] = User(action=Actions.ACTION_CREATE_TASK, id=message.chat.id)
            con.commit()

    elif message.text == "📱 Контакты":
        bot.send_message(message.chat.id, """Техническая поддержка Dobby.Avito:\n+7 800 777-08-35\ninfo@dobby.plus""")
    elif message.text == "ℹ Инструкция":
        bot.send_message(message.chat.id, text=""" Инструкция: 
                
➕ Чтобы создать задачу, нажмите кнопку «Создать задачу». 
Задайте URL, название и другие параметры.

❌ Чтобы удалить задачу, нажмите кнопку «Удалить задачу». 
Выберите из списка и удалите.

✅  Чтобы просмотреть задачи, нажмите кнопку «Мои задачи»

ℹ️ Чтобы просмотреть информацию об аккаунте, нажмите кнопку «Аккаунт»

🌎 Чтобы просмотреть контактную информацию, нажмите кнопку «Контакты»

🔑 Чтобы посмотреть срок действия подписки нажмите кнопку «Подписка»

По улучшению бота Dobby.Avito пишите на почту info@dobby.plus

Приятного пользования 🫡""")

    elif message.text == "🔑 Подписка":
        bot.send_message(message.chat.id, "Май: бесплатный период")

    elif message.text == "Главное меню":
        main_menu(message)

    elif users[message.chat.id].action == Actions.ACTION_CREATE_TASK:
        bot.send_message(message.chat.id, "Укажите url")
        users[message.chat.id].action = Actions.ACTION_TITLE_UPLOADED
        users[message.chat.id].title = message.text
    elif users[message.chat.id].action == Actions.ACTION_TITLE_UPLOADED:
        kb = [
            types.KeyboardButton(text=TimePreferences.NOW),
            types.KeyboardButton(text=TimePreferences.MORNING),
            types.KeyboardButton(text=TimePreferences.EVENING),
            types.KeyboardButton(text=TimePreferences.ONCE_A_WEEK),
            types.KeyboardButton("Главное меню")
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*kb, row_width=1)
        bot.send_message(message.chat.id, "Укажите частоту обновлений", reply_markup=markup)
        users[message.chat.id].action = Actions.ACTION_URL_UPLOADED
        users[message.chat.id].url = message.text
    elif users[message.chat.id].action == Actions.ACTION_URL_UPLOADED:
        kb = [
            types.KeyboardButton(text=SortedPrice.EXPENSIVE),
            types.KeyboardButton(text=SortedPrice.CHEAP),
            types.KeyboardButton("Главное меню")
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*kb, row_width=1)
        bot.send_message(message.chat.id, "Укажите сортировку", reply_markup=markup)
        users[message.chat.id].action = Actions.ACTION_TIME_UPLOADED
        users[message.chat.id].time_pref = message.text
    elif users[message.chat.id].action == Actions.ACTION_TIME_UPLOADED:
        kb = [
            types.KeyboardButton("Главное меню")
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*kb, row_width=1)
        bot.send_message(message.chat.id, "Поздравляем! Задача создана", reply_markup=markup)
        users[message.chat.id].action = Actions.ACTION_SORT_UPLOADED
        users[message.chat.id].sort = message.text

        with con.cursor() as cursor:
            q = f"SELECT * FROM `users` WHERE tg_id = '{message.chat.id}'"
            cursor.execute(q)
            fetchall = cursor.fetchall()
            if len(fetchall) == 0:
                cursor.execute(f"INSERT INTO `users` (tg_id, tasks) VALUES ('{message.chat.id}', '1')")
            else:
                cursor.execute(f"UPDATE `avito`.`users` SET `tasks` = '{int(fetchall[0][-1]) + 1}' WHERE (`tg_id` = "
                               f"'{message.chat.id}')")
            con.commit()
            cursor.execute("INSERT INTO `tasks` (name, url, time, sort, tg_id) VALUES "
                           f"('{users[message.chat.id].title}', '{users[message.chat.id].url}', "
                           f"'{users[message.chat.id].time_pref}', '{users[message.chat.id].sort}', "
                           f"'{message.chat.id}')")
            threading.Thread(target=track, args=[users[message.chat.id]]).start()

        con.commit()
    elif users[message.chat.id] == Actions.ACTION_TASK_DELETE:
        with con.cursor() as cursor:
            cursor.execute(f"DELETE FROM `tasks` WHERE tg_id = '{message.chat.id}' AND id = "
                           f"'{message.text.split(')')[-1][:-1]}'")
            con.commit()
        users[message.chat.id] = Actions.ACTION_START
        main_menu(message)


bot.infinity_polling()
