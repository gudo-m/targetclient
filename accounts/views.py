from mysite.settings import DEFAULT_SITE_ID, EMAIL_HOST_USER
from .models import UserEmailConfirmation, UserPlan, UserPasswordConfirmation, UserSettings, SiteSettings, UserSpamText
from room.models import UserAction, UserActionType, VKApiApplication, VKToken
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import login, get_user_model, logout, authenticate
from uuid import uuid4
from django.core.mail import EmailMessage
from ipware.ip import get_real_ip
import pytz
import datetime
import time
import random
import vk

User = get_user_model()  # модель юзера
site_settings = SiteSettings.objects.get(char_id=DEFAULT_SITE_ID)  # настройки сайта


def notify(to_email=EMAIL_HOST_USER, title=site_settings.name, text="ok", user=None):
    """Уведомление юзеру"""
    if user is not None:
        text = """Здравствуйте, {}!\n{}\n\n\n\n---------\nС уважением,\nTargetClient\nwww.targetclient.tk""".format(
            user.username,
            text
        )
    email = EmailMessage(title, text, to=[to_email])
    try:
        email.send()
    except Exception as e:
        # print(e)
        return

def check_action(char_id, seconds, user):
    """Проверить, прошло ли seconds секунд после последнего slug действия"""
    if user.username == 'admin':
        seconds = 0
    doing_slug = UserActionType.objects.get(char_id=char_id)  # берем действие (а именно тип действия)
    # пробуем найти это действие в действиях пользователя
    try:
        # и взять последнее действие
        user_doing = UserAction.objects.filter(type=doing_slug, user=user).order_by('-id')[0]
    except IndexError:
        # иначе none
        user_doing = None

    # если нашли
    if user_doing is not None:
        d = datetime.datetime.now()  # берём текущее время
        timezone = pytz.timezone("Europe/Moscow")  # указываем часовой пояс
        delta = timezone.localize(d) - user_doing.happened  # сколько прошло
        if delta.seconds < int(seconds):  # если ещё не прошло N секунд, даём знать
            return False

    # если такого действия нет, или уже прошло достаточно секунд - true
    return True


def add_action(title, char_id, user):
    """Добавление действия"""
    # берём тип
    action_type = UserActionType.objects.get(char_id=char_id)
    # добавляем действие пользователю
    UserAction.objects.create(name=title, type=action_type, user=user)


def normalize_num_texts(user):
    """Нормализует колво текстов"""
    # получаем текущие текста
    now_texts = UserSpamText.objects.filter(user=user)
    # пока сейчас текстов больше, чем надо
    while len(now_texts) > 2:
        # удаляем последний текст
        UserSpamText.objects.filter(user=user).order_by('-id')[0].delete()
        now_texts = UserSpamText.objects.filter(user=user)
    # пока текстов меньше, чем надо
    while len(now_texts) < 2:
        # добавляем текст
        UserSpamText.objects.create(user=user)
        now_texts = UserSpamText.objects.filter(user=user)
    return True


def get_default_text(user):
    """Возвращает основной текст"""
    # получаем текста юзера с отметкой основной
    user_texsts = UserSpamText.objects.filter(user=user, default=True)
    # если есть хоть один
    if len(user_texsts) > 0:
        # возвращаем первый
        return user_texsts[0]
    # если ни одного нет
    else:
        # возвращаем рандомный из всех, если у него есть хотябы один
        if len(UserSpamText.objects.filter(user=user)) > 0:
            return random.choice(UserSpamText.objects.filter(user=user))
        # если вообще нет то нон
        else:
            return None


