# Cкрипт скачивает альбомы с фотографиями во всех имеющихся размерах, включая и технические альбомы:
#       - фотографии профиля
#       - фотографии со стены пользователя
#       - сохраненные фотографии
#       - фотографии с пользователем
#
#       Если скачиваются обычные альбомы, то мы получаем и сохраняем информацию по альбому (заголовок и описание)
#       По каждой фотографии сохраняется исходный URL, и, если есть: комментарий-описание и координаты
#
#
#
# Само скачивание взято у https://proglib.io/p/python-vk-api-1/ , но переделано под другую библиотеку и добавлены другие опции по VK API и просто удобные для работы
# NB можно попробовать переделать на https://pypi.org/project/vk-requests/ https://github.com/prawn-cake/vk-requests
# TODO:
# - в служебных альбомах добавить соответствующий заголовок (c запросом информации по пользователю/группе (?)
# + в фото с пользователем, видимо, информацию по альбомам откуда фото фзяты (?)
# + сохранение всей информации в файл (html ? тогда с тубнейлами? что под них использовать?)
# + получение первичных данных из диалога (?) и хранение (? или удаление после использования) в ini-файле (?)
# + в диалоге же выдаем информацию об обозначении служебных каталогов



'''
Используется VK API метод photos.getAlbums
https://vk.com/dev/photos.getAlbums

###
Используется VK API метод photos.get
https://vk.com/dev/photos.get

###
Используется VK API метод photos.getUserPhotos
https://vk.com/dev/photos.getUserPhotos

Требуемые библиотеки:
sudo pip3 install vk_requests

sudo pip3 install yattag # http://www.yattag.org
'''



# Импортируем нужные модули
from urllib.request import urlretrieve

from yattag import Doc, indent # библиотека для формирования HTML http://www.yattag.org

import vk_requests, os, time, math, configparser

