import sqlite3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

URL = 'https://www.avito.ru/kostroma?q=машина'
PAUSE_DURATION_SECONDS = 5


def grouper(iterable, n):
    args = [iter(iterable)] * n
    return zip(*args)


class Product:
    def __init__(self, title, price):
        self.title = title
        self.price = price

    def __str__(self):
        return self.title + " " + self.price


products = list()


def main():
    driver.get(URL)
    if bool(driver.find_elements(By.CLASS_NAME, "items-extraTitle-JFe8_")):
        elem = driver.find_elements(By.XPATH, "//div[contains(concat(' ', @class, ' '), 'items-items-kAJAg')]")
        list_ = elem[0].text.split("\n")
        for index, i in enumerate(list_):
            try:
                if "₽" in list_[index + 1]:
                    products.append(Product(list_[index], list_[index + 1]))
            except IndexError:
                pass
    else:
        elem = driver.find_element(By.CLASS_NAME, "styles-module-root-OK422")
        for i in range(int(elem.text.split("\n")[-1])):
            driver.get("https://www.avito.ru/kostroma?q=машина&p=" + str(i + 1))
            if bool(driver.find_elements(By.CLASS_NAME, "items-extraTitle-JFe8_")):
                elem = driver.find_elements(By.XPATH, "//div[contains(concat(' ', @class, ' '), 'items-items-kAJAg')]")
                list_ = elem[0].text.split("\n")
                for index, i in enumerate(list_):
                    try:
                        if "₽" in list_[index + 1]:
                            products.append(Product(list_[index], list_[index + 1]))
                    except IndexError:
                        pass


if __name__ == '__main__':
    try:
        sqlite_connection = sqlite3.connect('sqlite_python.db')
        service = Service(executable_path="chromedriver.exe")
        driver = webdriver.Chrome(service=service)
        main()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    except Exception as e:
        print(e)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
        driver.quit()