def get_random_vk_api(vk_login=None, vk_password=None):
    """Возвращает апи вк"""
    # изначально вк апи нон
    vk_api = None
    # колво попыток
    i = 0
    # пока нон
    while vk_api is None:
        # пробуем получить апи
        try:
            if vk_login is not None and vk_password is not None:
                session = vk.AuthSession(
                    app_id=random.choice(VKApiApplication.objects.all()).app_id,
                    user_login=vk_login,
                    user_password=vk_password,
                    scope='messages, friends, wall, groups'
                )
            else:
                session = vk.AuthSession(access_token=random.choice(VKToken.objects.all()).token)
            vk_api = vk.API(session, version='5.80')
            vk_api.users.get(user_ids=['1'])
        # если ошибка
        except:
            # нон
            vk_api = None
        # +1 попытка
        i += 1
        # если уже больше 10 попыток
        if i > 10:
            # если через токен
            if vk_login is None and vk_password is None:
                # спим
                time.sleep(i * 0.5)
            # если через акк
            else:
                # возвращаем нон
                return None
        # если меньше 10 попыток
        else:
            # спим
            time.sleep(i//10)
    return vk_api


def register(request):
    """Регистрация юзера"""
    # если не админ, посылаем
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    # создаем словарь данных для передачи админу
    data = {'register': True, 'errors': []}
    if request.POST:  # если пост
        p_username = request.POST.get('login', '')  # берём логин
        p_password = request.POST.get('password', '')  # пароль
        p_password2 = request.POST.get('password2', '')  # пароль2
        p_email = request.POST.get('email', '')  # почту

        # проверки на валидность данных

        # длина логина меньше 4
        if len(p_username) < 4:
            data['errors'].append('Длина логина не может быть короче 4 символов!')
        # проверка на валидность почты
        if len(p_email.split('@')) != 2 or len(p_email.split('.')) == 1:
            data['errors'].append('Некорректный email адрес!')
        # если пароли не совпадают
        if p_password != p_password2:
            data['errors'].append('Пароли не совпадают!')
        # если длина пароля меньше 8 или пароль состоит из цифр
        if len(p_password) < 8 or p_password.isdigit():
            data['errors'].append(
                'Пароль лишком простой. Пароль не может состоять только из цифр и должен быть длиннее 7 символов!'
            )
        user_with_this_email = User.objects.filter(email=p_email)  # пробуем взять пользователя с почтой
        if user_with_this_email:  # если получилось - ошибка
            data['errors'].append('Пользователь с таким EMAIL-адресом уже существует!')
        user_with_this_login = User.objects.filter(username=p_username)  # тоже самое с логином
        if user_with_this_login:
            data['errors'].append('Пользователь с таким логином уже существует!')

        # если есть хоть одна ошибка, говорим админу
        if len(data['errors']) > 0:
            return render(request, 'accounts/register.html', data)

        base_plan = site_settings.default_plan  # берём начальный тариф

        # создаем пользователя
        user = User.objects.create_user(username=p_username, email=p_email, password=p_password)
        # создаем настройки для него
        UserSettings.objects.create(user=user, plan=base_plan)
        # сохраняем
        user.save()

        # добавляем действие
        add_action('Зарегистрировался', site_settings.action_type_registration.char_id, user)

        rand_token = uuid4()  # берём рандомный токен
        # создаем подтверждение почты
        UserEmailConfirmation.objects.create(token=rand_token, user=user)

        # уведомляем
        text = 'Ваш аккаунт успешно зарегистрирован!\n\n' \
               'Подтвердите почту для полного доступа к аккаунту:\n'\
               + 'www.targetclient.tk/accounts/confirm/'\
               + user.email + '/' + str(rand_token)
        notify(
            to_email=user.email,
            title=site_settings.action_type_registration.name,
            text=text,
            user=user
        )

        # нормализуем колво текстов
        normalize_num_texts(user)

        return HttpResponseRedirect('/room/')
    # если гет, то рендерим темплейт
    else:
        return render(request, 'accounts/register.html', data)


def login_view(request):
    """Логинирование"""
    if request.user.is_authenticated:  # если уже логинирован, посылаем
        return HttpResponseRedirect('/room/')
    data = {'register': True, 'errors': []}  # словарь данных
    if request.POST:  # если пост
        p_login = request.POST.get('login', '')  # берём логин
        p_password = request.POST.get('password', '')  # пароль

        user = authenticate(username=p_login, password=p_password)  # пробуем получить пользователя по логину
        if user is None:  # по почте
            user = authenticate(email=p_login, password=p_password)

        if user is None:  # если нет - говорим
            data['errors'].append('Пользователь с такими логином и паролем не найден!')
            return render(request, 'accounts/login.html', data)

        login(request, user)  # логинируем

        ip = get_real_ip(request)  # получаем айпи
        if ip is None:
            ip = '*IP-адрес скрыт*'

        text = 'В ваш аккаунт выполнен вход. Вот информация, которую мы получили:\n\n'\
               + 'Ip: ' + str(ip) + '\n\n\nЕсли это были не вы, немедленно примите меры.'
        # письмо
        notify(
            to_email=user.email,
            title=site_settings.action_type_login.name,
            text=text,
            user=user
        )

        # добавляем действие
        add_action('Вошёл в аккаунт', site_settings.action_type_login.char_id, user)

        return HttpResponseRedirect('/room/')
    # если гет
    else:
        return render(request, 'accounts/login.html', data)


def logout_view(request):
    """Выход из акка"""
    if not request.user.is_authenticated:  # если не авторизован посылаем
        return HttpResponseRedirect('/')

    # добавляем действие
    add_action('Вышел из аккаунта', site_settings.action_type_logout.char_id, request.user)

    # письмо
    text = 'Вы успешно вышли из аккаунта.'
    notify(
        to_email=request.user.email,
        title=site_settings.action_type_logout.name,
        text=text,
        user=request.user
    )

    logout(request)  # выходим

    return HttpResponseRedirect('/accounts/login')


def confirm_mail(request, email='', token=''):
    """Подтверждение почты"""
    try:  # пробуем получить юзера по мылу
        user = User.objects.get(email=email)
    # Если не получилось
    except User.DoesNotExist:
        # none
        user = None
    try:  # получаем подтверждение почты
        confirmation = UserEmailConfirmation.objects.get(user=user, token=token)
    # если не получилось - нон
    except UserEmailConfirmation.DoesNotExist:
        confirmation = None
    if confirmation is not None:  # если найдено
        user.settings.confirmed = True  # делаем юзера подтверждённым
        user.save()  # сохраняем
        confirmation.delete()  # удаляем подтверждение почты

        text = 'Ваш email успешно подтверждён, а значит вы имеете полный доступ к аккаунту!'

        # письмо
        notify(
            to_email=user.email,
            title=site_settings.action_type_email_confirmation.name,
            text=text,
            user=user
        )

        # добавляем действие
        add_action('Подтвердил почтовый адрес', site_settings.action_type_email_confirmation.char_id, request.user)

    return HttpResponseRedirect('/room/')


def edit_password(request):
    """Изменение пароля"""
    if not request.user.is_authenticated:  # не авторизован - посылаем
        return HttpResponseRedirect('/')
    data = {}  # данные
    if request.POST:
        # если пост
        # если старый пароль, который ввёл юзер, совпадает с текущим
        if request.user.check_password(request.POST['password1']):
            password2 = request.POST['password2']  # пароль 2
            password3 = request.POST['password3']  # пароль 3
            # если пароли совпадают и длина больше 7 символов и не состоят только из цифр
            if password2 == password3 and len(password3) > 7 and not password3.isdigit():
                request.user.set_password(password3)  # ставим новый пароль
                request.user.save()  # сохраняем

                text = 'Ваш пароль успешно изменён. Если это были не вы, немедленно сообщите нам!'

                # письмо
                notify(
                    to_email=request.user.email,
                    title=site_settings.action_type_edit_password.name,
                    text=text,
                    user=request.user
                )

                # добавляем действие
                add_action('Изменил пароль', site_settings.action_type_edit_password.char_id, request.user)

                data['errors'] = ['Ваш пароль успешно изменён!']

            # если пароли не прошли проверку
            else:
                data['errors'] = ['Ваши пароли не совпадают или слишком легкие!'
                                  'Пароль должен быть длиннее 7 символов и состоять из цифр и букв.']

        # если юзер ввёл неверный пароль
        else:
            data['errors'] = ['Вы ввели неверный пароль!']

        # в конце рендерим темплейт
        return render(request, 'accounts/edit_password.html', data)

    # если гет
    else:
        if request.user.is_staff:  # если одмен
            data['admin'] = True
        return render(request, 'accounts/edit_password.html')


def get_reset_password(request):
    """Запрос на сброс пароля"""
    data = {'errors': []}  # данные
    # если пост запрос
    if request.POST:
        p_login = request.POST['login']  # берём логин

        try:  # ищем юзера по логину
            user = User.objects.get(username=p_login)
        except User.DoesNotExist:
            user = None

        if user is None:  # если никак, то по майлу
            try:
                user = User.objects.get(email=p_login)
            except User.DoesNotExist:
                user = None

        if user is None:  # если никак, то сообщаем
            data['errors'].append('Пользователь с таким логином/email не найден!')
        if len(data['errors']) > 0:
            return render(request, 'accounts/get_reset_password.html', data)

        if not check_action(site_settings.action_type_get_reset_password.char_id, 86400, request.user):
            # если недавно был такой запрос
            data['errors'].append('За сутки можно восстановить пароль только один раз!')
            return render(request, 'accounts/get_reset_password.html', data)

        # берём все восстановления пароля пользоывателя
        reseting_password = UserAction.objects.filter(type=site_settings.action_type_get_reset_password, user=user)

        # если их больше N, сообщаем (n указывается в админке)
        if len(reseting_password) >= site_settings.num_password_resets:
            data['errors'].append(
                'Вы превысили максимальное число восстановок пароля на один аккаунт.'
                ' Теперь для восстановления пароля вам потребуется обратиться в тех. поддержку!'
            )
            return render(request, 'accounts/get_reset_password.html', data)

        # если всё норм, генерим рандомный токен
        rand_token = uuid4()
        # создаем подтверждение почты
        UserPasswordConfirmation.objects.create(user=user, token=rand_token)

        text = 'С вашего аккаунта пришла заявка на восстановление пароля. Вот ссылка для воостановления:\n'\
               + 'www.targetclient.tk/accounts/reset_password_already/' + user.email + '/' + str(rand_token)\
               + '\nЕсли запрос на восстановление пароля сделали не вы, немедленно примите меры!'

        # уведомление
        notify(
            to_email=user.email,
            title=site_settings.action_type_get_reset_password.name,
            text=text,
            user=user
        )

        # сообщаем на сайте
        data['errors'].append('Мы отправили ссылку для восстановления пароля на ваш email.')

        return render(request, 'accounts/get_reset_password.html', data)
    # если гет
    else:
        # админ
        if request.user.is_staff:
            data['admin'] = True
        return render(request, 'accounts/get_reset_password.html', data)


def reset_password(request, email=None, token=None):
    """Само сбрасывание пароля, при переходе по ссылке"""
    data = {'errors': []}  # данные
    # если запрос post
    if request.POST:
        pass1 = request.POST['password1']  # пароль1
        pass2 = request.POST['password2']  # пароль2

        user = User.objects.get(email=email)  # получаем юзера

        data['form'] = True  # показать форму для ввода пароля
        try:  # пробуем получить подтверждение пароля
            pass_conf = UserPasswordConfirmation.objects.get(token=token, user=user)
        except UserPasswordConfirmation.DoesNotExist:  # если такого нет, пишем, мол, неизвестная ошибка
            data['errors'].append('Неизвестная ошибка')
            return render(request, 'accounts/reset_password.html', data)

        if pass1 != pass2:  # если пароли не совпадают
            data['errors'].append('Пароли различаются')
            return render(request, 'accounts/reset_password.html', data)
        if len(pass1) < 8 or pass1.isdigit():  # если не валидны
            data['errors'].append(
                'Ваш пароль слишком простой. Пароль должен быть длиннее 7 символов и состоять из букв и цифр.'
            )
            return render(request, 'accounts/reset_password.html', data)

        pass_conf.delete()  # если всё ок, удаляем подтверждение
        user.set_password(pass1)  # делаем юзеру такой пароль
        user.save()  # сохраняем

        # добавляем действие
        add_action('Восстановил пароль', site_settings.action_type_reset_password.char_id, request.user)

        data['errors'].append('Пароль успешно восстановлен!')  # сообщаем на сайте

        text = 'Ваш пароль успешно восстановлен!'

        # письмо
        notify(
            to_email=user.email,
            title=site_settings.action_type_reset_password.name,
            text=text,
            user=user
        )

        data['form'] = False  # убираем форму

        return render(request, 'accounts/login.html', data)
    # если гет
    else:

        try:  # проверяем, есть ли такое подтверждение пароля
            UserPasswordConfirmation.objects.get(token=token, user=User.objects.get(email=email))
        except UserPasswordConfirmation.DoesNotExist:  # если нет сообщаем
            data['errors'].append('Неизвестная ошибка')
            return render(request, 'accounts/reset_password.html', data)
        except User.DoesNotExist:  # если юзера нет сообщаем
            data['errors'].append('Неизвестная ошибка')
            return render(request, 'accounts/reset_password.html', data)

        data['form'] = True  # показываем форму
        return render(request, 'accounts/reset_password.html', data)


def change_email(request):
    """Изменение почты"""
    if request.POST:
        # если запрос пост
        data = {'errors': []}  # данные
        new_email = request.POST['new_email']  # майл берём
        password = request.POST['password']  # пароль
        if request.user.check_password(password):  # если пароль правильный
            # проверяем валидность майла
            if len(new_email.split('@')) != 2:
                data['errors'].append('Новый email имеет некорректный вид')
                return render(request, 'accounts/change_email.html', data)
            if len(new_email.split('@')[1].split('.')) < 2:
                data['errors'].append('Новый email имеет некорректный вид')
                return render(request, 'accounts/change_email.html', data)

            # если всё валидно

            if not check_action(site_settings.action_type_change_email.char_id, 86400, request.user):
                # если недавно был такой запрос
                data['errors'].append('За сутки можно изменить email только один раз!')
                return render(request, 'accounts/get_reset_password.html', data)

            # ставим, что пользователь не подтверждён
            request.user.settings.confirmed = False
            # у него новый майл
            request.user.email = new_email
            # и сохраняем
            request.user.save()

            # берем рандомный токен
            rand_token = uuid4()
            # создаем подтверждение почты
            UserEmailConfirmation.objects.create(token=rand_token, user=request.user)

            text = 'Подтвердите новый Email по следующей ссылке:\n\n\n'\
                   + 'www.targetclient.tk/accounts/confirm/' + request.user.email + '/' + str(rand_token)

            # письмо
            notify(
                to_email=request.user.email,
                title=site_settings.action_type_change_email.name,
                text=text,
                user=request.user
            )

            # добавляем действие
            add_action('Изменил email на '+new_email, site_settings.action_type_change_email.char_id, request.user)

            # на сайте пишем
            data['errors'].append('На новый email отправлено письмо с подтверждением нового почтового адреса. '
                                  'До подтверждение почты доступ к аккаунту ограничен.')

            return render(request, 'accounts/change_email.html', data)
        else:
            # если пароль неправильный
            data['errors'].append('Неверный пароль')
            return render(request, 'accounts/change_email.html', data)
    # если гет
    else:
        return render(request, 'accounts/change_email.html')


def send_email_again(request):
    """Отправить ещё раз письмо об подтверждении почты"""
    if not request.user.is_authenticated:  # если юзер не авторизован, пусть идёт, шагает
        return HttpResponse("bad", content_type='text/html')
    if request.user.settings.confirmed:  # если юзер подтверждён тоже делать нечего тут ему
        return HttpResponse("bad", content_type='text/html')

    if not check_action(site_settings.action_type_send_email_again.char_id, 86400, request.user):
        # если недавно был такой запрос
        return HttpResponse("many_requests", content_type='text/html')

    try:  # берём у юзера подтверждение почты
        user_conf = UserEmailConfirmation.objects.get(user=request.user)
    except UserEmailConfirmation.DoesNotExist:
        user_conf = None

    if user_conf is None:  # если его нет, то возвращаем ошибку
        return HttpResponse("bad", content_type='text/html')

    text = ' Подтвердите Email по следующей ссылке:\n\n\n'\
           + 'www.targetclient.tk/accounts/confirm/' + request.user.email + '/' + str(user_conf.token)

    # письмо
    notify(
        to_email=request.user.email,
        title=site_settings.action_type_send_email_again.name,
        text=text,
        user=request.user
    )

    # добавляем действие
    add_action(
        'Повторно отправил письмо с подтверждением почты',
        site_settings.action_type_send_email_again.char_id,
        request.user
    )

    return HttpResponse("ok", content_type='text/html')
