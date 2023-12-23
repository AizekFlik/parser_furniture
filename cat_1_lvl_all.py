from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd
import os

# slug: Короткое имя категории, используемое в URL.
# name: Короткое имя категории, извлеченное из хлебных крошек.
# fullname: Полное имя категории, отображаемое на странице.
# productname: Наименование продукта в этой категории.
# parent: Slug родительской категории.

# TODO ДАННЫЕ

# Данные
cat_columns = ['slug', 'name', 'fullname', 'productname', 'parent']
category_lvl_1_df = pd.DataFrame(columns=cat_columns)

# Система
current_dir = os.path.dirname(os.path.abspath(__file__)) #? Получение текущей директории
output_path = os.path.join(current_dir, "Категории 1-ого уровня.csv") 

# TODO ДРАЙВЕР

# Запуск драйвера браузера
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

# Дать странице время для загрузки
time.sleep(7)

# Получение текущего URL и slug 
current_url = driver.current_url
slug_list = current_url.split('/')  # Разбить на список
slug_clean = [item for item in slug_list if item]
slug = slug_clean[-1]

# TODO СБОР ДАТАФРЕЙМА

# Категории 1-ого уровня
def get_cat_lvl_1():
    global slug
    global cat_columns

    # Извлечение данных 'name' и 'fullname'
    name = driver.find_element(By.CSS_SELECTOR, ".breadcrumbs__item.breadcrumbs__dont-a").text
    fullname = driver.find_element(By.CSS_SELECTOR, ".category__h1 h1").text

    container = driver.find_element(By.CLASS_NAME, "category__grid-4") # Находим контейнер с карточками товаров
    grid_items = container.find_elements(By.CLASS_NAME, "category__grid-item") # Находим все карточки товаров внутри контейнера

    # Подготовка списка для DataFrame
    products_data = []

    # Перебор всех карточек и сбор информации о товарах
    for item in grid_items:
        # Извлечение 'productname'
        full_name = item.find_element(By.CLASS_NAME, "mini-product__h4-custom").text # Находим первую часть названия товара

        # Формирование записи о товаре
        product_data = {
            'slug': slug,
            'name': name,
            'fullname': fullname,
            'productname': full_name,
            'parent': ''  # Оставляем пустым
        }

        products_data.append(product_data)

    return pd.DataFrame(products_data, columns=cat_columns)

# Цикл по страницам
for url in urls:
    # Открытие веб-страницы
    driver.get(url)
    time.sleep(7)  # Дать странице время для загрузки

    # Получение текущего URL и slug 
    slug = url.split('/')[-2]  # Предполагается, что слаг - предпоследний элемент URL

    while True:
        # Сбор данных со страницы и добавление в DataFrame
        new_data_df = get_cat_lvl_1()
        category_lvl_1_df = pd.concat([category_lvl_1_df, new_data_df], ignore_index=True)

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

# Сохранить DataFrame для проверки
category_lvl_1_df.to_csv(output_path, index=False)
print('done')

# Не забудьте закрыть драйвер после завершения
driver.quit()
