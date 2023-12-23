from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import time
import pandas as pd
import os
import re

# Характеристики 1-уровня
def char_1_lvl():
    product_table = driver.find_element(By.CLASS_NAME, "product__table") # Находим контейнер таблицы характеристик
    rows = product_table.find_elements(By.CLASS_NAME, "product__table__row") # Находим все строки в таблице характеристик
    characteristics = {} # Собираем данные в словарь
    for row in rows:
        # Находим заголовок и значение в каждой строке
        char_title = row.find_element(By.CLASS_NAME, "product__table__title").text
        value = row.find_element(By.CLASS_NAME, "product__table__text").text
        characteristics[char_title] = value
    print('Характеристик  1-ого уровня собраны')
    return characteristics

# Характеристики 2-ого уровня
def char_2_lvl():
    try:
        # Попытка найти контейнеры с характеристиками товара
        columns_container = driver.find_elements(By.CLASS_NAME, "product__columns_item")
    except NoSuchElementException:
        # Если контейнер не найден, возвращаем пустой словарь
        print('Характеристик  2-ого уровня нет')
        return {}

    product_features = {}  # Инициализируем словарь для хранения характеристик

    for item in columns_container:
        title_element = item.find_element(By.CLASS_NAME, "product__columns_title")
        desc_element = item.find_element(By.CLASS_NAME, "product__columns_desc")

        title = title_element.text
        description = desc_element.text

        product_features[title] = description
    print('Характеристик  2-ого уровня собраны')

    return product_features

# Вытащить комплектации
def extract_complect_info():
    print('Сбор комплектации начат')

    righttitles = []
    rightprices = []

    try:
        # Кликаем по активной вкладке комплектации
        tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.product__tab-link[data-id='2']"))
        )
        tab.click()
        print('Кнопка нажата')
    except TimeoutException:
        # Если вкладка не найдена или не кликабельна, пропускаем этот шаг
        print('Вкладка не найдена или не кликабельна, пропускаем')
        return [], []

    # Находим активный элемент комплектации с style="display: block;"
    active_complect = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".product__tab-dot-item[style='display: block;']"))
    )

    # Ожидаем загрузки всех элементов комплектации в активном блоке
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "product__tab-dot"))
    )

    comp_elements = active_complect.find_elements(By.CLASS_NAME, "product__tab-dot")

    for element in comp_elements:
        item_name = element.find_element(By.CLASS_NAME, "product__tab-dot__name").get_attribute("title")
        righttitles.append(item_name)

        item_price = element.find_element(By.CLASS_NAME, "product__tab-dot__price").get_attribute("price")
        rightprices.append(item_price)

    print('Сбор комплектации закончен')
    print(righttitles)
    print(rightprices)
    return righttitles, rightprices

# Цвета и комплектации
def get_colors_and_complect():
    try:
        # Сначала собираем ссылки и названия цветов на основной странице
        color_elements = driver.find_elements(By.CLASS_NAME, "product__color-group__color")
        if not color_elements:
            return None, None, None, None, None

        color_links_dict = {}
        
        for element in color_elements:
            color_name = element.get_attribute("data-title")
            color_link = element.find_element(By.TAG_NAME, "a").get_attribute("href")
            color_links_dict[color_name] = color_link
        
        print(color_links_dict)

        # Переменные для сбора данных
        color_names = list(color_links_dict.keys())
        color_images = []
        all_righttitles = []
        all_rightprices = []
        all_rightcolors = []

        # Перебор ссылок на цвета и сбор данных о комплектациях
        for color_name, color_link in color_links_dict.items():
            driver.get(color_link)
            print(f'Страница - {color_link}, Цвет {color_name}')
            # Сбор изображения для цвета
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product__slider-img img")))
                image_element = driver.find_element(By.CSS_SELECTOR, ".product__slider-img img")
                image_src = image_element.get_attribute("src").replace('_w', '')
                color_images.append(image_src)
                print('Изображение добавлено')
            except TimeoutException:
                print('Изображение не найдено')
                color_images.append(None)  # Если изображение не найдено, добавляем None
            
            print('Скрипт выполняется 1')

            # Проверка наличия комплектаций
            if not driver.find_elements(By.CLASS_NAME, "product__tab-dots"):
                print('Пропускаем цвет - нет комплектации')
                continue  # Пропускаем цвет, если нет комплектаций
            
            print('Скрипт выполняется 2')

            # Сбор информации о комплектации
            righttitles, rightprices = extract_complect_info()  # Используйте функцию из предыдущего ответа
            rightcolors = [color_name] * len(righttitles)
            print('Скрипт выполняется 3')

            all_righttitles.extend(righttitles)
            all_rightprices.extend(rightprices)
            all_rightcolors.extend(rightcolors)

        colors = '|'.join(color_names)
        colorsimg = '|'.join(color_images)

        print("Сбор комплектации и цветов закончен")

        return colors, colorsimg, all_righttitles, all_rightprices, all_rightcolors

    except NoSuchElementException:
        return None, None, None, None, None

