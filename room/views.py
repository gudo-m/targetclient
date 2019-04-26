from .models import VKGroup, VKComment, VKSpamDialog, VKSpamDialogMessage, VKClient
from accounts.views import add_action, notify, check_action
from accounts.views import get_default_text, normalize_num_texts, get_random_vk_api
from .models import VKToken, VKAccount, VKApiApplication, UserAction
from accounts.models import SiteSettings, UserPlan, UserSpamText
from mysite.settings import DEFAULT_SITE_ID
from multiprocessing import Process
from urllib.parse import urlparse
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.paginator import Paginator
import time
import datetime
import pytz
import random
import calendar
import uuid
import vk
site_settings = SiteSettings.objects.get(char_id=DEFAULT_SITE_ID)


def main(request):
    """Мой профиль"""
    data = {'room': True}  # данные
    if not request.user.is_authenticated:  # проверка на авторизацию
        return HttpResponseRedirect('/')
    if request.user.is_staff:  # админ
        data['admin'] = True
    if not request.user.settings.confirmed:  # если юзер не подтвердил свою почту
        data['errors'] = [
            'Для полного доступа подтвердите свой EMAIL.'
            ' Если не можете найти письмо, обязательно проверьте папку "СПАМ"!'
        ]

    data['left_days'] = '∞'

    return render(request, 'room/main.html', data)


def roots(request, page_num=1):
    """Источники"""
    data = {'room': True}  # данные
    # если юзер не авторизован
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если юзер не подтвердил почту
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # админ
    if request.user.is_staff:
        data['admin'] = True
    # берём группы (истоники) юзера
    groups = VKGroup.objects.filter(user=request.user)
    # добавляем пагинацию
    current_page = Paginator(groups, per_page=10)
    # закидываем на |сайт
    data['groups'] = current_page.page(page_num)
    return render(request, 'room/roots.html', data)


def add_group(request):
    """Добавление источника, на клиенте отправляется ajax запрос сюда"""
    # если не авторизован юзер
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если юзер
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # если гет
    if request.GET:

        def get_group_info(vk_group, user, is_last, vk_api):
            """Функция парсит группу"""
            # берём название группы
            title = vk_group['name']
            # берём айди
            group_id = vk_group['gid']
            # фотку
            image = vk_group['photo']

            # берём колво подписчиков
            num_members = vk_api.groups.getMembers(group_id=group_id)['count']
            # создаем группу
            group = VKGroup.objects.create(
                title=title,
                group_id=group_id,
                image=image,
                num_members=num_members,
                user=user
            )
            # строка-список подписчиков
            members_ids = ''
            # флаг, показывающий, завершён ли парсинг подписчиков
            flag = False
            # сколько попыток
            i = 0
            # инфа об ощибке
            error_info = None
            # пока не распарсится
            while not flag:
                # пробуем распарсить
                try:
                    # проходим по колву подписчиков
                    for offset in range(1, num_members, 1000):
                        # спим перед каждым запросом
                        time.sleep(2)
                        # проходим по айдишникам
                        for id in vk_api.groups.getMembers(group_id=group_id, offset=offset)['users']:
                            # добавляем к общему списку
                            members_ids += 'id' + str(id)
                    # после всего парсинга флаг на тру
                    flag = True
                # если при парсинге возникла ошибка
                except Exception as e:
                    # флаг на ноль
                    flag = False
                    # сохраняем инфу об ошибке
                    error_info = e
                # если уже более 10 попыток было
                if i > 10 and not flag:
                    # сообщаем об ошибке
                    text = 'Сервер не смог обработать источник с ID club' + str(
                        group_id) + '. Информация об ошибке:\n'+str(error_info)

                    notify(
                        to_email=user.email,
                        title='Обработка источников завершена',
                        text=text,
                        user=user
                    )

                    # удаляем группу
                    group.delete()
                    # завершаем парсинг
                    break
            if is_last:
                text = 'Обработка источников успешно завершена!'
                notify(
                    to_email=user.email,
                    title='Обработка источников завершена',
                    text=text,
                    user=user
                )
            # в бд всё записываем
            group.members_ids = members_ids
            group.save()

        # берём айдишники, введённые юзером
        gids = request.GET['group_id'].split()

        # если недавно был такой запрос
        if not check_action(site_settings.action_type_add_group.char_id, 70, request.user):
            return HttpResponse("many_requests", content_type='text/html')

        # проходим по айдишникам
        for i in range(len(gids)):
            # получаем айди (урл)
            gid = gids[i]

            # последний айдишник или нет
            is_last = True if i == len(gids) else False

            # пробуем распарсить урл
            try:
                # если в урле нет хттп
                if gid[:8] != 'https://' and gid[:7] != 'http://':
                    # добавляем
                    gid = 'http://'+gid
                # парсим
                o = urlparse(gid)
                # слова, используемые перед айди группы
                registered_words = ('event', 'club', 'public')
                # берём из урла айди
                gid = o.path[1:]
                # проходим по используемым словам
                for registered_word in registered_words:
                    # если в айди есть это слово
                    if gid[:len(registered_word)] == registered_word:
                        # обрезаем
                        gid = gid[len(registered_word):]
            # если возникла какая - либо ошибка
            except:
                return HttpResponse("bad", content_type='text/html')

            # берём вк апи
            vk_api = get_random_vk_api()

            # берем инфу о группе из апи
            try:
                vk_group = vk_api.groups.getById(group_ids=gid)[0]
            # если не получается
            except:
                vk_group = None

            # если не получилось
            if vk_group is None:
                # сообщаем
                text = 'Сервер не смог обработать источник с ID ' + str(gid) + '. Указан неверный ID.'

                notify(
                    to_email=request.user.email,
                    title='Ошибка при обработке источника',
                    text=text,
                    user=request.user
                )
                return HttpResponse("bad", content_type='text/html')

            # пробуем получить такую группу у юзера
            try:
                group_already_exists = VKGroup.objects.get(group_id=vk_group['gid'], user=request.user)
            # если не получыаетя то нон
            except VKGroup.DoesNotExist:
                group_already_exists = None

            # если группа уже есть у пользователя, возвращаем bad
            if group_already_exists is not None:
                return HttpResponse("bad", content_type='text/html')

            # если у юзера уже слишком много групп (ограничение по тарифу)
            if len(VKGroup.objects.filter(user=request.user)) >= request.user.settings.plan.num_groups:
                return HttpResponse('too_many_groups', content_type='text/html')

            # если в группе слишком много подписчиков (ограничение по тарифу)
            if int(vk_api.groups.getMembers(group_id=gid)['count']) > int(request.user.settings.plan.max_group_size):
                return HttpResponse("too_big", content_type='text/html')

            # добавляем действие
            add_action(
                'Отправил запрос на обработку источника',
                site_settings.action_type_add_group.char_id,
                request.user
            )

            text = 'Сервер начал обрабатывать источник с ID '\
                   + gid + '!\nПо завершению вам придёт письмо, вкладку в браузере можно закрыть.'

            # письмо
            notify(
                to_email=request.user.email,
                title=site_settings.action_type_add_group.name,
                text=text,
                user=request.user
            )

            # если же всё нормально, берём инфу
            process = Process(target=get_group_info, args=(vk_group, request.user, is_last, vk_api,))
            process.start()
        return HttpResponse("started", content_type='text/html')


