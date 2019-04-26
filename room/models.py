from django.db import models
from django.contrib.auth.models import User


class UserActionType(models.Model):
    """Тип действия"""
    name = models.CharField(max_length=255, verbose_name='Название')
    char_id = models.CharField(max_length=32, unique=True, verbose_name='Идентификатор (символьный)')
    description = models.TextField(default='', blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Тип действия'
        verbose_name_plural = 'Типы действий'

    def __str__(self):
        return self.name


class UserAction(models.Model):
    """Действие пользователя"""
    name = models.CharField(max_length=255, verbose_name='Название')
    happened = models.DateTimeField(auto_now_add=True, verbose_name='Время действия')
    type = models.ForeignKey('UserActionType', on_delete=models.PROTECT, verbose_name='Тип действия')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Действие'
        verbose_name_plural = 'Действия'

    def __str__(self):
        return self.name


class VKApiApplication(models.Model):
    """Приложение вк для апи"""
    app_id = models.CharField(max_length=255, unique=True, verbose_name='Айди приложения')

    class Meta:
        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'

    def __str__(self):
        return self.app_id


class VKToken(models.Model):
    """Токен приложения вк"""
    token = models.CharField(max_length=255, unique=True, verbose_name='Токен')
    active = models.BooleanField(default=True, verbose_name='Рабочий')

    class Meta:
        verbose_name = 'Токен'
        verbose_name_plural = 'Токены'

    def __str__(self):
        return self.token


class VKAccount(models.Model):
    """Аккаунт вк для задач"""
    login = models.CharField(max_length=255, verbose_name='Логин')
    password = models.CharField(max_length=255, verbose_name='Пароль')
    aid = models.CharField(max_length=255, verbose_name='Айди')
    fname = models.CharField(max_length=255, verbose_name='Имя')
    lname = models.CharField(max_length=255, verbose_name='Фамилия')
    photo = models.CharField(max_length=255, verbose_name='Изображение')
    num_messages = models.IntegerField(verbose_name='Количество отправленных сообщений при рассылке')
    blocked = models.BooleanField(default=False, verbose_name='Заблокирован')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользоваватель')

    class Meta:
        verbose_name = 'Аккаунт вк'
        verbose_name_plural = 'Аккаунты вк'

    def __str__(self):
        return self.login


class VKClient(models.Model):
    """Возможный Клиент"""
    client_id = models.CharField(max_length=255, verbose_name='Айди')
    fname = models.CharField(max_length=255, verbose_name='Имя')
    lname = models.CharField(max_length=255, verbose_name='Фамилия')
    photo = models.CharField(max_length=255, verbose_name='Фото')
    group = models.ForeignKey('VKGroup', on_delete=models.CASCADE, verbose_name='Группа')
    selected = models.BooleanField(default=False, verbose_name='Выбран')
    spammed = models.BooleanField(default=False, verbose_name='Разослано?')
    visited = models.BooleanField(default=False, verbose_name='Просмотрен')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.client_id


class VKGroup(models.Model):
    """Источник"""
    group_id = models.CharField(max_length=255, verbose_name='Айди')
    title = models.CharField(max_length=255, verbose_name='Название')
    image = models.CharField(max_length=255, verbose_name='Картинка')
    num_members = models.IntegerField(verbose_name='Количество участников')
    members_ids = models.TextField(default='', verbose_name='Список айдишников')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Источник'
        verbose_name_plural = 'Источники'

    def __str__(self):
        return self.title


class VKComment(models.Model):
    """Комментарий"""
    uid = models.CharField(max_length=255, verbose_name='Айди пользователя')
    fname = models.CharField(max_length=255, verbose_name='Имя пользователя')
    lname = models.CharField(max_length=255, verbose_name='Фамилия пользователя')
    photo = models.CharField(max_length=255, verbose_name='Фото пользователя')
    text = models.TextField(default='', verbose_name='Текст комментария')
    selected = models.BooleanField(default=False, verbose_name='Выбран')
    visited = models.BooleanField(default=False, verbose_name='Просмотрен')
    spammed = models.BooleanField(default=False, verbose_name='Разослано?')
    group = models.ForeignKey('VKGroup', on_delete=models.CASCADE, verbose_name='Группа')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользоваватель')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.fname + ' ' + self.lname


class VKSpamDialog(models.Model):
    """Диалог вк"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользоваватель')
    vk_account = models.ForeignKey('room.VKAccount', on_delete=models.CASCADE, verbose_name='Аккаунт вк')
    with_uid = models.CharField(max_length=255, verbose_name='Айди собеседника')
    with_fname = models.CharField(max_length=255, verbose_name='Имя собеседника')
    with_lname = models.CharField(max_length=255, verbose_name='Фамилия собеседника')
    with_photo = models.CharField(max_length=255, verbose_name='Изображение собеседника')
    num_messages = models.IntegerField(verbose_name='Количество сообщений')

    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'

    def __str__(self):
        return self.with_fname + ' ' + self.with_lname


class VKSpamDialogMessage(models.Model):
    """Сообщения диалога вк"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользоваватель')
    from_vk_account = models.BooleanField(verbose_name='От аккаунта вк?')
    message_id = models.CharField(max_length=255, verbose_name='Айди сообщения')
    body = models.TextField(verbose_name='Тело сообщения')
    sent_at = models.DateTimeField(verbose_name='Время отправки')
    dialog = models.ForeignKey('VKSpamDialog', on_delete=models.CASCADE, verbose_name='Диалог')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return self.body
