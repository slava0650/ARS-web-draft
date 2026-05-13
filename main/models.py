from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='profile',
    )
    steamid64 = models.CharField('SteamID64', max_length=17, unique=True)
    arma_id = models.CharField('Arma ID', max_length=120, unique=True)
    discord_username = models.CharField('Discord username', max_length=120, unique=True)
    is_approved = models.BooleanField('Подтверждён администратором', default=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Подтвердил',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_profiles',
    )
    approved_at = models.DateTimeField('Дата подтверждения', null=True, blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'{self.user.username} profile'

    def approve(self, admin_user=None):
        self.is_approved = True
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])

    def revoke(self):
        self.is_approved = False
        self.approved_by = None
        self.approved_at = None
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])


class SquadApplication(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_squad_applications',
    )
    squad_name = models.CharField('Название отряда', max_length=120)
    commander_name = models.CharField('Имя командира', max_length=120)
    contact = models.CharField('Discord или Telegram', max_length=120)
    players_count = models.PositiveIntegerField('Количество игроков')
    description = models.TextField('Описание отряда')
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка на отряд'
        verbose_name_plural = 'Заявки на отряды'

    def __str__(self):
        return f'{self.squad_name} — {self.commander_name}'


class Squad(models.Model):
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Набор открыт'),
        (STATUS_CLOSED, 'Набор закрыт'),
    ]

    name = models.CharField('Название отряда', max_length=120)
    slug = models.SlugField('URL', max_length=140, unique=True, allow_unicode=True)
    description = models.TextField('Краткое описание')
    players_count = models.PositiveIntegerField('Количество игроков', default=1)
    recruitment_status = models.CharField('Статус набора', max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    commander_name = models.CharField('Командир', max_length=120, blank=True)
    specialization = models.TextField('Специализация', blank=True)
    communication = models.CharField('Связь', max_length=160, blank=True)
    schedule = models.CharField('Расписание', max_length=160, blank=True)
    requirements = models.TextField('Требования', blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Владелец отряда',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_squads',
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Отряд'
        verbose_name_plural = 'Отряды'

    def __str__(self):
        return self.name

    @property
    def status_label(self):
        return self.get_recruitment_status_display()

    @property
    def requirements_list(self):
        return [line.strip() for line in self.requirements.splitlines() if line.strip()]


class SquadMembership(models.Model):
    ROLE_COMMANDER = 'commander'
    ROLE_DEPUTY = 'deputy'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [
        (ROLE_COMMANDER, 'Командир отряда'),
        (ROLE_DEPUTY, 'Зам. командира'),
        (ROLE_MEMBER, 'Участник'),
    ]

    squad = models.ForeignKey(Squad, verbose_name='Отряд', on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='squad_memberships',
    )
    display_name = models.CharField('Имя игрока', max_length=120)
    contact = models.CharField('Контакт', max_length=120, blank=True)
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField('Дата вступления', auto_now_add=True)

    class Meta:
        ordering = ['squad', 'role', 'display_name']
        verbose_name = 'Участник отряда'
        verbose_name_plural = 'Участники отрядов'

    def __str__(self):
        return f'{self.display_name} — {self.squad}'

    @property
    def can_review_applications(self):
        return self.role in {self.ROLE_COMMANDER, self.ROLE_DEPUTY}

    @property
    def can_edit_squad(self):
        return self.role == self.ROLE_COMMANDER


class SquadJoinApplication(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'На рассмотрении'),
        (STATUS_ACCEPTED, 'Принята'),
        (STATUS_REJECTED, 'Отклонена'),
    ]

    squad = models.ForeignKey(
        Squad,
        verbose_name='Отряд',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='join_applications',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='squad_join_applications',
    )
    squad_name = models.CharField('Отряд', max_length=120)
    player_name = models.CharField('Игровой ник', max_length=120)
    contact = models.CharField('Discord или Telegram', max_length=120)
    age = models.PositiveIntegerField('Возраст')
    experience = models.CharField('Опыт в Arma Reforger', max_length=160)
    message = models.TextField('Комментарий')
    status = models.CharField('Статус', max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Рассмотрел',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_squad_join_applications',
    )
    reviewed_at = models.DateTimeField('Дата рассмотрения', null=True, blank=True)
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка на вступление'
        verbose_name_plural = 'Заявки на вступление'

    def __str__(self):
        return f'{self.player_name} → {self.squad_name}'

    def accept(self, reviewer):
        self.status = self.STATUS_ACCEPTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        if self.squad:
            SquadMembership.objects.get_or_create(
                squad=self.squad,
                user=self.user,
                display_name=self.player_name,
                defaults={
                    'contact': self.contact,
                    'role': SquadMembership.ROLE_MEMBER,
                },
            )

    def reject(self, reviewer):
        self.status = self.STATUS_REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])