def delete_group(request, gr_id=None):
    """Удаление группы, ajax запрос"""
    # пробуем получить группу
    try:
        group_will_deleted = VKGroup.objects.get(group_id=str(gr_id), user=request.user)
    # Если такой нет - нон
    except VKGroup.DoesNotExist:
        group_will_deleted = None
    # если группу получили
    if group_will_deleted is not None:
        # удаляем
        group_will_deleted.delete()

        # добавляем действие
        add_action(
            'Удалил источник с ID='+str(gr_id),
            site_settings.action_type_delete_group.char_id,
            request.user
        )
    # если группу не получили
    else:
        # пишем бэд
        return HttpResponse("bad", content_type='text/html')
    # если всё ок - ок
    return HttpResponse("ok", content_type='text/html')


def delete_client(request, uid=None):
    """Удаление клиента, ajax запрос"""
    # получаем айди группы
    gr_id = request.GET['gr_id']
    # получаем саму группу
    group = VKGroup.objects.get(group_id=gr_id, user=request.user)
    # пробуем получить самого клиента
    try:
        users_client = VKClient.objects.get(user=request.user, client_id=uid, group=group)
    # если никак то нон
    except VKClient.DoesNotExist:
        users_client = None
    # если не нон
    if users_client is not None:
        # удаляем
        users_client.delete()
    # если нон
    else:
        # бэд
        return HttpResponse("bad", content_type='text/html')
    # если всё ок - ок
    return HttpResponse("ok", content_type='text/html')


