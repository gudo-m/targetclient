import kronos
import random
import vk
import time
import datetime
import pytz
from accounts.views import get_random_vk_api, notify
from room.models import VKAccount, VKApiApplication, VKToken, VKSpamDialogMessage, VKSpamDialog, VKClient, VKComment, VKGroup
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model

User = get_user_model()


@kronos.register('0 * * * *')
def check_dialogs():
    emails = ['admin@targetclient.tk']
    data = "Здравствуйте, Администратор!" + '\nПроверка диалогов началась!\n\n\n\n---------\nС уважением,\nTargetClient\nwww.targetclient.tk'
    email = EmailMessage('Проверка диалогов началась', data, to=emails)
    email.send()
    num_new_messages = 0
    num_checked_dialogs = 0
    num_checked_vk_accounts = 0
    for vk_account in VKAccount.objects.all():
        for dialog in VKSpamDialog.objects.filter(vk_account=vk_account):
            num_checked_dialogs += 1
            time.sleep(0.3)
            vk_api = get_random_vk_api(vk_login=vk_account.login, vk_password=vk_account.password)

            last_messages = vk_api.messages.getHistory(count=200, user_id=dialog.with_uid)
            new_messages = last_messages[1:]
            for new_message in new_messages:
                from_me = True if str(new_message['from_id']) == str(vk_account.aid) else False
                d = datetime.datetime.fromtimestamp(new_message['date'])
                timezone = pytz.timezone("Europe/Moscow")  # указываем часовой пояс
                d = timezone.localize(d)
                msg_text_updtd = new_message['body']
                while '<br>' in msg_text_updtd:
                    msg_text_updtd = msg_text_updtd[:msg_text_updtd.index('<br>')] + '\n' + msg_text_updtd[msg_text_updtd.index('<br>') + len('<br>'):]
                try:
                    mess_ex = VKSpamDialogMessage.objects.get(from_vk_account=from_me, message_id=new_message['mid'],mdialog=dialog, user=vk_account.user, body=msg_text_updtd)
                except VKSpamDialogMessage.DoesNotExist:
                    mess_ex = VKSpamDialogMessage.objects.create(from_vk_account=from_me, message_id=new_message['mid'],mdialog=dialog, sended_at=d, user=vk_account.user, body=msg_text_updtd)
                    dialog.num_messages+=1
                    num_new_messages+=1
            dialog.save()
        num_checked_vk_accounts+=1
    data = "Здравствуйте, Администратор!" + '\nПроверка диалогов завершена! \nНовых сообщений: '+str(num_new_messages)+'\nПроверено диалогов: '+str(num_checked_dialogs)+'\nПроверено аккаунтов вк: '+str(num_checked_vk_accounts)+'\n\n\n\n---------\nС уважением,\nTargetClient\nwww.targetclient.tk'
    email = EmailMessage('Проверка диалогов завершена', data, to=emails)
    email.send()



@kronos.register('0 11,23 * * *')
def check_roots():
    emails = ['admin@targetclient.tk']
    data = "Здравствуйте, Администратор!" + '\nПроверка источников началась!\n\n\n\n---------\nС уважением,\nTargetClient\nwww.targetclient.tk'
    email = EmailMessage('Проверка источников началась', data, to=emails)
    email.send()
    num_new_clients = 0
    num_checked_roots = 0
    num_checked_users = 0
    num_errors = 0
    vk_api = get_random_vk_api()
    for user in User.objects.all().order_by('-id'):
        num_checked_users+=1
        for root in VKGroup.objects.filter(user=user):
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
                            user=user,
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
                                    user=user,
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
                                    user=user,
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
                        to_email=user.email,
                        title='Проверка источников',
                        text=text,
                        user=user
                    )
                # после каждого раза прибавляем 1
                i += 1
            # после парсинга сохраняем
            root.save()
        to_email = [user.email]
        data = "Здравствуйте, "+user.username+"!" + '\nПроверка ваших источников завершена! Скорее всего, на странице возможных клиентов появились новые клиенты.' + '\n\n\n\n---------\nС уважением,\nTargetClient\nwww.targetclient.tk'
        email = EmailMessage('Проверка источников завершена', data, to=to_email)
        email.send()
    data = "Здравствуйте, Администратор!" + '\nПроверка источников завершена! \nНовых клиентов: '+str(num_new_clients)+'\nПроверено источников: '+str(num_checked_roots)+'\nПроверено пользователей: '+str(num_checked_users)+'\nОшибок: '+str(num_errors)+'\n\n\n\n---------\nС уважением,\nTargetClient\nwww.targetclient.tk'
    email = EmailMessage('Проверка источников завершена', data, to=emails)
    email.send()