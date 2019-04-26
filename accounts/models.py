from django.db import models
from django.contrib.auth.models import User


class UserPlan(models.Model):
    """Тариф"""
    name = models.CharField(max_length=255, verbose_name='Название')
    char_id = models.CharField(max_length=32, unique=True, verbose_name='Идентификатор тарифа (символьный)')
    num_accounts = models.IntegerField(verbose_name='Максимальное количество аккаунтов вконтакте', default=0)
    num_groups = models.IntegerField(verbose_name='Максимальное количество групп', default=0)
    max_group_size = models.IntegerField(verbose_name='Максимальный размер группы', default=0)
    num_texts = models.IntegerField(verbose_name='Количество текстов для рассылки сообщений', default=2)
    price = models.FloatField(default=0, verbose_name='Цена за месяц')
    is_standard = models.BooleanField(default=False, verbose_name='Входит ли тариф в состав стандартных')

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'

    def __str__(self):
        return self.name


class UserSettings(models.Model):
    """Настройки пользователя"""
    confirmed = models.BooleanField(default=False, verbose_name='Подтверждённая почта')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    plan = models.ForeignKey('UserPlan', on_delete=models.PROTECT, verbose_name='Тариф')
    # spam settings
    spam_selected_option = models.CharField(
        max_length=1,
        default='1',
        verbose_name='Выбранная опция рассылки сообщений'
    )
    spam_interval = models.CharField(
        max_length=2,
        default='10',
        verbose_name='Выбранный интервал между сообщениями, мин.'
    )
    spam_range_from = models.CharField(
        max_length=2,
        default='1',
        verbose_name='Выбранный диапозон (от), мин.'
    )
    spam_range_to = models.CharField(
        max_length=2,
        default='10',
        verbose_name='Выбранный диапозон (до, включительно), мин.'
    )
    spam_range_or_interval = models.CharField(
        max_length=1,
        default='1',
        verbose_name='Выбранный интервал (заданный, или в диапазоне)'
    )
    spam_last = models.BooleanField(default=True, verbose_name='Рассылать тем, кому уже разослано')

    class Meta:
        verbose_name = 'Настройка'
        verbose_name_plural = 'Настройки'

    def __str__(self):
        return str(self.id)


class UserEmailConfirmation(models.Model):
    """Подтверждение почты"""
    token = models.CharField(max_length=255, unique=True, verbose_name='Токен')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    class Meta:
        verbose_name = 'Подтверждение почты'
        verbose_name_plural = 'Подтверждения почты'

    def __str__(self):
        return self.user.email


class UserPasswordConfirmation(models.Model):
    """Подтверждение пароля"""
    token = models.CharField(max_length=255, unique=True, verbose_name='Токен')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    class Meta:
        verbose_name = 'Подтверждение изменения пароля'
        verbose_name_plural = 'Подтверждения изменения пароля'

    def __str__(self):
        return self.user.email


class UserSpamText(models.Model):
    """Текст для спама"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    spam_text = models.TextField(
        default="Здравствуйте, <имя> <фамилия>!\nИнтересуетесь группой <группа>?\nТогда вам понравится...",
        verbose_name='Текст рассылки сообщений'
    )
    default = models.BooleanField(default=False, verbose_name='Основной')

    class Meta:
        verbose_name = 'Текст для спама'
        verbose_name_plural = 'Текста для спама'

    def __str__(self):
        return self.user.email


class SiteSettings(models.Model):
    """Настройки сайта"""
    name = models.CharField(max_length=255, verbose_name='Название')
    char_id = models.CharField(max_length=255, verbose_name='Идентификатор (символьный)')
    default_plan = models.ForeignKey(
        'UserPlan',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Стандартный тариф'
    )
    action_type_registration = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "регистрация"',
        related_name='action_type_registration'
    )
    action_type_login = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "логинирование"',
        related_name='action_type_login'
    )
    action_type_logout = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "выход из аккаунта"',
        related_name='action_type_logout'
    )
    action_type_email_confirmation = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "подтверждение почты"',
        related_name='action_type_email_confirmation'
    )
    action_type_edit_password = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "изменение пароля"',
        related_name='action_type_edit_password'
    )
    action_type_get_reset_password = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "получение восстановления пароля"',
        related_name='action_type_get_reset_password'
    )
    action_type_reset_password = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "восстановление пароля"',
        related_name='action_type_reset_password'
    )
    action_type_change_email = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "изменение почты"',
        related_name='action_type_change_email'
    )
    action_type_send_email_again = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "повторное отправление письма с подтверждением"',
        related_name='action_type_send_email_again'
    )
    action_type_confirm_promocode = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "ввод промокода"',
        related_name='action_type_confirm_promocode'
    )
    action_type_add_group = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "добавление источника"',
        related_name='action_type_add_group'
    )
    action_type_delete_group = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "удаление источника"',
        related_name='action_type_delete_group'
    )
    action_type_check_roots = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "проверка источников"',
        related_name='action_type_check_roots'
    )
    action_type_add_vk_account = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "добавление аккаунта вк"',
        related_name='action_type_add_vk_account'
    )
    action_type_delete_vk_account = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "удаление аккаунта вк"',
        related_name='action_type_delete_vk_account'
    )
    action_type_delete_comment = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "удаление коммента вк"',
        related_name='action_type_delete_comment'
    )
    action_type_send_message = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "отправка сообщения вк"',
        related_name='action_type_send_message'
    )
    action_type_delete_dialog = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "удаление диалога"',
        related_name='action_type_delete_dialog'
    )
    action_type_change_plan = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "изменение тарифа"',
        related_name='action_type_change_plan'
    )
    action_type_start_spam = models.ForeignKey(
        'room.UserActionType',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Тип действия "рассылка сообщений"',
        related_name='action_type_start_spam'
    )

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайтов'

    def __str__(self):
        return self.char_id