def check_roots(request):
    """Проверка источников, на клиенте отправляется ajax запрос сюда"""
    # если не авторизован
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если не подтвердил мыло
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')

    # если гет запрос
    if request.GET:

        def check_root(root, vk_api, is_last):
            """Проверяет источник"""
            # делаем айди группы валидным
            gr_id = 'club' + str(root.group_id)
            # пауза перед каждым запросом
            time.sleep(0.5)
            # строка-список айдишников
            members_ids = ''
            # строка-список новых айдишников
            new_ids = ''
            # берём старый список айдишников
            group_members_ids = root.members_ids
            # флаг говорит, выполнена ли проверка
            flag = False
            # количество попыток выполнить проверку
            i = 0
            # информация об ошибке - нон
            error_info = None
            # пока флаг не покажет, что проверка выполнена
            while not flag:
                # пробуем обработать
                try:
                    # берём колво подписчиков
                    num_members = vk_api.groups.getMembers(group_id=gr_id[4:])['count']
                    # проходим по колву подписчиков
                    for offset in range(1, num_members, 1000):
                        # перед запросом спим 2 секунды
                        time.sleep(2)
                        # проходим по айдишникам
                        for id in vk_api.groups.getMembers(group_id=gr_id[4:], offset=offset)['users']:
                            # добавляем в список
                            members_ids += 'id' + str(id)
                            #  если такого айди в бд не было добавляем ещё и отдельно
                            if ('id' + str(id)) not in group_members_ids:
                                new_ids += 'id' + str(id)
                    # после сбора инфы сохраняем её
                    root.members_ids = str(members_ids)
                    root.num_members = str(num_members)
                    # обрабатываем айдишники, которых не было в бд:
                    for us_id in new_ids.split('id')[1:]:
                        # если это админ
                        if str(us_id) == '101':
                            # пропускаем
                            continue
                        # перед запросом спим
                        time.sleep(0.3)
                        # получаем инфу о клиенте
                        client_vk = vk_api.users.get(
                            user_ids=[str(us_id)],
                            fields=('photo_100', 'first_name', 'last_name', 'deactivated')
                        )[0]
                        # если заблочен
                        if 'deactivated' in client_vk:
                            # пропуск
                            continue
                        # пробуем получить такого клиента
                        try:
                            object_exists = VKClient.objects.get(user=request.user, client_id=us_id, group=root)
                        # если не получается то нон
                        except VKClient.DoesNotExist:
                            object_exists = None
                        # если не нон
                        if object_exists is not None:
                            # пропуск
                            continue
                        # создаем клиента
                        VKClient.objects.create(
                            client_id=us_id,
                            group=root,
                            user=request.user,
                            photo=client_vk['photo_100'],
                            fname=client_vk['first_name'],
                            lname=client_vk['last_name']
                        )

                    # проходим по записям источника
                    for pid in vk_api.wall.get(owner_id=-int(gr_id[4:]), count=10)[1:]:
                        # получаем айди записи
                        pid = pid['id']
                        # перед запросом спим
                        time.sleep(2)
                        # получаем комменты поста
                        returned_comments = vk_api.wall.getComments(
                            owner_id=-int(gr_id[4:]),
                            post_id=pid,
                            count=100
                        )
                        # проходим по комментам
                        for comment in returned_comments[1:]:
                            # если коммент от админа
                            if str(comment['uid']) == '101':
                                # пропускаем
                                continue
                            # перед запросом спим
                            time.sleep(0.3)
                            # получаем комментатора
                            user_vk = vk_api.users.get(
                                user_ids=[str(comment['uid'])],
                                fields=('photo_100', 'first_name', 'last_name', 'deactivated')
                            )[0]
                            # если он заблочен
                            if 'deactivated' in user_vk:
                                # пропускаем
                                continue
                            # проверяем, нет ли уже такого комментария в базе:
                            try:
                                comment_exists = VKComment.objects.get(
                                    text=comment['text'],
                                    user=request.user,
                                    group=root,
                                    uid=comment['uid']
                                )
                            # если не существует то нон
                            except VKComment.DoesNotExist:
                                comment_exists = None
                            # если не существует
                            if comment_exists is None:
                                # создаем
                                VKComment.objects.create(
                                    text=comment['text'],
                                    user=request.user,
                                    group=root,
                                    fname=user_vk['first_name'],
                                    lname=user_vk['last_name'],
                                    photo=user_vk['photo_100'],
                                    uid=comment['uid']
                                )
                    # если всё получилось - ставим флаг
                    flag = True
                # если при обработке ошибка
                except Exception as e:
                    # флаг на фолз
                    flag = False
                    # инфу об ошибке сохраняем
                    error_info = e
                # если уже больше 10 попыток
                if not flag and i > 10:
                    text = 'При проверке источников возникла неизвестная ошибка.\n' \
                           'Информация об ошибке:\n' + str(error_info)
                    # письмо
                    notify(
                        to_email=request.user.email,
                        title='Проверка источников',
                        text=text,
                        user=request.user
                    )
                    return HttpResponse('bad', content_type='text/html')
                # после каждого раза прибавляем 1
                i += 1
            # после парсинга сохраняем
            root.save()
            # если это была последняя группа
            if is_last:
                text = 'Проверка источников успешно завершена!'
                # письмо
                notify(
                    to_email=request.user.email,
                    title=site_settings.action_type_check_roots.name,
                    text=text,
                    user=request.user
                )

        # получаем список групп юзера
        users_roots = VKGroup.objects.filter(user=request.user)
        # если таковых нет, сообщаем пользователю
        if users_roots is None or len(users_roots) == 0:
            return HttpResponse("no_roots", content_type='text/html')

        # если недавно был такой запрос
        if not check_action(site_settings.action_type_check_roots.char_id, 320, request.user):
            return HttpResponse("many_requests", content_type='text/html')

        # добавляем действие
        add_action(
            'Отправил запрос на проверку источников',
            site_settings.action_type_check_roots.char_id,
            request.user
        )

        text = 'Проверка источников началась, по завершению мы вам отправим письмо.'
        # письмо
        notify(
            to_email=request.user.email,
            title=site_settings.action_type_check_roots.name,
            text=text,
            user=request.user
        )

        # берём вк апи
        vk_api = get_random_vk_api()

        # проходим по группам
        for i in range(len(users_roots)):
            # получаем группу
            root = users_roots[i]
            # последний айдишник или нет
            is_last = True if i == len(users_roots) else False
            # создаем процесс
            proc = Process(target=check_root, args=(root, vk_api, is_last))
            proc.start()
            time.sleep(0.5)

        # всё ок
        return HttpResponse('ok', content_type='text/html')


def comments(request, page_num=1):
    """Выводит комменты"""
    data = {'room': True}  # данные
    # если юзер не авторизован
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если юзер не подтвердил мыло
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # если админ
    if request.user.is_staff:
        data['admin'] = True
    # берём комментарии у юзера
    comments = VKComment.objects.filter(user=request.user).order_by('-selected', '-visited', '-id')
    # пагинируем их
    current_page = Paginator(comments, per_page=10)
    # добавляем в данные
    data['comments'] = current_page.page(page_num)
    # список текстов, которые нужно скопировать
    data['texts'] = []
    # берём текст для спама юзера
    user_text = get_default_text(request.user)
    # проходим по комментам
    for comment in data['comments']:
        # копируем текст для спама
        msg_text_updtd = user_text.spam_text[:]
        # делаем вставки
        while '<фамилия>' in msg_text_updtd:
            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<фамилия>')]\
                             + comment.lname\
                             + msg_text_updtd[msg_text_updtd.index('<фамилия>') + len('<фамилия>'):]
        while '<имя>' in msg_text_updtd:
            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<имя>')]\
                             + comment.fname\
                             + msg_text_updtd[msg_text_updtd.index('<имя>') + len('<имя>'):]
        while '<группа>' in msg_text_updtd:
            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<группа>')]\
                             + comment.group.title\
                             + msg_text_updtd[msg_text_updtd.index('<группа>') + len('<группа>'):]
        # добавляем в список
        data['texts'].append({'id': str(comment.id), 'msg': msg_text_updtd})
    return render(request, 'room/comments.html', data)


