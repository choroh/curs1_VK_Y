'''
Netology
Курсовая работа. 11.08.21
Нужно написать программу для резервного копирования фотографий с профиля(аватарок) пользователя vk в облачное хранилище Яндекс.Диск.
Для названий фотографий использовать количество лайков, если количество лайков одинаково, то добавить дату загрузки.
Информацию по сохраненным фотографиям сохранить в json-файл.
'''

import requests
from pprint import pprint
import operator
import json

# получаем токены от VK и Яндекс
with open('files/t.txt') as f:
    token = f.readline().strip()
V = '5.131'
numbers = 5  # количество фотографий для скачивания

owner_id = ''  # id по умолчанию

#  Работа с аккаунтом VK
class VKUser:
    url = 'https://api.vk.com/method/'
    #  Авторизация на VK
    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }

#  Функция получения списка фотографий с профиля
    def get_photos(self, owner_id=None):
        photo_url = self.url + 'photos.get'
        photo_params = {
            'owner_id': owner_id,
            'count': numbers,
            'album_id': 'profile',
            'photo_size': 1
        }
        req = requests.get(photo_url, params={**self.params, **photo_params}).json()
        return req

    def photo_info(self, owner_id=None):
        self.owner_id = owner_id
        req = self.get_photos(owner_id)
        # Получение данных о фотографиях
        photos_all_list = req.get('response').get('items')
        # all_my_photo словарь id: прочая информаци по нему
        all_my_photo = {}
        for i in photos_all_list:
            #  photos_sizes словать коллекции фото с разлиными размерами текущего id
            photos_sizes = {}
            # photo_info слоарь - данные по всем фотографиям сгруппированне по id.
            # id: словарь данных по текущей фотографии
            photo_info = {}
            id_photo = i.get('id')
            date_photo = i.get('date')
            photo_info['date_photo'] = date_photo
            sizes = i.get('sizes')
            for j in sizes:
                height = j.get('height')
                width = j.get('width')
                size = j.get('type')
                url_photo_collection = j.get('url')
                #  получаем разешение каждой фото из коллекции и их площадь
                resolution = f'{height} x {width}'
                #  площадь в ключе словаря используем для сортировки
                photos_sizes[height * width] = [resolution, url_photo_collection, size]

            #  сортируем словарь с коллекцией фотографий по площади изображения, выбираем последнюю, как самую большую
            resolutions_list = sorted(photos_sizes.items(), key=operator.itemgetter(0))

            #  получаем максимальное разрешение и адрес
            url_resolution_collection_max = resolutions_list[len(resolutions_list) - 1][1]
            resolution_max = url_resolution_collection_max[0]
            url_max = url_resolution_collection_max[1]
            size_max = url_resolution_collection_max[2]

            photo_info['resolution_max'] = resolution_max
            photo_info['url_max'] = url_max
            photo_info['type'] = size_max

            all_my_photo[id_photo] = photo_info
        return all_my_photo

    #  Сохраняем лог
    def write_log(self, to_json):
        with open('files/log.json', 'w') as f_log:
            json.dump(to_json, f_log, indent=1)


#  Работа с аккаунтом Яндекс
class YaUploader:
    #  Авторизация на Яндексе
    def __init__(self, token_y: str):
        self.token_y = token_y
        self.APT_BASE_URL = 'https://cloud-api.yandex.net/'
        self.headers = {'Authorization': OAuth}

    def upload(self, file_in, file_out):
        self.file_in = file_in
        self.file_out = file_out

        #  Получаем ссылку для загрузки файла на Яндекс диск в папку Netology/Photo_VK
        req = requests.post(self.APT_BASE_URL + 'v1/disk/resources/upload', headers=self.headers, params={'path': self.file_out, 'url': self.file_in})
        if req.status_code == 202:
            print('##', end='')
            success = True
        else:
            print('При отправке произошла ошибка', req.status_code)
            success = False
        return success

    def create_folder(self):
        req = requests.put(self.APT_BASE_URL + 'v1/disk/resources?path=Netology/Photo_VK', headers=self.headers)

#  Запрашиваем у пользователя ID VK. Если не введет- то по умолчанию свой ID
owner_id = input('Введите ID аккаунта VK: ')
if not owner_id:
    owner_id = '416852531'

#  Запрашиваем у пользователя токен Яндекс
token_yandex = input('Введите токен Яндекс Диска: ')

#  Создаем экземпляр класса
vk_client = VKUser(token, V)

#  Работаем с Яндекс
OAuth = token_yandex
uploader = YaUploader(OAuth)
file_out = 'Netology/Photo_VK'
log = []

# Создать папку на Яндекс
uploader.create_folder()

for i in list(vk_client.photo_info(owner_id).values()):
    log_dict = {}
    size = i['type']
    file_in = i['url_max']  # Полученные ссылки на фотографии
    date_photo = i['date_photo']
    file_out = 'Netology/Photo_VK/' + str(date_photo) + '.jpeg'
    #  Отправляем фотографии на Яндекс
    result = uploader.upload(file_in, file_out)
    #  Готовим иноформацию для записи в лог
    log_dict['file_name'] = str(date_photo) + '.jpeg'
    log_dict['size'] = size
    log.append(log_dict)

print()
vk_client.write_log(log)
if result:
    print(f'{numbers} фотографий с аккаунта VK успешно загружено на аккаунт Яндекс')