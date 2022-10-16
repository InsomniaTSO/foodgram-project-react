[![CI](https://github.com/InsomniaTSO/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)](https://github.com/InsomniaTSO/yamdb_final/actions/workflows/yamdb_workflow.yml)

# __Проект «Продуктовый помощник»__

## __Описание__:

Cайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное 
и подписываться на публикации других авторов. 
Сервис «Список покупок» позволит пользователям создавать список продуктов, 
которые нужно купить для приготовления выбранных блюд.

## __Авторы__:
Татьяна Манакова.

## __Технологии__:

* [Python](https://www.python.org/)
* [Django](https://www.djangoproject.com/)
* [Django REST framework](https://www.django-rest-framework.org/)
* [PostgreSQL](https://www.postgresql.org/)
* [Docker](https://www.docker.com/)
* [Gunicorn](https://gunicorn.org/)
* [Nginx](https://nginx.org/)

## __Подготовка и запуск проекта__:

* Клонируйте репозиторий:

```
git clone https://github.com/InsomniaTSO/foodgram-project-react
```

* На сервере установите Docker и docker-compose:

```
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

* Скопируйте docker-compose.yml и default.conf на сервер и заполните .env по шаблону:

```
scp myfile.dat pingvin@192.168.1.74:/home/pingvin
```

* На сервере соберите запустите контейнеры:

```
sudo docker-compose up -d --build
```
Миграции и база данных с тестовыми данными запустится автоматически.

### __Шаблон наполнения env-файла__:

```
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=xxxxxx # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД
SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxx # секретный ключ из settings.py 
```

## Ссылки

Проект доступен по ссылке <http://insomniatso.sytes.net/>