def clients(request, page_num=1):
    """Выводит клиентов"""
    data = {'room': True}  # данные
    # если не авторизован
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если не подтвердил почту
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # админ
    if request.user.is_staff:
        data['admin'] = True
    # берем клиентов юзера
    clients = VKClient.objects.filter(user=request.user).order_by('-selected', '-visited', '-id')
    # пагинируем
    current_page = Paginator(clients, per_page=12)
    # пагинацию в данные
    data['clients'] = current_page.page(page_num)
    # список текстов для спама
    data['texts'] = []
    # нормализуем колво текстов
    #normalize_num_texts(request.user)
    # берём текст юзера
    user_text = get_default_text(request.user)
    # проходим по клиентам
    for client in data['clients']:
        # копируем текст
        msg_text_updtd = user_text.spam_text[:]
        # делаем вставки
        while '<фамилия>' in msg_text_updtd:
            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<фамилия>')]\
                             + client.lname\
                             + msg_text_updtd[msg_text_updtd.index('<фамилия>') + len('<фамилия>'):]
        while '<имя>' in msg_text_updtd:
            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<имя>')]\
                             + client.fname\
                             + msg_text_updtd[msg_text_updtd.index('<имя>') + len('<имя>'):]
        while '<группа>' in msg_text_updtd:
            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<группа>')]\
                             + client.group.title\
                             + msg_text_updtd[msg_text_updtd.index('<группа>') + len('<группа>'):]
        # добавляем в список текстов
        data['texts'].append({'id': str(client.id), 'msg': msg_text_updtd})
    return render(request, 'room/clients.html', data)


def spam(request):
    """Страница рассылки сообщений"""
    data = {'room': True}  # даные
    # если юзер не авторизован
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если юзер не подтвердил мыло
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # если админ
    if request.user.is_staff:
        data['admin'] = True
    # аккаунты вк
    data['vk_accounts'] = []
    # проходим по аккаунтам вк
    for vk_account in VKAccount.objects.filter(user=request.user).order_by('id'):
        # добавляем в список
        data['vk_accounts'].append(vk_account)
    # проходим по количеству аккаунтов, которые доступны, но не добавлены
    for _ in range(request.user.settings.plan.num_accounts - len(data['vk_accounts'])):
        # добавляем
        data['vk_accounts'].append(False)
    return render(request, 'room/spam.html', data)


def add_vk_account(request):
    """Добавление аккаунта вк ajax"""
    # получаем логин акка
    ulogin = request.GET['ulogin']
    # пароль
    upassword = request.GET['upassword']
    # получаем вк апи
    vk_api = get_random_vk_api(vk_login=ulogin, vk_password=upassword)
    # если вк апи не удвлось получить
    if vk_api is None:
        # говорим
        return HttpResponse('bad', content_type='text/html')
    # получаем айди юзера в вк
    uid = vk_api.users.get()[0]['uid']
    # пробуем получить такой аккаунт в бд
    try:
        vk_exist = VKAccount.objects.get(aid=uid, login=ulogin, password=upassword, user=request.user)
    # если не получается - нон
    except VKAccount.DoesNotExist:
        vk_exist = None
    # если получили аккаунт
    if vk_exist is not None:
        # говорим
        return HttpResponse('exists', content_type='text/html')
    # получаем инфу об акке из вк
    a_vk = vk_api.users.get(user_ids=[str(uid)], fields=('photo_100', 'first_name', 'last_name', 'deactivated'))[0]
    # если аккаунт заблочен
    if 'deactivated' in a_vk:
        # говорим
        return HttpResponse('blocked', content_type='text/html')
    # создаем аккаунт
    VKAccount.objects.create(
        login=ulogin,
        password=upassword,
        aid=uid,
        fname=a_vk['first_name'],
        lname=a_vk['last_name'],
        photo=a_vk['photo_100'],
        num_messages=0,
        user=request.user,
        blocked=False
    )

    # добавляем действие
    add_action(
        'Добавил аккаунт вк с ID='+str(uid),
        site_settings.action_type_add_vk_account.char_id,
        request.user
    )

    text = 'Аккаунт вконтакте с ID='+str(uid)+' успешно добавлен!'
    # письмо
    notify(
        to_email=request.user.email,
        title=site_settings.action_type_add_vk_account.name,
        text=text,
        user=request.user
    )
    return HttpResponse('ok', content_type='text/html')


def delete_vk_account(request):
    """Удаление аккаунта вк ajax"""
    # получаем айди акка
    ac_id = request.GET['acc_id']
    # пробуем получить
    try:
        acc_not_exist = VKAccount.objects.get(id=ac_id, user=request.user)
    # если никак то нон
    except VKAccount.DoesNotExist:
        acc_not_exist = None
    # если получили акк
    if acc_not_exist is not None:
        # сохраняем айди
        vk_uid = acc_not_exist.aid
        # и удаляем акк
        acc_not_exist.delete()

        # добавляем действие
        add_action(
            'Удалил аккаунт вконтакте с ID='+str(vk_uid),
            site_settings.action_type_delete_vk_account.char_id,
            request.user
        )

        text = 'Аккаунт вконтакте с ID=' + str(vk_uid) + ' успешно удален.'
        # письмо
        notify(
            to_email=request.user.email,
            title=site_settings.action_type_delete_vk_account.name,
            text=text,
            user=request.user
        )

    else:
        return HttpResponse("bad", content_type='text/html')
    return HttpResponse("ok", content_type='text/html')


