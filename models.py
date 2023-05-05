from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get(
    "view-source:https://www.avito.ru/kostroma/tovary_dlya_detey_i_igrushki/igrushki-ASgBAgICAUT~AZYJ?cd=1&q"
    "=%D1%82%D0%B0%D1%87%D0%BA%D0%B8%27")
elem = driver.find_element(By.NAME, "q")
print(elem.text)
