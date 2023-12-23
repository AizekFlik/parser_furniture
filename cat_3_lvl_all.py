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
        return item.find_element(By.CSS_SELECTOR, ".mini-product__h4-custom").text
    except NoSuchElementException:
        # Если не найдено, пытаемся найти fullname в альтернативном месте
        try:
            return item.find_element(By.CSS_SELECTOR, ".mini-product__atr-group .mini-product__atr").text
        except NoSuchElementException:
            # В случае отсутствия fullname возвращаем пустую строку или другое подходящее значение
            return ""

# Функция для сбора данных с одной страницы
def get_cat_lvl_3(url, parent_slug):
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
category_lvl_3_df = pd.DataFrame(columns=cat_columns)

# Система
current_dir = os.path.dirname(os.path.abspath(__file__))

# Драйвер
service = Service('./chromedriver-win64/chromedriver.exe')
driver = webdriver.Chrome(service=service)

# Открытие веб-страницы
urls = ['https://krasnodar.prime-wood.ru/mebel-dlya-personala/',
        'https://krasnodar.prime-wood.ru/kabinety-rukovoditeley/',
        'https://krasnodar.prime-wood.ru/kresla-i-stulya/',
        'https://krasnodar.prime-wood.ru/myagkaya-ofisnaya-mebel/',
        'https://krasnodar.prime-wood.ru/stoly-dlya-peregovorov/',
        'https://krasnodar.prime-wood.ru/mebel-dlya-priemnoy/',
        'https://krasnodar.prime-wood.ru/metallicheskaya-mebel/',
        'https://krasnodar.prime-wood.ru/ofisnye-peregorodki/',
        'https://krasnodar.prime-wood.ru/ofisnye-kuhni/',
        'https://krasnodar.prime-wood.ru/raznoe/']

for url in urls:
    # Открытие каждого URL из списка
    driver.get(url)

    try:
        # Явное ожидание появления контейнера с категориями 3-ого уровня
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product__tegs")))

        # Находим контейнер seoBlock
        seoBlock_container = driver.find_element(By.CLASS_NAME, "seoBlock")

        container = seoBlock_container.find_element(By.CLASS_NAME, "product__tegs")
        links_elements = container.find_elements(By.TAG_NAME, "a")
        link_lvl_3 = {link.text: link.get_attribute('href') for link in links_elements}

        # Далее идет обработка найденных ссылок...

    except NoSuchElementException:
        # Здесь вы можете определить, что делать, если элемент не найден
        print(f"Элемент не найден на странице {url}")
        continue  # Пропускаем текущий URL и переходим к следующему

    # Получение slug родительской категории
    parent_slug = get_slug_from_url(url)

    # Перебор категорий 3-ого уровня и сбор данных
    for text, sub_url in link_lvl_3.items():
        category_lvl_3_df = pd.concat([category_lvl_3_df, get_cat_lvl_3(sub_url, parent_slug)], ignore_index=True)


# Сохранение данных в CSV
output_path = os.path.join(current_dir, "Категории 3-ого уровня.csv")
category_lvl_3_df.to_csv(output_path, index=False)
print('Сбор данных завершен')

# Закрытие браузера
driver.quit()
