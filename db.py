import sqlalchemy as sq
import psycopg2
from pprint import pprint
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DataBase:
    # Подключение к существующей базе данных
    connection = psycopg2.connect(user='',
                                  password='',
                                  host='',
                                  port='')
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    # Курсор для выполнения операций с базой данных
    cursor = connection.cursor()

    def create_database(self):
        # Создание базы данных, если она не была создана ранее
        try:
            sql_create_database = 'create database if not exists postgres'
            self.cursor.execute(sql_create_database)
        except:
            print('Database created or was created')
        print('----------------')

    def create_tables(self):
        # Создание таблиц, если они не были созданы ранее
        with self.cursor:
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS users(
                id serial PRIMARY KEY,
                user_who_find_vk_id varchar(20) NOT NULL,
                partner_vk_id varchar(20) NOT NULL);"""
            )
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS seen_users(
                id serial primary key,
                user_who_find_vk_id varchar(20) not null,
                partner_vk_id varchar(20) not null);"""
            )
        print('Tables User and Seen_users created or were created')
        print('----------------')

    def info_into_users(self, user_who_write_vk_id, partner_vk_id):
        # Заполнение таблицы 'users' всеми найденными партнерами
        cur = self.connection.cursor()
        with cur:
            cur.execute(
                f"""insert into users(
                user_who_find_vk_id, partner_vk_id) 
                values ({user_who_write_vk_id}, {partner_vk_id});"""
            )

    def info_into_seen_users(self, user_who_write_vk_id, partner_vk_id):
        # Заполнение таблицы 'seen_users' просмотренными партнерами
        cur = self.connection.cursor()
        with cur:
            cur.execute(
                f"""insert into seen_users(
                user_who_find_vk_id, partner_vk_id) 
                values ({user_who_write_vk_id}, {partner_vk_id});"""
            )

    def search_seen_users(self, user_who_write_vk_id, partner_vk_id):
        # Проверка данных таблицы 'seen_users' на повторяющийся показ партнера для каждого пользователя
        person = True
        cur = self.connection.cursor()
        cur.execute(
                'select user_who_find_vk_id, partner_vk_id from seen_users '
                'where user_who_find_vk_id = %(user_who_write)s '
                'and partner_vk_id = %(partner_vk)s',
                {'user_who_write': str(user_who_write_vk_id), 'partner_vk': str(partner_vk_id)}
        )
        check_partner = cur.fetchall()
        if check_partner:
            print(f'Пользователь с id {user_who_write_vk_id} просматривал партнера с id {partner_vk_id}')
            print('----------------')
            person = False
        else:
            print(f'Пользователь с id {user_who_write_vk_id} не просматривал партнера с id {partner_vk_id}')
            print(f'Вывод партнера с id {partner_vk_id}')
            print('----------------')
        return person