class getPhotos():
    """
    Класс для скачивания фотографий из албомов VK
    """

    def __init__(self, configfile='settings.ini',rewrite=False):
        """ Inits
        """

        if not os.path.exists(configfile):
            self.__createConfig(configfile)
        if rewrite == True:
            self.__createConfig(configfile)

        config = configparser.ConfigParser()
        config.read(configfile)

        # Читаем некоторые значения из конфиг. файла.
        #self.__version_n = config.get("Settings", "version_n") # версия API VK


        self.__in_dir = config.get("Settings", "in_dir") # каталог для скачивания фото
        if config.has_option("Settings", "login"):
            self.__login = config.get("Settings", "login")
        else:
            self.__login = ''

        if config.has_option("Settings", "password"):
            self.__password = config.get("Settings", "password")
        else:
            self.__password = ''

        self.__vk_id = config.get("Settings", "vk_id")
        self.__service_token = config.get("Settings", "service_token")

        self.__version_n = "5.78"
        self.__scope = 'photos'

        self.__getAl()

    def __createConfig(self, configfile):
        """
        Create a config file
        """

        config = configparser.ConfigParser()
        config.add_section("Settings")
        #config.set("Settings", "version_n", "5.78")
        in_dir = input("Имя каталога для ввода данных (если saved - просто нажмите на Enter): ")
        if in_dir=='':
            in_dir = 'saved'
        config.set("Settings", "in_dir", in_dir)

        vk_id = input("ID зарегистрированного на сайте Vk приложения: ")
        config.set("Settings", "vk_id", vk_id)

        service_token = input("Token, полученный для зарегистрированного на сайте Vk приложения: ")
        config.set("Settings", "service_token", service_token)

        login  = input("login для vk (если пропускаем - нажмите на Enter): ")
        if login != '':
            config.set("Settings", "login", login)
        password = input("пароль пользователя для vk (если пропускаем - нажмите на Enter)")
        if password != '':
            config.set("Settings", "password", password)

        with open(configfile, "w") as config_file:
            config.write(config_file)

    def __getAl(self):
        """
        Получаем задачу и разбираемся с ней первично
        """
        version_n = self.__version_n #'5.78'  # версия API VK
        in_dir =  self.__in_dir                   #'saved'  # каталог для скачивания фото

        login = self.__login
        password = self.__password
        vk_id = self.__vk_id

        token = self.__service_token #'cc13c81fcc13c81fcc13c81f37cc71c76eccc13cc13c81f96a9e7d32caf1e3b37bd51a4'
        scope = self.__scope #'photos'

        if login=='':
            print ('No login')
            vkapi = vk_requests.create_api(app_id=vk_id,service_token=token, scope=scope,api_version=version_n)
        else:
            print('Login')
            vkapi = vk_requests.create_api(app_id=vk_id,login=login,password=password,scope=scope,api_version=version_n)
        print("Введите url альбома \nнапример: https://vk.com/album2309870_259395754\nЕсли Вам нужно скачать фотографии профиля,\nфото со стены пользователя,\nсохраненные фотографии пользователя,\nили фотографии с пользователем\n")
        print("введите соответственно \nhttps://vk.com/album1234567_0 - фотографии профиля,\nhttps://vk.com/album1234567_00 - фото со стены пользователя,\nhttps://vk.com/album1234567_000 - сохраненные фотографии пользователя,\nhttps://vk.com/album1234567_0000 -  фотографии с пользователем\n")
        print("где вместо 12345 нужно ввести настойщий ID пользователя\n")
        url = input("Введите url альбома:") ## 'https://vk.com/album2309870_250605103' ##

        # Разбираем ссылку
        try:
            album_id = url.split('/')[-1].split('_')[1]
        except Exception:
            print('Произошла ошибка в определении ID альбома')
            exit(0)
        self.albumUrl = url
        ## NB album_id - идентификатор альбома. Для служебных альбомов используются следующие идентификаторы:
        ## wall — фотографии со стены; https://vk.com/album2309870_00
        ## profile — фотографии профиля; https://vk.com/album2309870_0
        ## saved — сохраненные фотографии. url - https://vk.com/album2309870_000
        ## строка
        real_album = 1
        if album_id == '0':
            album_id = 'profile'
            real_album = 0
        if album_id == '00':
            album_id = 'wall'
            real_album = 0
        if album_id == '000':
            album_id = 'saved'
            real_album = 0
        if album_id == '0000':  # псевдономер -тут будет использоваться другой метод (photos.getUserPhotos, а не photos.get)
            album_id = 'UserPhotos'
            real_album = 0
            self.albumUrl = ''

        owner_id = url.split('/')[-1].split('_')[0].replace('album', '')

        self.__getAlPhotoFromAlbum(vkapi, owner_id, album_id, real_album)

    def __getAlPhotoFromAlbum(self, vkapi, owner_id,album_id,real_album):

        """
        Получаем все фотографии альбома
        """

        version_n = self.__version_n  # '5.78'  # версия API VK
        in_dir = self.__in_dir  # 'saved'  # каталог для скачивания фото

        photos_count = vkapi.photos.getAlbums(owner_id=owner_id, album_ids=album_id, v=version_n)['items'][0]['size']

        counter = 0  # текущий счетчик
        prog = 0  # процент загруженных
        breaked = 0  # не загружено из-за ошибки
        time_now = time.time()  # время старта
        tmpResult = ''
        album_title = ''
        album_description = ''
        # Создадим каталоги
        if not os.path.exists(in_dir):
            os.mkdir(in_dir)
        photo_folder = '{0}/album{1}_{2}'.format(in_dir, owner_id, album_id)
        if not os.path.exists(photo_folder):
            os.mkdir(photo_folder)

        for j in range(math.ceil(
                        photos_count / 1000)):  # Подсчитаем сколько раз нужно получать список фото, так как число получится не целое - округляем в большую сторону
            try:
                if album_id == 'UserPhotos':
                    photos = vkapi.photos.getUserPhotos(user_id=owner_id, count=1000, offset=j * 1000, v=version_n,
                                                        extended=1)  # Получаем список фото
                else:
                    if real_album == 1:
                        albums = vkapi.photos.getAlbums(owner_id=owner_id, album_ids=album_id, v=version_n)
                        for album in albums['items']:
                            album_description = album['description']
                            album_title = album['title']
                            print('Альбом: %s' % (album_title))
                            print('Описание альбома: %s ' % (album_description))
                    photos = vkapi.photos.get(owner_id=owner_id, album_id=album_id, count=1000, offset=j * 1000,
                                              v=version_n, extended=1)  # Получаем список фото
            except vk_requests.exceptions.VkAPIError as vk_error:
                # print(vk_error) error_code=7,message='Permission to perform this action is denied',request_params={'v': '5.78', 'oauth': '1', 'count': '1000', 'offset': '0', 'method': 'photos.getUserPhotos', 'user_id': 'номер'}
                error_code = vk_error.error_data['error_code']
                error_msg = vk_error.error_data['error_msg']
                print('Что-то пошло не так :( Код ошибки: ', error_code, ', сообщение: ', error_msg)
                # print(vk_error.error_data) {'request_params': [{'key': 'oauth', 'value': '1'}, {'key': 'method', 'value': 'photos.getUserPhotos'}, {'key': 'offset', 'value': '0'}, {'key': 'v', 'value': '5.78'}, {'key': 'user_id', 'value': 'номер'}, {'key': 'count', 'value': '1000'}], 'error_code': 7, 'error_msg': 'Permission to perform this action is denied'}
                exit()

            for photo in photos['items']:
                counter += 1
                photoNmaes = []
                preview = ''
                # print(photo)

                # "id": 456242737,
                # "album_id": 259226725,
                # "owner_id": 2309870,

                photo_url = 'https://vk.com/photo%s_%s' % (photo['owner_id'], photo['id'])

                photo_text = ''
                photo_lat = ''
                photo_long = ''

                if 'text' in photo:
                    photo_text = photo['text']
                if 'lat' in photo:
                    photo_lat = photo['lat']
                if 'long' in photo:
                    photo_long = photo['long']

                print('Фото %s %s  подпись: %s ' % (
                counter, photo_url, photo_text))

                if photo_lat != '' and photo_long != '':
                    print('Координаты: %s,%s' % (photo_lat, photo_long))


                for photo_in in photo['sizes']:
                    photo_width = photo_in['width']
                    photo_height = photo_in['height']
                    photo_folder_in = '{0}/{1}'.format(photo_folder, photo_width)
                    photo_folder_in_in = '{0}'.format(photo_width)
                    if not os.path.exists(photo_folder_in):
                        os.mkdir(photo_folder_in)

                    url = photo_in['url']
                    fname = photo_folder_in_in + "/" + os.path.split(url)[1];
                    if not os.path.exists(photo_folder_in + "/" + os.path.split(url)[1]):

                        print(
                            'Загружаю фото № {} из {} размером {}x{}.  url: {} Загружаем в: {}/{} Прогресс: {} '.format(
                                counter, photos_count, photo_width, photo_height, url, photo_folder_in,
                                os.path.split(url)[1], prog))
                        prog = round(100 / photos_count * counter, 2)
                        try:
                            urlretrieve(url,photo_folder_in + "/" + os.path.split(url)[1])  # Загружаем и сохраняем файл
                            photoNmaes.append(fname)
                            if photo_width==200:
                                preview = fname
                        except Exception:
                            print('Произошла ошибка, файл пропущен.')
                            breaked += 1
                            continue
                    else:
                        photoNmaes.append(fname)
                        if photo_width == 200:
                            preview = fname
                tmpResult += self.prepareHtml(photo_url, photo_text, photo_lat, photo_long,preview,photoNmaes)
        time_for_dw = time.time() - time_now
        print(
            "\nВ очереди было файлов: {}. Из них удачно загружено файлов: {}, {} не удалось загрузить. Затрачено времени: {} сек.\n\n".format(
                photos_count, photos_count - breaked, breaked, round(time_for_dw, 1)))

        resHtml = self.doHtml(self.albumUrl,album_title, album_description,tmpResult)
        #print(resHtml)
        fpath = photo_folder+"/index.html"
        f = open(fpath, 'w')
        f.write(resHtml)
        f.close()

    def prepareHtml(self,photo_url,photo_text,photo_lat,photo_long,preview,photoNmaes):
        #from yattag import Doc
        #from yattag import indent

        doc, tag, text, line = Doc().ttl()
        print(photoNmaes)
        with tag('h2'):
            with tag('a', target="_blank", href=photo_url):
                text(photo_url)
        if preview!='':
            #doc.asis('<img src="'+preview+'"/>')
            doc.stag('img', src=preview, klass="photo")
        else:
            #doc.asis('<img src="' + photoNmaes[0] + '"/>')
            doc.stag('img', src=photoNmaes[0], klass="photo")
        if photo_text!='':
            with tag ('br'):
                text(photo_text)
        if photo_lat!='':
            with tag ('br'):
                text('Координаты: '+photo_lat,photo_long)
        with tag('ul', id='grocery-list'):
            for photo in photoNmaes:
                with tag('li'):
                    with tag('a',href=photo, klass="photoA", target="_blank"):
                        text(photo)
        doc.stag('hr')
        result = indent(
            doc.getvalue(),
            indentation='    ',
            newline='\r\n',
            indent_text=True
        )
        return (result)

    def doHtml(self, url, album_title, album_description, tmpHtml):
        #from yattag import Doc
        #from yattag import indent

        doc, tag, text, line = Doc().ttl()

        if url=='':
            album_title = 'Фотографии с пользователем'

        doc.asis(
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
        with tag('html'):
            with tag('head'):
                with tag ('title'):
                    text(album_title)
                doc.asis('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>')
            with tag('body'):
                with tag('h1'):
                    text(album_title)
                    with tag('a', target="_blank", href=url):
                        text(url)
                if(album_description!=''):
                    with tag('p'):
                        album_description
                doc.asis(tmpHtml)

        # result = indent(doc.getvalue())
        result = indent(
            doc.getvalue(),
            indentation='    ',
            newline='\r\n',
            indent_text=True
        )
        # print(doc.getvalue())
        #print(result)
        return result

if __name__ == "__main__":
    path = "settings.ini"
    getPhotos(path,False)