def start_spam(request):
    """Рассылка сообщений, ajax"""

    # выбранная опция рассылки
    selected = request.GET['selected']

    # спамить тем, кому разослано?
    spam_last = True if request.GET['spam_last'] == 'true' else False

    # Выбранный диапозон (от)
    range_from = int(request.GET['ranged_from'])*60  # sec
    # Выбранный диапозон (до, включительно)
    range_to = int(request.GET['ranged_to'])*60+1  # sec
    # в диапазоне или зафиксированное
    range_fixed = True if int(request.GET['ranged_or_diap']) == 1 else False
    # зафиксированное время
    fixed = int(request.GET['ranged'])*60  # sec

    # если что-то неправильно
    if fixed > 3600 or range_from > 3600 or range_to > 3600:
        return HttpResponse("bad", content_type='text/html')

    # сохраняем всё в бд
    request.user.settings.spam_interval = fixed
    request.user.settings.spam_range_to = range_to
    request.user.settings.spam_range_from = range_from
    request.user.settings.spam_range_or_interval = range_fixed
    request.user.settings.spam_last = spam_last
    request.user.settings.spam_selected_option = selected
    request.user.save()
    request.user.settings.save()

    if not check_action(site_settings.action_type_start_spam.char_id, 320, request.user):
        # если недавно был такой запрос
        return HttpResponse("many_requests", content_type='text/html')

    # берём вк аккаунты юзера
    accounts = VKAccount.objects.filter(user=request.user)
    # если такие есть
    if len(accounts) > 0:
        # выбираем, кому рассылать
        if selected == '1':
            receivers = VKClient.objects.filter(user=request.user)
            comments = None
        elif selected == '2':
            receivers = VKClient.objects.filter(user=request.user)
            comments = VKComment.objects.filter(user=request.user)
        elif selected == '3':
            receivers = None
            comments = VKComment.objects.filter(user=request.user)
        elif selected == '4':
            receivers = VKClient.objects.filter(user=request.user, selected=True)
            comments = None
        elif selected == '5':
            receivers = None
            comments = VKComment.objects.filter(user=request.user, selected=True)
        elif selected == '6':
            receivers = VKClient.objects.filter(user=request.user, selected=True)
            comments = VKComment.objects.filter(user=request.user, selected=True)
        else:
            receivers = None
            comments = None

        # добавляем действие
        add_action(
            'Начал рассылку сообщений',
            site_settings.action_type_start_spam.char_id,
            request.user
        )
        text = 'Рассылка сообщений началась.'
        # письмо
        notify(
            to_email=request.user.email,
            title=site_settings.action_type_start_spam.name,
            text=text,
            user=request.user
        )

        def spam_to(user, receivers, comments):
            blocked_ids = ('2052295', '116595273')
            # если нужно рассылать клиентам
            if receivers is not None:
                # проходим по ним
                for receiver in receivers:
                    # если выбран точный интервал
                    if user.settings.spam_range_or_interval:
                        # выбираем интервал
                        ranged_now = user.settings.spam_interval
                    # если выбран диапазон
                    else:
                        # выбираем из диапазона
                        ranged_now = random.randint(
                            user.settings.spam_range_from,
                            user.settings.spam_range_to
                        )
                    if str(receiver.client_id) in blocked_ids:
                        # пропускаем
                        continue
                    # если не спамить тем, кому рахослано
                    if not spam_last:
                        # если клиенту разослано
                        if receiver.spammed:
                            # пропускаем
                            continue
                        # если есть такой коммент и ему разослано
                        if len(VKComment.objects.filter(user=user, uid=receiver.client_id, spammed=True)) > 0:
                            # делаем этому клиенту разослано
                            receiver.spammed = True
                            # сохраняем
                            receiver.save()
                            # пропускаем
                            continue
                        # если есть такой клиент и ему разослано
                        if len(VKClient.objects.filter(user=user, client_id=receiver.client_id, spammed=True)) > 0:
                            # делаем этому клиенту разослано
                            receiver.spammed = True
                            # сохраняем
                            receiver.save()
                            # пропускаем
                            continue
                    # флаг указывает, отослали ему сообщение или нет
                    flag = True
                    # колво попыток
                    i = 0
                    # спим столько, сколько выбрали
                    time.sleep(ranged_now)
                    # пока не отправили сообщение
                    while flag:
                        # получаем апи
                        # получаем рандомный акк юзера
                        random_vk_acc = random.choice(VKAccount.objects.filter(user=user))
                        vk_api = get_random_vk_api(random_vk_acc.login, random_vk_acc.password)

                        # копируем рандомный текст
                        msg_text_updtd = random.choice(UserSpamText.objects.filter(user=user)).spam_text[:]

                        # делаем вставки
                        while '<фамилия>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<фамилия>')]\
                                             + receiver.lname\
                                             + msg_text_updtd[msg_text_updtd.index('<фамилия>') + len('<фамилия>'):]
                        while '<имя>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<имя>')]\
                                             + receiver.fname\
                                             + msg_text_updtd[msg_text_updtd.index('<имя>') + len('<имя>'):]
                        while '<группа>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<группа>')]\
                                             + receiver.group.title\
                                             + msg_text_updtd[msg_text_updtd.index('<группа>') + len('<группа>'):]
                        while '<br>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<br>')]\
                                             + '\n' + msg_text_updtd[msg_text_updtd.index('<br>') + len('<br>'):]

                        # пробуем отправить сообщение
                        try:
                            # пауза перед запросом
                            time.sleep(0.5)
                            # отправляем сообщение
                            message_id = vk_api.messages.send(user_id=receiver.client_id, message=msg_text_updtd)
                            # колво сообщений += 1
                            random_vk_acc.num_messages += 1
                            # акк не заблочен
                            random_vk_acc.blocked = False
                            # сохраняем
                            random_vk_acc.save()
                            # флаг показывает, что всё получилось
                            flag = False
                            # пробуем получить диалог
                            try:
                                dialog_with_this_receiver = VKSpamDialog.objects.get(
                                    user=request.user,
                                    vk_account=random_vk_acc,
                                    with_uid=receiver.client_id
                                )
                            # если не получается, создаем
                            except VKSpamDialog.DoesNotExist:
                                dialog_with_this_receiver = VKSpamDialog.objects.create(
                                    user=request.user,
                                    vk_account=random_vk_acc,
                                    with_fname=receiver.fname,
                                    with_lname=receiver.lname,
                                    with_uid=receiver.client_id,
                                    with_photo=receiver.photo,
                                    num_messages=0
                                )
                            # прибавляем к диалогу колво сообщений
                            dialog_with_this_receiver.num_messages += 1
                            # сохраняем
                            dialog_with_this_receiver.save()
                            # достаем текущую дату
                            d = datetime.datetime.now()
                            # достаем часовой пояс
                            timezone = pytz.timezone("Europe/Moscow")
                            # указываем часовой пояс
                            d = timezone.localize(d)
                            # создаем сообщение в бд
                            VKSpamDialogMessage.objects.create(
                                from_vk_account=True,
                                message_id=message_id,
                                dialog=dialog_with_this_receiver,
                                sent_at=d,
                                user=request.user,
                                body=msg_text_updtd
                            )
                            # ставим его проспамленным
                            receiver.spammed = True
                            # сохраняем
                            receiver.save()
                        # если возникла какая либо ошибка
                        except Exception as e:
                            # письмо
                            notify(
                                to_email=request.user.email,
                                title=site_settings.action_type_start_spam.name,
                                text=e,
                                user=request.user
                            )
                            # берём аккаунт вк
                            vk_acc_vk = vk_api.users.get(user_ids=[str(random_vk_acc.aid)], fields='deactivated')[0]
                            # если он заблочен
                            if 'deactivated' in vk_acc_vk:
                                # ставим заблоченным
                                random_vk_acc.blocked = True
                                # сохраняем
                                random_vk_acc.save()
                            # получаем аккаунты вк незаблоченные
                            check_block = VKAccount.objects.filter(user=request.user, blocked=False)
                            # если таких нет, говорим
                            if len(check_block) < 1:
                                text = 'Все ваши аккаунты заблокированы.'
                                # письмо
                                notify(
                                    to_email=request.user.email,
                                    title=site_settings.action_type_start_spam.name,
                                    text=text,
                                    user=request.user
                                )

                        # если было более 10 попыток, но так и не удалось отправить сообщение
                        if flag and i > 10:
                            # переходим к следующему клиенту
                            break
                        # +1 попытка
                        i += 1
            # если надо рассылать комментаторам
            if comments is not None:
                # проходим по комментам
                for comment in comments:
                    # если выбран точный интервал
                    if user.settings.spam_range_or_interval:
                        # выбираем интервал
                        ranged_now = user.settings.spam_interval
                    # если выбран диапазон
                    else:
                        # выбираем из диапазона
                        ranged_now = random.randint(
                            user.settings.spam_range_from,
                            user.settings.spam_range_to
                        )
                    if str(comment.uid) in blocked_ids:
                        # пропускаем
                        continue
                    # если не спамить тем, кому рахослано
                    if not spam_last:
                        # если клиенту разослано
                        if comment.spammed:
                            # пропускаем
                            continue
                        # если есть такой коммент и ему разослано
                        if len(VKComment.objects.filter(user=user, uid=comment.uid, spammed=True)) > 0:
                            # делаем этому клиенту разослано
                            comment.spammed = True
                            # сохраняем
                            comment.save()
                            # пропускаем
                            continue
                        # если есть такой клиент и ему разослано
                        if len(VKClient.objects.filter(user=user, client_id=comment.uid, spammed=True)) > 0:
                            # делаем этому клиенту разослано
                            comment.spammed = True
                            # сохраняем
                            comment.save()
                            # пропускаем
                            continue
                    # флаг указывает, отослали ему сообщение или нет
                    flag = True
                    # колво попыток
                    i = 0
                    # спим столько, сколько выбрали
                    time.sleep(ranged_now)
                    # пока не отправили сообщение
                    while flag:
                        # получаем апи
                        # получаем рандомный акк юзера
                        random_vk_acc = random.choice(VKAccount.objects.filter(user=user))
                        vk_api = get_random_vk_api(random_vk_acc.login, random_vk_acc.password)

                        # копируем рандомный текст
                        msg_text_updtd = random.choice(UserSpamText.objects.filter(user=user)).spam_text[:]

                        # делаем вставки
                        while '<фамилия>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[
                                             :msg_text_updtd.index('<фамилия>')]\
                                             + comment.lname\
                                             + msg_text_updtd[msg_text_updtd.index('<фамилия>') + len('<фамилия>'):]
                        while '<имя>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[
                                             :msg_text_updtd.index('<имя>')]\
                                             + comment.fname\
                                             + msg_text_updtd[msg_text_updtd.index('<имя>') + len('<имя>'):]
                        while '<группа>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[
                                             :msg_text_updtd.index('<группа>')]\
                                             + comment.group.title\
                                             + msg_text_updtd[msg_text_updtd.index('<группа>') + len('<группа>'):]
                        while '<br>' in msg_text_updtd:
                            msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<br>')]\
                                             + '\n' + msg_text_updtd[msg_text_updtd.index('<br>') + len('<br>'):]

                            # пробуем отправить сообщение
                            try:
                                # пауза перед запросом
                                time.sleep(0.5)
                                # отправляем сообщение
                                message_id = vk_api.messages.send(user_id=comment.uid, message=msg_text_updtd)
                                # колво сообщений += 1
                                random_vk_acc.num_messages += 1
                                # акк не заблочен
                                random_vk_acc.blocked = False
                                # сохраняем
                                random_vk_acc.save()
                                # флаг показывает, что всё получилось
                                flag = False
                                # пробуем получить диалог
                                try:
                                    dialog_with_this_receiver = VKSpamDialog.objects.get(
                                        user=request.user,
                                        vk_account=random_vk_acc,
                                        with_uid=comment.uid
                                    )
                                # если не получается, создаем
                                except VKSpamDialog.DoesNotExist:
                                    dialog_with_this_receiver = VKSpamDialog.objects.create(
                                        user=request.user,
                                        vk_account=random_vk_acc,
                                        with_fname=comment.fname,
                                        with_lname=comment.lname,
                                        with_uid=comment.uid,
                                        with_photo=comment.photo,
                                        num_messages=0
                                    )
                                # прибавляем к диалогу колво сообщений
                                dialog_with_this_receiver.num_messages += 1
                                # сохраняем
                                dialog_with_this_receiver.save()
                                # достаем текущую дату
                                d = datetime.datetime.now()
                                # достаем часовой пояс
                                timezone = pytz.timezone("Europe/Moscow")
                                # указываем часовой пояс
                                d = timezone.localize(d)
                                # создаем сообщение в бд
                                VKSpamDialogMessage.objects.create(
                                    from_vk_account=True,
                                    message_id=message_id,
                                    dialog=dialog_with_this_receiver,
                                    sent_at=d,
                                    user=request.user,
                                    body=msg_text_updtd
                                )
                                # ставим его проспамленным
                                comment.spammed = True
                                # сохраняем
                                comment.save()
                            # если возникла какая либо ошибка
                            except Exception as e:
                                # письмо
                                notify(
                                    to_email=request.user.email,
                                    title=site_settings.action_type_start_spam.name,
                                    text=e,
                                    user=request.user
                                )
                                # берём аккаунт вк
                                vk_acc_vk = vk_api.users.get(user_ids=[str(random_vk_acc.aid)], fields='deactivated')[0]
                                # если он заблочен
                                if 'deactivated' in vk_acc_vk:
                                    # ставим заблоченным
                                    random_vk_acc.blocked = True
                                    # сохраняем
                                    random_vk_acc.save()
                                # получаем аккаунты вк незаблоченные
                                check_block = VKAccount.objects.filter(user=request.user, blocked=False)
                                # если таких нет, говорим
                                if len(check_block) < 1:
                                    text = 'Все ваши аккаунты заблокированы.'
                                    # письмо
                                    notify(
                                        to_email=request.user.email,
                                        title=site_settings.action_type_start_spam.name,
                                        text=text,
                                        user=request.user
                                    )

                            # если было более 10 попыток, но так и не удалось отправить сообщение
                            if flag and i > 10:
                                # переходим к следующему клиенту
                                break
                            # +1 попытка
                            i += 1

            text = 'Рассылка сообщений завершена!'
            # письмо
            notify(
                to_email=request.user.email,
                title=site_settings.action_type_start_spam.name,
                text=text,
                user=request.user
            )
            return True

        # запускаем процесс
        proc = Process(target=spam_to, args=(request.user, receivers, comments))
        proc.start()

        # и говорим, что он запущен
        return HttpResponse("started", content_type='text/html')
    # если нет аккаунтов для рассылки
    else:
        # бэд
        return HttpResponse("bad", content_type='text/html')