def get_children_info():
    print('Сбор дочерних товаров начат')
    children = []
    childrencat = []
    children_urls = []

    # Проверяем, есть ли элемент product-sorting__main на странице
    if not driver.find_elements(By.CLASS_NAME, "product-sorting__main"):
        print('Дочерние товары отсутствуют')
        return children, childrencat, children_urls  # Возвращаем пустые списки, если нет дочерних товаров

    # Находим основную сетку разделов дочерних товаров
    main_grid = driver.find_element(By.CLASS_NAME, "product-sorting__main")

    # Находим все секции в основной сетке
    sections = main_grid.find_elements(By.CLASS_NAME, "product-sorting__item")

    for section in sections:
        try:
            section_name = section.find_element(By.CLASS_NAME, "product__h2").text
        except NoSuchElementException:
            continue

        try:
            products_grid = section.find_element(By.CLASS_NAME, "products_grid")
            grid_items = products_grid.find_elements(By.CLASS_NAME, "products_grid-item")
        except NoSuchElementException:
            continue

        for item in grid_items:
            try:
                id_element = item.find_element(By.CSS_SELECTOR, ".mini-product__atr[title^='ID: ']")
                product_id = id_element.get_attribute("title").split(": ")[1]
                # Извлекаем ссылку на товар
                link_element = item.find_element(By.TAG_NAME, "a")
                children_url_item = link_element.get_attribute("href")
            except NoSuchElementException:
                continue

            children.append(product_id)
            childrencat.append(section_name)
            children_urls.append(children_url_item)

    return children, childrencat, children_urls

