'''
Netology
Курсовая работа. 11.08.21
Нужно написать программу для резервного копирования фотографий с профиля(аватарок) пользователя vk в облачное хранилище Яндекс.Диск.
Для названий фотографий использовать количество лайков, если количество лайков одинаково, то добавить дату загрузки.
Информацию по сохраненным фотографиям сохранить в json-файл.
'''

import requests
#  from pprint import pprint
import operator
import json
from datetime import datetime


#  Работа с аккаунтом VK
class VKUser:
    url = 'https://api.vk.com/method/'
    #  Авторизация на VK

    def __init__(self):
        # получаем токены от VK
        self.token = ''
        while self.token == '':
            self.token = input('Введите токен VK: ').strip()
        self.V = '5.131'
        self.params = {
            'access_token': self.token,
            'v': self.V
        }

#  Функция получения списка фотографий с профиля
    def get_photos(self, numbers, owner_id=None):
        photo_url = self.url + 'photos.get'
        photo_params = {
            'owner_id': owner_id,
            'count': numbers,
            'album_id': 'profile',
            'photo_size': 1
        }
        req = requests.get(photo_url, params={**self.params, **photo_params}).json()
        return req

    #  Обработка данных с аккаунта VK
    def photo_info(self, owner_id=None):
        self.owner_id = owner_id
        self.numbers = self.ask_nombers()
        req = self.get_photos(self.numbers, owner_id)
        # Получение данных о фотографиях
        try:
            photos_all_list = req.get('response').get('items')
        except Exception as error:
            print('Убедитесь в верном токене. ')
            return 'Убедитесь в верном токене VK. {error}'
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

    #  Запрашиваем число фотографий для скачивания. Ограничение - 20, по умолчанию 5.
    def ask_nombers(self):
        numbers = input('Введите число фотографий для скачивания до 20, по умолчанию - 5: ')
        if numbers == '':
            numbers = 5
        else:
            while not numbers.isdigit() or int(numbers) <= 0 or int(numbers) > 20:
                numbers = input('Введите число фотографий для скачивания до 20, по умолчанию - 5: ')
            numbers = int(numbers)
        return numbers


#  Работа с аккаунтом Яндекс
class YaUploader:
    #  Авторизация на Яндексе
    OAuth = input('Введите токен Яндекс Диска: ')

    def __init__(self):
        self.APT_BASE_URL = 'https://cloud-api.yandex.net/'
        self.headers = {'Authorization': self.OAuth}

    def upload(self, file_in, file_out):
        self.file_in = file_in
        self.file_out = file_out

        #  Получаем ссылку для загрузки файла на Яндекс диск в папку пользователя
        try:
            req = requests.post(self.APT_BASE_URL + 'v1/disk/resources/upload', headers=self.headers, params={'path': self.file_out, 'url': self.file_in})
        except Exception as error:
            print('Убедитесь в правильности токена Yandex. ')
            return 'Убедитесь в правильности токена Yandex. {error}'

        if req.status_code == 202:
            print('##', end='')
            success = True
        else:
            print('При отправке произошла ошибка', req.status_code)
            success = False
        return success

    # Создать папку на Яндекс
    def create_folder(self, folder_name):
        self.folder_name = folder_name
        req = requests.put(self.APT_BASE_URL + 'v1/disk/resources?path=' + self.folder_name, headers=self.headers)


def run_copy():
    count = 0
    #  Запрашиваем у пользователя ID VK и имя папки для загрузки на Яндекс.
    folder_name = ''
    owner_id = ''
    while folder_name == '':
        folder_name = input('Введите название папки для сохранения фотографий на Яндекс-Диске: ')
    while owner_id == '':
        owner_id = input('Введите ID аккаунта VK: ')
    log = []

    # Создать папку на Яндекс
    uploader.create_folder(folder_name)

    try:
        for i in list(vk_client.photo_info(owner_id).values()):  # Получаем необходимые данные с VK
            count += 1
            log_dict = {}
            size = i['type']
            file_in = i['url_max']  # Полученные ссылки на фотографии
            date_photo = datetime.fromtimestamp(i['date_photo']).strftime("%d_%b_%Y_%I_%M_%S")
            file_out = folder_name + '/' + str(date_photo) + '.jpeg'
            #  Отправляем фотографии на Яндекс
            result = uploader.upload(file_in, file_out)
            #  Готовим иноформацию для записи в лог
            log_dict['file_name'] = str(date_photo) + '.jpeg'
            log_dict['size'] = size
            log.append(log_dict)
    except Exception as error:
        return 'Убедитесь в верном токене. {error}'

    print()
    vk_client.write_log(log)
    if result:
        print(f'{count} фотографий с аккаунта VK успешно загружено на аккаунт Яндекс в папку {folder_name}')


if __name__ == "__main__":
    #  Создаем экземпляр класса VKUser()
    vk_client = VKUser()

    #  Создаем экземпляр класса YaUploader()
    uploader = YaUploader()

    run_copy()