def select_client(request):
    """Выбор клиента"""
    # получаем айди клиента
    c_id = request.GET['c_id']
    # пробуем получить
    try:
        client = VKClient.objects.get(client_id=c_id, user=request.user)
    # если не получается
    except VKClient.DoesNotExist:
        # говорим
        return HttpResponse("bad", content_type='text/html')
    # если он уже выбран
    if client.selected:
        # убираем
        client.selected = False
    # если не выбран
    else:
        # ставим
        client.selected = True
    # сохраняем
    client.save()
    return HttpResponse("ok", content_type='text/html')


def history(request):
    """История действий"""
    data = {}  # данные
    # если юзер не авторизован
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если не подтвердил мыло
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # админ
    if request.user.is_staff:
        data['admin'] = True
    # действия юзера последние 100
    data['actions'] = UserAction.objects.filter(user=request.user).order_by('-id')[:100]
    return render(request, 'room/history.html', data)


def delete_comment(request):
    """Удаление комментария ajax"""
    # получаем айди коммента
    cid = request.GET['cid']
    # пробуем получить коммент
    try:
        comment_exists = VKComment.objects.get(user=request.user, id=cid)
    # если не существует
    except VKComment.DoesNotExist:
        # говорим
        return HttpResponse("bad", content_type='text/html')
    # если существует
    if comment_exists is not None:
        # удаляем
        comment_exists.delete()

        # добавляем действие
        add_action(
            'Удалил комментарий',
            site_settings.action_type_delete_comment.char_id,
            request.user
        )

        text = 'Комментарий успешно удален.'
        # письмо
        notify(
            to_email=request.user.email,
            title=site_settings.action_type_delete_comment.name,
            text=text,
            user=request.user
        )

        return HttpResponse('ok', content_type='text/html')