# Парсинг товара
def parser_item(url):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product__block-control__text")))

    # Получение текущего URL, slug
    current_url = driver.current_url
    slug_split = current_url.rstrip('/').split('/')
    slug = slug_split[-1]
    print(f'URL - {current_url}')
    print(f'slug - {slug}')

    # article, title, catcolor
    article_text = driver.find_element(By.CSS_SELECTOR, ".product__block-control__text").text
    article = article_text.split()[1]
    title = driver.find_element(By.CSS_SELECTOR, ".product__head h1").text
    try:
        # Попытка найти элемент и получить его текст
        catcolor = driver.find_element(By.CSS_SELECTOR, ".product__color-group__title.mb-2 span").text
    except NoSuchElementException:
        # Если элемент не найден, присваиваем переменной catcolor значение None или другое подходящее значение
        catcolor = None
    main = slug_split[3]
    print(f'article - {article}')
    print(f'title - {title}')
    print(f'catcolor - {catcolor}')
    print(f'main - {main}')

    # gallery
    images_elements = driver.find_elements(By.CSS_SELECTOR, ".product-slider-mini-img img") # Находим все элементы img внутри контейнеров product-slider-mini-img
    images_urls = [img.get_attribute('src').replace('_w', '') for img in images_elements] # Собираем ссылки на картинки в список, удаляя суффикс '_w'
    gallery = '|'.join(images_urls)
    print('Галерея собрана')

    # Характеристики
    char_1_lvl_keys = ['Ширина', 'Глубина', 'Высота', 'Длина', 'Объем', 'Материал столешницы', 'Толщина столешницы', 'Страна производства', 'Ценовой сегмент', 'Стиль мебели']
    characteristics = char_1_lvl()  # Первый словарь
    product_features = char_2_lvl()  # Второй словарь

    # Проходим по копии первого словаря
    for key in list(characteristics.keys()):
        if key not in char_1_lvl_keys:
            # Перемещаем пару ключ-значение во второй словарь
            product_features[key] = characteristics[key]
            # Удаляем пару из первого словаря
            del characteristics[key]

    # Описание
    information_element = driver.find_element(By.CLASS_NAME, "product__information") # Находим элемент с информацией о продукте
    information_html = information_element.get_attribute('innerHTML') # Получаем HTML содержимое элемента
    soup = BeautifulSoup(information_html, 'html.parser') # Используем BeautifulSoup для парсинга HTML    
    p_tags = soup.find_all('p') # Находим все теги <p> и их содержимое
    filtered_html = ''.join(str(tag) for tag in p_tags) # Собираем содержимое всех тегов <p> в одну строку, сохраняя HTML-теги
    print('Описание получено')
    
    # Цена
    price_element = driver.find_element(By.CLASS_NAME, "product__price__new") # Найти элемент, содержащий цену
    price = price_element.get_attribute("new-price") # Получить цену из атрибута new-price
    print(f'Цена получена - {price}')

    children, childrencat, children_urls = get_children_info()
    print(children)
    print(childrencat)
    print(len(children_urls))
    children = '|'.join(children)
    childrencat = '|'.join(childrencat)

    # Цвета
    print('Сбор цветов и комплектации начат')
    colors, colorsimg, righttitles, rightprices, rightcolors = get_colors_and_complect()
    
    print(rightcolors)

    righttitles = '|'.join(righttitles)
    rightprices = '|'.join(rightprices)
    rightcolors = '|'.join(rightcolors)

    item_data = {'article': article, 
                 'title': title, 
                 'slug': slug, 
                 'url': current_url, 
                 'catslug': None, 
                 'cat': None, 
                 'catcolor': catcolor, 
                 'tags': None, 
                 'gallery': gallery, 
                 'main': main, 
                 'width': characteristics.get('Ширина'), 
                 'depth': characteristics.get('Глубина'), 
                 'height': characteristics.get('Высота'), 
                 'length': characteristics.get('Длина'), 
                 'volume': characteristics.get('Объем'), 
                 'material': characteristics.get('Материал столешницы'), 
                 'thick': characteristics.get('Толщина столешницы'), 
                 'producer': characteristics.get('Страна производства'), 
                 'segment': characteristics.get('Ценовой сегмент'), 
                 'style': characteristics.get('Стиль мебели'), 
                 'addtitle': '|'.join(product_features.keys()),
                 'addvalue': '|'.join(product_features.values()), 
                 'description': filtered_html, 
                 'colors': colors, 
                 'colorsimg': colorsimg, 
                 'price': price, 
                 'righttitles': righttitles, 
                 'rightcolors': rightcolors, 
                 'rightprices': rightprices, 
                 'children': children,
                 'childrencat': childrencat,
                 'children_urls': children_urls}
    
    item_data_list = {key: [value] for key, value in item_data.items()} # Преобразуем каждое скалярное значение в список
    df = pd.DataFrame(item_data_list) # Теперь можно безопасно создать DataFrame
        
    return df

# Данные
item_columns = ['article', 'title', 'slug', 'url', 'catslug', 'cat', 'catcolor', 
               'tags', 'gallery', 'main', 'width', 'depth', 'height', 'length', 
               'volume', 'material', 'thick', 'producer', 'segment', 'style', 
               'addtitle', 'addvalue', 'description', 'colors', 'colorsimg', 
               'price', 'righttitles', 'rightcolors', 'rightprices', 'children', 'childrencat', 'children_urls']

# Система
current_dir = os.path.dirname(os.path.abspath(__file__))

# Инициализация WebDriver
service = Service('./chromedriver-win64/chromedriver.exe')
driver = webdriver.Chrome(service=service)

df = parser_item("https://krasnodar.prime-wood.ru/kresla-i-stulya/ofisnye-styliya/styliya-iso/stul-ofisnyy-iso-black-c/")

# Закрытие браузера
driver.quit()

# Сохранение данных в CSV
output_path = os.path.join(current_dir, "Товар.csv")
df.to_csv(output_path, index=False)


