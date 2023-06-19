# Проект Yatube

[![Python](https://img.shields.io/badge/-Python-464641?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![HTML5](https://img.shields.io/badge/-HTML5-464646?style=flat-square&logo=html5)](https://en.wikipedia.org/wiki/HTML5)

Яндекс Практикум. Спринт 6. Финальный проект

## Описание

Yatube - это социальная сеть с авторизацией, персональными лентами, комментариями и подписками на авторов статей.

## Функционал

- Регистрируется и восстанавливается доступ по электронной почте;
- Добавляются изображения к посту;
- Создаются и редактируются собственные записи;
- Просмотриваются страницы других авторов;
- Комментируются записи других авторов;
- Подписки и отписки от авторов;
- Записи назначаются в отдельные группы;
- Личная страница для публикации записей;
- Отдельная лента с постами авторов на которых подписан пользователь;
- Через панель администратора модерируются записи, происходит управление пользователями и создаются группы.

## Установка

1. Клонировать репозиторий:

   ```python
   git clone https://github.com/valtocom/hw05_final.git
   ```

2. Перейти в папку с проектом:

   ```python
   cd hw05_final/
   ```

3. Установить виртуальное окружение для проекта:

   ```python
   python -m venv venv
   ```

4. Активировать виртуальное окружение для проекта:

   ```python
   # для OS Lunix и MacOS
   source venv/bin/activate

   # для OS Windows
   source venv/Scripts/activate
   ```

5. Установить зависимости:

   ```python
   python3 -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Выполнить миграции на уровне проекта:

   ```python
   cd yatube
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```

7. Запустить проект локально:

   ```python
   python3 manage.py runserver

   # адрес запущенного проекта
   http://127.0.0.1:8000
   ```

8. Зарегистирировать суперпользователя Django:

   ```python
   python3 manage.py createsuperuser

   # адрес панели администратора
   http://127.0.0.1:8000/admin
   ```