def select_comment(request):
    """Выбор комментария ajax"""
    # получаем айди коммента
    cid = request.GET['cid']
    # пробуем получить коммент
    try:
        comment_exists = VKComment.objects.get(user=request.user, id=cid)
    # если никак
    except VKComment.DoesNotExist:
        # говорим
        return HttpResponse("bad", content_type='text/html')
    # если получили коммент
    if comment_exists is not None:
        # если коммент выделен
        if comment_exists.selected:
            # убираем выделение
            comment_exists.selected = False
        # если коммент не выделен
        else:
            # выделяем
            comment_exists.selected = True
        # сохраняем
        comment_exists.save()
        return HttpResponse('ok', content_type='text/html')


def dialogs(request, vk_acc_id=None, page_num=1):
    """Вывод диалогов аккаунта"""
    data = {}  # данные
    # если не авторизован юзер
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если юзер не подтвердил мыло
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # админ
    if request.user.is_staff:
        data['admin'] = True
    # берём вк аккаунт
    data['vk_account'] = VKAccount.objects.get(user=request.user, id=vk_acc_id)
    # получаем диалоги аккаунта
    dialogs = VKSpamDialog.objects.filter(user=request.user, vk_account=data['vk_account']).order_by('-id')
    # пагинируем
    current_page = Paginator(dialogs, per_page=10)
    # передаем пагинацию юзеру
    data['dialogs'] = current_page.page(page_num)
    # список информации о диалоге
    data['dialogs_info'] = []
    # проходим по выбранным диалогам
    for dialog in current_page.page(page_num):
        # пробуем получить последнее сообщение
        try:
            last_mess = VKSpamDialogMessage.objects.filter(mdialog=dialog, user=dialog.user).order_by('-sent_at')[0]
        # если там нет последнего
        except:
            # нон
            last_mess = None
        # если нон
        if last_mess is None:
            # пропускаем
            continue
        # в список добавляем инфу
        data['dialogs_info'].append({
            'id': dialog.id,
            'user': dialog.user,
            'vk_account': dialog.vk_account,
            'with_uid': dialog.with_uid,
            'with_fname': dialog.with_fname,
            'with_lname': dialog.with_lname,
            'with_photo': dialog.with_photo,
            'num_messages': dialog.num_messages,
            'last_message': last_mess
        })
    return render(request, 'room/dialogs.html', data)


