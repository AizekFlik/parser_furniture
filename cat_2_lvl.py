from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import pandas as pd
import os

def get_slug_from_url(url):
    # Извлекаем часть URL до знака вопроса, если он есть
    base_url = url.split('?')[0]
    # Затем получаем последний компонент URL
    slug = base_url.rstrip('/').split('/')[-1]
    return slug

def get_fullname(item):
    try:
        # Попытка найти fullname в стандартном месте
        return item.find_element(By.CSS_SELECTOR, "mini-product__h4-custom").text
    except NoSuchElementException:
        # Если не найдено, пытаемся найти fullname в альтернативном месте
        try:
            return item.find_element(By.CSS_SELECTOR, ".mini-product__atr-group .mini-product__atr").text
        except NoSuchElementException:
            # В случае отсутствия fullname возвращаем пустую строку или другое подходящее значение
            return ""

# Функция для сбора данных с одной страницы
def get_cat_lvl_2(url, parent_slug):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "category__grid-4")))

    products_data = []

    while True:
        # Получение текущего URL и извлечение slug
        current_url = driver.current_url
        slug = get_slug_from_url(current_url)

        # Извлечение данных 'name' и 'fullname'
        name = driver.find_element(By.CSS_SELECTOR, ".breadcrumbs__item.breadcrumbs__dont-a").text
        fullname = driver.find_element(By.CSS_SELECTOR, ".category__h1 h1").text

        container = driver.find_element(By.CLASS_NAME, "category__grid-4")
        grid_items = container.find_elements(By.CLASS_NAME, "category__grid-item")

        for item in grid_items:
            full_name = get_fullname(item)
            product_data = {
                'slug': slug,
                'name': name,
                'fullname': fullname,
                'productname': full_name,
                'parent': parent_slug
            }
            products_data.append(product_data)

        # Проверка наличия кнопки "Следующая" и переход на следующую страницу
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, ".pagination__item_next")
            next_page_url = next_button.get_attribute('data-href')

            if next_page_url:
                driver.get(next_page_url)
                time.sleep(5)
            else:
                break
        except NoSuchElementException:
            break

    return pd.DataFrame(products_data, columns=cat_columns)

# Данные
cat_columns = ['slug', 'name', 'fullname', 'productname', 'parent']
category_lvl_2_df = pd.DataFrame(columns=cat_columns)

# Система
current_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(current_dir, "Категории 2 уровня - Столы для переговоров.csv") 

# Драйвер
service = Service('./chromedriver-win64/chromedriver.exe')
driver = webdriver.Chrome(service=service)

# Базовые данные
driver.get('https://krasnodar.prime-wood.ru/stoly-dlya-peregovorov/')
time.sleep(7)

# Получение словаря категорий 2-ого уровня
container = driver.find_element(By.CLASS_NAME, "product__tegs")
links_elements = container.find_elements(By.TAG_NAME, "a")
link_lvl_2 = {link.text: link.get_attribute('href') for link in links_elements}

# Получение slug родительской категории
parent_slug = driver.current_url.split('/')[-2]

# Перебор категорий 2-ого уровня и сбор данных
for text, url in link_lvl_2.items():
    category_lvl_2_df = pd.concat([category_lvl_2_df, get_cat_lvl_2(url, parent_slug)], ignore_index=True)

# Сохранение данных в CSV
category_lvl_2_df.to_csv(output_path, index=False)
print('Сбор данных завершен')

# Закрытие браузера
driver.quit()
