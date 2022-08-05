import vk_api
import emoji
import requests
import random
from db import DataBase
from pprint import pprint
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardButton, VkKeyboardColor
import sqlalchemy as sq
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class Vkinder(DataBase):
    group_token = ''
    user_token = ''
    vk = vk_api.VkApi(token=group_token)
    longpoll = VkLongPoll(vk)
    _url_method = 'https://api.vk.com/method'
    user_who_write = ''

    def __init__(self, user_id):
        self.user_id = user_id

    def _get_url(self, method):
        # Получение URL
        return '/'.join((self._url_method, method))

    def write_msg(self, user_id, message=None, keyboard=None, attachment=None):
        # Отправка сообщения с проверкой на наличие клавиатуры ВК
        post = {'user_id': user_id,
                'message': message,
                'random_id': random.randint(0, 2048),
                'attachment': attachment}
        if keyboard:
            post['keyboard'] = keyboard.get_keyboard()
        self.vk.method('messages.send', post)

    def take_params_from_user(self):
        # Активация бота полсе любого сообщения пользователя
        print('Bot started')
        print('----------------')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    global user_who_write
                    user_who_write = event.user_id
                    request = event.text
                    if request.lower() == 'начать поиск':
                        sex = self.person_sex(user_id=event.user_id)
                        age_from = self.person_age_from(user_id=event.user_id)
                        age_to = self.person_age_to(user_id=event.user_id)
                        city = self.person_city(user_id=event.user_id)
                        return sex, age_from, age_to, city
                    else:
                        keyboard = VkKeyboard(one_time=True)
                        keyboard.add_button("Начать поиск", VkKeyboardColor.PRIMARY)
                        self.write_msg(event.user_id,
                                       "Для запуска приложения по поиску второй половинки нажмите кнопку "
                                       "'Начать поиск'."
                                       "\n Обращаем Ваше внимание, что поиск осуществляется только на территориий "
                                       "Российской Федерации!",
                                       keyboard)

    def person_sex(self, user_id):
        # Получение пола партнера
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Мужской', VkKeyboardColor.PRIMARY)
        keyboard.add_button('Женский', VkKeyboardColor.PRIMARY)
        self.write_msg(user_id, 'Какого пола спутника Вы ищите?', keyboard)
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    if event.text.lower() == 'мужской':
                        sex = 2
                        return sex
                    elif event.text.lower() == 'женский':
                        sex = 1
                        return sex
                    else:
                        self.write_msg(user_id, 'Ошибка указания пола партнера! Воспользуйтесь VK клавиатурой! '
                                                '\nКакого пола спутника Вы ищите?', keyboard)

    def person_age_from(self, user_id):
        # Получение минимального возраста партнера
        self.write_msg(user_id, 'Какой минимальный возраст Вашего спутника?')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    if 17 < int(event.text) < 90:
                        global age_from
                        age_from = event.text
                        return age_from
                    else:
                        self.write_msg(user_id, 'Возраст не может быть менее 17 лет и более 89 лет!'
                                                '\nКакой минимальный возраст Вашего спутника?')

    def person_age_to(self, user_id):
        # Получение максимального возраста партнера
        self.write_msg(user_id, 'Какой максимальный возраст Вашего спутника?')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    if int(age_from) <= int(event.text):
                        age_to = event.text
                        return age_to
                    else:
                        self.write_msg(user_id, 'Максимальный возраст не может быть менее минимального возраста!'
                                                '\nКакой максимальный возраст Вашего спутника?')

    def unpacking_cities(self, city_name):
        # Получение списка городов по заданному пользователем названию
        _url = self._get_url('database.getCities')
        responce = requests.get(_url, {'access_token': self.user_token, 'v': '5.131', 'need_all': 1, 'q': city_name,
                                       'country_id': 1})
        return responce.json()['response']['items']

    def person_city(self, user_id):
        # Получение города проживания партнера
        self.write_msg(user_id, 'Из какого города Вы хотите найти спутника?')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    person_input = self.unpacking_cities(event.text)
                    if len(person_input) > 1:
                        b, c = 1, []
                        for dicts in person_input:
                            if len(dicts) == 2:
                                self.write_msg(user_who_write, f"{b} - город в {dicts['title']}")
                                c.append(dicts.items())
                            else:
                                for pairs in dicts.items():
                                    if 'area' in pairs:
                                        self.write_msg(user_who_write, f'{b} - город в {pairs[1]}')
                                        c.append(dicts.items())
                            b += 1
                        self.write_msg(user_who_write, 'Напишите порядковый номер города, который Вы ищите')
                        print('Список городов по заданным параметрам:')
                        pprint(c)
                        print('----------------')
                        for events in self.longpoll.listen():
                            if events.type == VkEventType.MESSAGE_NEW:
                                if events.to_me:
                                    city = person_input[int(events.text)-1]['id']
                                    return city
                    else:
                        city = person_input[0]['id']
                        return city

    def find_person(self, options):
        # Возвращает json файл с партнерами по заданным пользователем параметрам
        _url = self._get_url('users.search')
        responce = requests.get(_url, options).json()
        return responce

    def zip_params(self):
        # Создает словарь для поиска партнера по параметрам
        params_name_for_vk = ('sex', 'age_from', 'age_to', 'city')
        person_params = self.take_params_from_user()
        return dict(zip(params_name_for_vk, person_params))

    def find_partners(self):
        # Возвращает список партнеров
        options = {
            'access_token': self.user_token,
            'v': '5.131',
            'status': '6',
            'fields': 'is_closed, has_photo, city, country, relation',
            'count': 1000
        }
        options_from_user = self.zip_params()
        options.update(options_from_user)
        found_partners = self.find_person(options)
        return found_partners

    def get_send_photos(self, partner_id):
        # Получение и отправление 3-х лучших фото партнера
        _url = self._get_url('photos.getAll')
        params = {
            'access_token': self.user_token,
            'v': '5.131',
            'owner_id': partner_id,
            'extended': 1
        }
        responce = requests.get(_url, params).json()
        photos_with_likes = dict()
        for values in responce.values():
            for _ in values.values():
                if isinstance(_, list):
                    for photo_info in _:
                        id_photo = str(photo_info.get('id'))
                        likes_count = photo_info.get('likes')
                        if likes_count.get('count'):
                            likes = likes_count.get('count')
                            photos_with_likes[likes] = id_photo
        list_of_ids = sorted(photos_with_likes.items())
        for photos in list_of_ids[-1:-4:-1]:
            for _ in photos:
                if isinstance(_, str):
                    photo_id = int(_)
                    self.write_msg(user_who_write, attachment=f'photo{partner_id}_{photo_id}')

    def send_info_about_partner(self):
        # Отправление информации о подходящих партнерах
        self.create_database()
        self.create_tables()
        partners = self.find_partners()
        partners_open_page = []
        for values in partners.values():
            for _ in values.values():
                if isinstance(_, list):
                    for info in _:
                        if not info.get('is_closed'):
                            partners_open_page.append(info)
                            partner_vk_id = info['id']
                            self.info_into_users(user_who_write, partner_vk_id)
        partner_count = len(partners_open_page)
        if partner_count == 0:
            self.write_msg(user_who_write,
                           (emoji.emojize(f'Увы, но по заданным параметрам партнеров не найдено! '
                                          f'Попробуйте изменить параметры!:red_heart:')))
            self.send_id()
        else:
            self.write_msg(user_who_write,
                           (emoji.emojize(f'Мы нашли {partner_count} подходящих партнеров для Вас! '
                                          f'Напишите "Далее", чтобы увидеть их странички VK :red_heart:')))
        i = 0

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    if event.text.lower() == 'далее':
                        partner_id = 'not seen'
                        while partner_id == 'not seen':
                            partner_page_vk = partners_open_page[i]['id']
                            if not self.search_seen_users(user_who_write, partner_page_vk):
                                i += 1
                                continue
                            else:
                                self.info_into_seen_users(user_who_write, partner_page_vk)
                                self.write_msg(user_who_write, f'https://vk.com/id{partner_page_vk}')
                                self.get_send_photos(partner_page_vk)
                                i += 1
                                partner_id = 'seen'


bot = Vkinder()

bot.send_info_about_partner()