def dialog(request, vk_acc_id=None, dialog_id=None):
    """Вывод диалога"""
    data = {'errors': []}  # данные
    # если юзер не авторизован
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # если у юзера не подтверждено мыло
    if not request.user.settings.confirmed:
        return HttpResponseRedirect('/room/')
    # админ
    if request.user.is_staff:
        data['admin'] = True
    # берём аккаунт вк
    data['vk_account'] = VKAccount.objects.get(user=request.user, id=vk_acc_id)
    # берём диалог вк
    data['dialog'] = VKSpamDialog.objects.get(user=request.user, vk_account=data['vk_account'], id=dialog_id)
    # берём сообщения диалоа вк
    data['messages'] = VKSpamDialogMessage.objects.filter(user=request.user, mdialog=data['dialog']).order_by('sent_at')[:100]
    return render(request, 'room/dialog.html', data)


def send_message(request):
    """Отправка сообщения из диалога"""
    # получаем текст сообщения
    body_message = request.GET['body']
    # получаем акк вк
    vk_acc = VKAccount.objects.get(id=request.GET['id_vk_acc'], user=request.user)
    # получаем диалог
    dialog = VKSpamDialog.objects.get(id=request.GET['id_dialog'], user=request.user)

    # получаем апи
    vk_api = get_random_vk_api(vk_login=vk_acc.login, vk_password=vk_acc.password)
    # если не получили
    if vk_api is None:
        # говорим
        return HttpResponse('bad', content_type='text/html')
    # если получили
    else:
        # отсылаем сообщение
        vk_api.messages.send(user_id=dialog.with_uid, message=body_message)
        # прибавляем колво сообщений
        dialog.num_messages += 1
        # сохраняем
        dialog.save()

    # получаем текущее время
    d = datetime.datetime.now()
    # получаем часовой пояс
    timezone = pytz.timezone("Europe/Moscow")
    # устанавливаем часовой пояс
    d = timezone.localize(d)

    # создаем сообщение
    VKSpamDialogMessage.objects.create(from_vk_account=True, user=request.user, body=body_message, mdialog=dialog, sended_at=d)

    # добавляем действие
    add_action(
        'Отправил сообщение вконтакте',
        site_settings.action_type_send_message.char_id,
        request.user
    )

    text = 'Сообщение успешно отправлено.'
    # письмо
    notify(
        to_email=request.user.email,
        title=site_settings.action_type_send_message.name,
        text=text,
        user=request.user
    )

    return HttpResponse('ok', content_type='text/html')


def delete_dialog(request):
    """Удаление диалога"""
    try:
        # получаем вк акк
        vk_acc = VKAccount.objects.get(id=request.GET['id_vk_acc'], user=request.user)
        # диалог получаем
        dialog = VKSpamDialog.objects.get(id=request.GET['id_dialog'], user=request.user, vk_account=vk_acc)
        # и удаляем
        dialog.delete()
    # если какая либо ошибка
    except:
        # говорим
        return HttpResponse('bad', content_type='text/html')

    # добавляем действие
    add_action(
        'Удалил диалог',
        site_settings.action_type_delete_dialog.char_id,
        request.user
    )

    text = 'Диалог успешно удален.'
    # письмо
    notify(
        to_email=request.user.email,
        title=site_settings.action_type_delete_dialog.name,
        text=text,
        user=request.user
    )
    return HttpResponse('ok', content_type='text/html')


def visit_client(request):
    """Пометить клиента как посещённого"""
    # получаем айди
    c_id = request.GET['c_id']
    # получаем самого клиента
    client = VKClient.objects.get(id=c_id)
    # делаем посещённым
    client.visited = True
    # сохраняем
    client.save()
    return HttpResponse('ok')


def visit_comment(request):
    """Пометить коммент как посещённый"""
    # получаем айди
    c_id = request.GET['c_id']
    # получаем сам коммент
    comment = VKComment.objects.get(id=c_id)
    # делаем посещённым
    comment.visited = True
    # сохраняем
    comment.save()
    return HttpResponse('ok')