class Event(models.Model):
    title = models.CharField('Название события', max_length=160)
    slug = models.SlugField('URL', max_length=180, unique=True, allow_unicode=True)
    date_label = models.CharField('Дата', max_length=60)
    time_label = models.CharField('Время', max_length=40)
    starts_at_unix = models.PositiveBigIntegerField(
        'Unix время события',
        null=True,
        blank=True,
        help_text='Unix timestamp в секундах. На сайте дата и время будут показаны в часовом поясе пользователя.',
    )
    event_type = models.CharField('Тип события', max_length=80)
    short_description = models.TextField('Краткое описание')
    mission_description = models.TextField('Описание миссии')
    server_name = models.CharField('Название сервера', max_length=160)
    server_ip = models.GenericIPAddressField('IP сервера')
    server_port = models.PositiveIntegerField('Порт сервера')
    server_password = models.CharField('Пароль сервера', max_length=120, blank=True)
    password_visible_to_squads = models.BooleanField('Пароль виден отрядам', default=True)
    password_visible_to_solo = models.BooleanField('Пароль виден одиночным игрокам', default=False)
    max_solo_players = models.PositiveIntegerField('Слотов для одиночных игроков', default=20)
    solo_registration_open = models.BooleanField('Запись одиночных игроков открыта', default=False)
    squad_slotting_open = models.BooleanField('Слоттинг отрядов открыт', default=False)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return self.title

    @property
    def server_address(self):
        return f'{self.server_ip}:{self.server_port}'


class EventSoloRegistration(models.Model):
    event = models.ForeignKey(Event, verbose_name='Событие', on_delete=models.CASCADE, related_name='solo_registrations')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='event_solo_registrations',
    )
    player_name = models.CharField('Игровой ник', max_length=120)
    contact = models.CharField('Discord или Telegram', max_length=120)
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('event', 'user')
        verbose_name = 'Регистрация одиночного игрока'
        verbose_name_plural = 'Регистрации одиночных игроков'

    def __str__(self):
        return f'{self.player_name} → {self.event}'


class EventSquadSlot(models.Model):
    event = models.ForeignKey(Event, verbose_name='Событие', on_delete=models.CASCADE, related_name='squad_slots')
    squad = models.ForeignKey(Squad, verbose_name='Отряд', on_delete=models.CASCADE, related_name='event_slots')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Кто записал',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_event_squad_slots',
    )
    side = models.CharField('Сторона / роль на миссии', max_length=120)
    players_count = models.PositiveIntegerField('Количество игроков')
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Дата слоттинга', auto_now_add=True)

    class Meta:
        ordering = ['squad__name']
        unique_together = ('event', 'squad')
        verbose_name = 'Слоттинг отряда'
        verbose_name_plural = 'Слоттинг отрядов'

    def __str__(self):
        return f'{self.squad} → {self.event}'


class EventSlotDepartment(models.Model):
    event = models.ForeignKey(Event, verbose_name='Событие', on_delete=models.CASCADE, related_name='slot_departments')
    name = models.CharField('Название отделения', max_length=120)
    total_slots = models.PositiveIntegerField('Количество слотов')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Отделение миссии'
        verbose_name_plural = 'Отделения миссии'

    def __str__(self):
        return f'{self.name} — {self.event}'

    @property
    def occupied_slots_count(self):
        return self.assignments.count()

    @property
    def slot_numbers(self):
        return range(1, self.total_slots + 1)


class EventSlotAssignment(models.Model):
    department = models.ForeignKey(
        EventSlotDepartment,
        verbose_name='Отделение',
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    squad = models.ForeignKey(Squad, verbose_name='Отряд', on_delete=models.CASCADE, related_name='event_slot_assignments')
    slot_number = models.PositiveIntegerField('Номер слота')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Кто занял слот',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_event_slot_assignments',
    )
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Дата слоттинга', auto_now_add=True)

    class Meta:
        ordering = ['department', 'slot_number']
        unique_together = ('department', 'slot_number')
        verbose_name = 'Занятый слот миссии'
        verbose_name_plural = 'Занятые слоты миссии'

    def __str__(self):
        return f'{self.department.name} #{self.slot_number} — {self.squad}'
