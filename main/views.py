from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from .forms import (
    EventConcreteSlotForm,
    LoginForm,
    RegisterForm,
    SquadApplicationForm,
    SquadEditForm,
    SquadJoinApplicationForm,
)
from .models import (
    Event,
    EventSoloRegistration,
    EventSlotAssignment,
    EventSlotDepartment,
    Squad,
    SquadApplication,
    SquadJoinApplication,
    SquadMembership,
)


SERVERS = [
    {'name': 'ARMA-RUSSIAN | MAIN', 'ip': '185.123.45.21:2001', 'online': '42 / 64'},
    {'name': 'ARMA-RUSSIAN | TRAINING', 'ip': '185.123.45.21:2002', 'online': '18 / 64'},
    {'name': 'ARMA-RUSSIAN | EVENT', 'ip': '185.123.45.21:2003', 'online': '0 / 80'},
    {'name': 'ARMA-RUSSIAN | HARDCORE', 'ip': '185.123.45.21:2004', 'online': '36 / 64'},
    {'name': 'ARMA-RUSSIAN | CONFLICT', 'ip': '185.123.45.21:2005', 'online': '51 / 80'},
    {'name': 'ARMA-RUSSIAN | RESERVE', 'ip': '185.123.45.21:2006', 'online': '7 / 48'},
]

DEFAULT_SQUADS = [
    {
        'slug': 'volk',
        'name': 'Волк',
        'description': 'Тактический отряд для организованных операций.',
        'players_count': 24,
        'recruitment_status': Squad.STATUS_OPEN,
        'commander_name': 'Алексей Волков',
        'specialization': 'Штурмовые группы, зачистка населённых пунктов, удержание ключевых позиций.',
        'communication': 'Discord: volk-command',
        'schedule': 'Среда и воскресенье, 20:00 МСК',
        'requirements': 'Возраст от 16 лет.\nГотовность играть по приказам командира.\nНаличие микрофона и стабильной связи.',
    },
    {
        'slug': 'sever',
        'name': 'Север',
        'description': 'Пехотное подразделение для регулярных событий.',
        'players_count': 18,
        'recruitment_status': Squad.STATUS_OPEN,
        'commander_name': 'Дмитрий Северин',
        'specialization': 'Пехотные манёвры, оборона рубежей, сопровождение техники.',
        'communication': 'Telegram: @sever_unit',
        'schedule': 'Вторник и суббота, 19:30 МСК',
        'requirements': 'Базовое понимание Arma Reforger.\nСпокойная коммуникация в голосовом канале.\nРегулярное участие в тренировках.',
    },
    {
        'slug': 'shtorm',
        'name': 'Шторм',
        'description': 'Отряд быстрого реагирования и разведки.',
        'players_count': 31,
        'recruitment_status': Squad.STATUS_CLOSED,
        'commander_name': 'Илья Громов',
        'specialization': 'Разведка, быстрые рейды, фланговые действия и работа малыми группами.',
        'communication': 'Discord: shtorm-hq',
        'schedule': 'Пятница, 21:00 МСК',
        'requirements': 'Опыт участия в организованных событиях.\nУверенная навигация и работа в малой группе.\nДисциплина связи во время операции.',
    },
]

EVENTS = [
    {
        'date': '12 мая',
        'time': '20:00',
        'title': 'Основная миссия',
        'type': 'PvP-событие',
        'description': 'Командная операция с участием нескольких отрядов.',
    },
    {
        'date': '14 мая',
        'time': '19:30',
        'title': 'Тренировка отрядов',
        'type': 'Тренировка',
        'description': 'Подготовка игроков к будущим событиям.',
    },
    {
        'date': '17 мая',
        'time': '21:00',
        'title': 'Динамическая операция',
        'type': 'Blitz-событие',
        'description': 'Быстрая миссия с высокой плотностью боевых действий.',
    },
]

DEFAULT_EVENTS = [
    {
        'slug': 'main-mission',
        'date_label': '12 мая',
        'time_label': '20:00',
        'title': 'Основная миссия',
        'event_type': 'PvP-событие',
        'short_description': 'Командная операция с участием нескольких отрядов.',
        'mission_description': 'Стороны получают ограниченные ресурсы, несколько ключевых районов и задачу удержать инициативу до конца операции. Миссия рассчитана на взаимодействие пехоты, разведки и командования.',
        'server_name': 'ARMA-RUSSIAN | EVENT',
        'server_ip': '185.123.45.21',
        'server_port': 2003,
        'max_solo_players': 20,
    },
    {
        'slug': 'squad-training',
        'date_label': '14 мая',
        'time_label': '19:30',
        'title': 'Тренировка отрядов',
        'event_type': 'Тренировка',
        'short_description': 'Подготовка игроков к будущим событиям.',
        'mission_description': 'Отработка построений, связи, перемещения колонной, зачистки зданий и взаимодействия между подразделениями. Подходит для новых игроков и отрядов, которым нужно синхронизировать базовые процедуры.',
        'server_name': 'ARMA-RUSSIAN | TRAINING',
        'server_ip': '185.123.45.21',
        'server_port': 2002,
        'max_solo_players': 30,
    },
    {
        'slug': 'dynamic-operation',
        'date_label': '17 мая',
        'time_label': '21:00',
        'title': 'Динамическая операция',
        'event_type': 'Blitz-событие',
        'short_description': 'Быстрая миссия с высокой плотностью боевых действий.',
        'mission_description': 'Короткая операция с быстрым развёртыванием, ограниченным временем на планирование и высокой плотностью контактов. Основной акцент — скорость принятия решений и удержание темпа боя.',
        'server_name': 'ARMA-RUSSIAN | MAIN',
        'server_ip': '185.123.45.21',
        'server_port': 2001,
        'max_solo_players': 16,
    },
]

DEFAULT_SLOT_DEPARTMENTS = [
    {'name': 'Командование', 'total_slots': 3, 'order': 1},
    {'name': 'Пехотное отделение 1', 'total_slots': 8, 'order': 2},
    {'name': 'Пехотное отделение 2', 'total_slots': 8, 'order': 3},
    {'name': 'Разведка', 'total_slots': 4, 'order': 4},
    {'name': 'Экипаж техники', 'total_slots': 3, 'order': 5},
]

RULE_SECTIONS = [
    {
        'title': 'Общие правила',
        'rules': [
            'Уважайте других игроков.',
            'Запрещены оскорбления, провокации и токсичное поведение.',
            'Запрещено мешать игровому процессу другим участникам.',
        ],
    },
    {
        'title': 'Правила связи',
        'rules': [
            'Во время событий запрещено использовать сторонние каналы связи для передачи игровой информации.',
            'Используйте только разрешённые голосовые каналы.',
            'Не передавайте мета-информацию вне игры.',
        ],
    },
    {
        'title': 'Правила событий',
        'rules': [
            'Следуйте указаниям организаторов.',
            'Не покидайте событие без причины.',
            'Соблюдайте задачи своей стороны и своего отряда.',
        ],
    },
    {
        'title': 'Нарушения',
        'rules': [
            'За нарушение правил игрок может получить предупреждение, кик, временный бан или постоянный бан.',
            'Решение администрации зависит от тяжести нарушения.',
        ],
    },
]


def ensure_default_squads():
    for squad_data in DEFAULT_SQUADS:
        Squad.objects.get_or_create(slug=squad_data['slug'], defaults=squad_data)


def ensure_default_events():
    for event_data in DEFAULT_EVENTS:
        event, _ = Event.objects.get_or_create(slug=event_data['slug'], defaults=event_data)
        if not event.slot_departments.exists():
            for department_data in DEFAULT_SLOT_DEPARTMENTS:
                EventSlotDepartment.objects.create(event=event, **department_data)


def unique_squad_slug(name):
    base_slug = slugify(name, allow_unicode=True) or 'squad'
    slug = base_slug
    index = 2
    while Squad.objects.filter(slug=slug).exists():
        slug = f'{base_slug}-{index}'
        index += 1
    return slug


def get_user_membership(user, squad):
    if not user.is_authenticated:
        return None
    return SquadMembership.objects.filter(squad=squad, user=user).first()


def user_can_review(user, squad):
    membership = get_user_membership(user, squad)
    return bool(membership and membership.can_review_applications)


def user_can_edit(user, squad):
    membership = get_user_membership(user, squad)
    return bool(membership and membership.can_edit_squad)


def manageable_squads_for_user(user):
    if not user.is_authenticated:
        return Squad.objects.none()
    return Squad.objects.filter(
        members__user=user,
        members__role__in=[SquadMembership.ROLE_COMMANDER, SquadMembership.ROLE_DEPUTY],
    ).distinct()


def build_event_slot_table(event, manageable_squads=None):
    manageable_squads = manageable_squads or Squad.objects.none()
    departments = []
    for department in event.slot_departments.prefetch_related('assignments__squad'):
        assignments = {assignment.slot_number: assignment for assignment in department.assignments.all()}
        slots = [
            {
                'number': slot_number,
                'assignment': assignments.get(slot_number),
                'can_cancel': can_cancel_slot_assignment(
                    None,
                    assignments.get(slot_number),
                    manageable_squads,
                ),
            }
            for slot_number in department.slot_numbers
        ]
        departments.append(
            {
                'department': department,
                'total_slots': department.total_slots,
                'occupied_slots': len(assignments),
                'slots': slots,
            }
        )
    return departments


def can_cancel_slot_assignment(user, assignment, manageable_squads):
    if assignment is None:
        return False
    return manageable_squads.filter(id=assignment.squad_id).exists()


def user_is_approved(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return bool(user.is_active and profile and profile.is_approved)


def user_has_squad(user):
    if not user.is_authenticated:
        return False
    return SquadMembership.objects.filter(user=user).exists()


def home(request):
    return render(request, 'main/home.html', {'servers': SERVERS, 'active_page': 'home'})


def squads(request):
    ensure_default_squads()
    is_modal_open = False

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Чтобы зарегистрировать отряд, войдите в аккаунт.')
            return redirect('login')
        if not user_is_approved(request.user):
            messages.error(request, 'Регистрировать отряды могут только подтверждённые пользователи.')
            return redirect('profile')

        form = SquadApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.owner = request.user
            application.save()

            squad = Squad.objects.create(
                name=application.squad_name,
                slug=unique_squad_slug(application.squad_name),
                description=application.description,
                players_count=application.players_count,
                commander_name=application.commander_name,
                communication=application.contact,
                specialization='Отряд зарегистрирован через заявку сообщества.',
                schedule='Уточняется командиром отряда.',
                requirements='Наличие связи.\nГотовность соблюдать правила проекта.',
                owner=request.user,
            )
            SquadMembership.objects.create(
                squad=squad,
                user=request.user,
                display_name=application.commander_name,
                contact=application.contact,
                role=SquadMembership.ROLE_COMMANDER,
            )
            messages.success(request, 'Отряд зарегистрирован. Вы назначены командиром отряда.')
            return redirect('squad_manage', slug=squad.slug)

        messages.error(request, 'Проверьте поля формы и исправьте ошибки.')
        is_modal_open = True
    else:
        form = SquadApplicationForm()

    return render(
        request,
        'main/squads.html',
        {
            'squads': Squad.objects.all(),
            'form': form,
            'active_page': 'squads',
            'is_modal_open': is_modal_open,
        },
    )


def squad_detail(request, slug):
    ensure_default_squads()
    squad = get_object_or_404(Squad, slug=slug)

    is_join_modal_open = False
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Чтобы подать заявку в отряд, войдите в аккаунт.')
            return redirect('login')
        if not user_is_approved(request.user):
            messages.error(request, 'Подавать заявки в отряды могут только подтверждённые пользователи.')
            return redirect('profile')
        join_form = SquadJoinApplicationForm(request.POST, squad=squad, user=request.user)
        if join_form.is_valid():
            join_form.save()
            messages.success(request, 'Заявка на вступление отправлена')
            return redirect('squad_detail', slug=slug)
        messages.error(request, 'Проверьте поля заявки на вступление.')
        is_join_modal_open = True
    else:
        join_form = SquadJoinApplicationForm(squad=squad, user=request.user)

    return render(
        request,
        'main/squad_detail.html',
        {
            'squad': squad,
            'join_form': join_form,
            'active_page': 'squads',
            'is_join_modal_open': is_join_modal_open,
            'can_manage': user_can_review(request.user, squad),
            'can_edit': user_can_edit(request.user, squad),
        },
    )


@login_required
def squad_manage(request, slug):
    squad = get_object_or_404(Squad, slug=slug)
    membership = get_user_membership(request.user, squad)
    if not membership or not membership.can_review_applications:
        messages.error(request, 'У вас нет доступа к управлению этим отрядом.')
        return redirect('squad_detail', slug=slug)

    can_edit = membership.can_edit_squad
    edit_form = SquadEditForm(instance=squad)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_squad':
            if not can_edit:
                messages.error(request, 'Зам. командира может рассматривать заявки, но не изменять отряд.')
                return redirect('squad_manage', slug=slug)
            edit_form = SquadEditForm(request.POST, instance=squad)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Информация об отряде обновлена.')
                return redirect('squad_manage', slug=squad.slug)
            messages.error(request, 'Проверьте поля отряда.')

        elif action in {'accept_application', 'reject_application'}:
            application = get_object_or_404(
                SquadJoinApplication,
                id=request.POST.get('application_id'),
                squad=squad,
                status=SquadJoinApplication.STATUS_PENDING,
            )
            if action == 'accept_application':
                application.accept(request.user)
                squad.players_count = squad.players_count + 1
                squad.save(update_fields=['players_count'])
                messages.success(request, 'Заявка принята. Игрок добавлен в участники.')
            else:
                application.reject(request.user)
                messages.success(request, 'Заявка отклонена.')
            return redirect('squad_manage', slug=slug)

        elif action == 'update_member_role':
            if not can_edit:
                messages.error(request, 'Только командир может изменять роли участников.')
                return redirect('squad_manage', slug=slug)
            member = get_object_or_404(SquadMembership, id=request.POST.get('member_id'), squad=squad)
            new_role = request.POST.get('role')
            if new_role not in dict(SquadMembership.ROLE_CHOICES):
                messages.error(request, 'Некорректная роль участника.')
            else:
                member.role = new_role
                member.save(update_fields=['role'])
                messages.success(request, 'Роль участника обновлена.')
            return redirect('squad_manage', slug=slug)

    return render(
        request,
        'main/squad_manage.html',
        {
            'squad': squad,
            'edit_form': edit_form,
            'pending_applications': squad.join_applications.filter(status=SquadJoinApplication.STATUS_PENDING),
            'reviewed_applications': squad.join_applications.exclude(status=SquadJoinApplication.STATUS_PENDING)[:10],
            'members': squad.members.all(),
            'role_choices': SquadMembership.ROLE_CHOICES,
            'membership': membership,
            'can_edit': can_edit,
            'active_page': 'squads',
        },
    )


def events(request):
    ensure_default_events()
    return render(request, 'main/events.html', {'events': Event.objects.all(), 'active_page': 'events'})


def redirect_to_event_modal(slug, modal_id):
    return redirect(f'{reverse("event_detail", kwargs={"slug": slug})}?modal={modal_id}')


def event_detail(request, slug):
    ensure_default_events()
    event = get_object_or_404(Event, slug=slug)
    manageable_squads = manageable_squads_for_user(request.user)
    slot_squad = manageable_squads.first()
    managed_slot_assignments = EventSlotAssignment.objects.none()
    if slot_squad:
        managed_slot_assignments = EventSlotAssignment.objects.filter(
            department__event=event,
            squad=slot_squad,
        ).select_related('department', 'squad')
    squad_slot_form = EventConcreteSlotForm(
        event=event,
        user=request.user,
        manageable_squads=manageable_squads,
    )
    open_modal = request.GET.get('modal', '')
    user_solo_registration = (
        event.solo_registrations.filter(user=request.user).first()
        if request.user.is_authenticated
        else None
    )
    can_view_event_password = bool(
        event.server_password
        and request.user.is_authenticated
        and (
            request.user.is_staff
            or request.user.is_superuser
            or (event.password_visible_to_squads and user_has_squad(request.user))
            or (event.password_visible_to_solo and user_solo_registration)
        )
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if not request.user.is_authenticated:
            messages.error(request, 'Чтобы записаться на миссию, войдите в аккаунт.')
            return redirect('login')
        if not user_is_approved(request.user):
            messages.error(request, 'Запись на миссии доступна только подтверждённым пользователям.')
            return redirect('profile')
        if action == 'solo_registration':
            if not event.solo_registration_open:
                messages.error(request, 'Запись одиночных игроков на эту миссию закрыта.')
                return redirect('event_detail', slug=slug)
            profile_data = getattr(request.user, 'profile', None)
            if event.solo_registrations.filter(user=request.user).exists():
                messages.error(request, 'Вы уже зарегистрированы на эту миссию как одиночный игрок.')
                return redirect_to_event_modal(slug, 'solo-registration-modal')
            if event.solo_registrations.count() >= event.max_solo_players:
                messages.error(request, 'Свободных одиночных слотов на миссию больше нет.')
                return redirect_to_event_modal(slug, 'solo-registration-modal')
            if not profile_data:
                messages.error(request, 'Профиль игрока не найден.')
                return redirect('profile')

            EventSoloRegistration.objects.create(
                event=event,
                user=request.user,
                player_name=request.user.username,
                contact=profile_data.discord_username,
            )
            messages.success(request, 'Вы зарегистрированы на миссию как одиночный игрок.')
            return redirect('event_detail', slug=slug)

        elif action == 'squad_slot':
            if not event.squad_slotting_open:
                messages.error(request, 'Слоттинг отрядов на эту миссию закрыт.')
                return redirect_to_event_modal(slug, 'squad-slot-modal')
            squad_slot_form = EventConcreteSlotForm(
                request.POST,
                event=event,
                user=request.user,
                manageable_squads=manageable_squads,
            )
            if squad_slot_form.is_valid():
                squad_slot_form.save()
                messages.success(request, 'Выбранные слоты закреплены за отрядом.')
                return redirect('event_detail', slug=slug)
            messages.error(request, 'Проверьте поля слоттинга отряда.')
            open_modal = 'squad-slot-modal'

        elif action == 'cancel_solo_registration':
            deleted_count, _ = event.solo_registrations.filter(user=request.user).delete()
            if not deleted_count:
                messages.error(request, 'Одиночная регистрация не найдена.')
            return redirect('event_detail', slug=slug)

        elif action == 'cancel_squad_slot':
            assignment_id = request.POST.get('assignment_id')
            slot_assignment = EventSlotAssignment.objects.filter(
                id=assignment_id,
                department__event=event,
            ).first()

            if not can_cancel_slot_assignment(request.user, slot_assignment, manageable_squads):
                messages.error(request, 'Вы можете отменять только слоты своего отряда.')
                return redirect_to_event_modal(slug, 'squad-slot-modal')

            slot_assignment.delete()
            return redirect_to_event_modal(slug, 'squad-slot-modal')

    return render(
        request,
        'main/event_detail.html',
        {
            'event': event,
            'squad_slot_form': squad_slot_form,
            'solo_registrations': event.solo_registrations.select_related('user'),
            'slot_departments': build_event_slot_table(event, manageable_squads),
            'manageable_squads': manageable_squads,
            'slot_squad': slot_squad,
            'managed_slot_assignments': managed_slot_assignments,
            'user_solo_registration': user_solo_registration,
            'can_view_event_password': can_view_event_password,
            'open_modal': open_modal,
            'active_page': 'events',
        },
    )


def rules(request):
    return render(
        request,
        'main/rules.html',
        {'rule_sections': RULE_SECTIONS, 'active_page': 'rules'},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Вы вошли в аккаунт.')
            return redirect('home')
        messages.error(request, 'Неверное имя пользователя или пароль.')

    return render(request, 'main/login.html', {'form': form, 'active_page': 'login'})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Регистрация отправлена. Войти можно будет после подтверждения профиля администратором.',
            )
            return redirect('login')
        messages.error(request, 'Проверьте данные регистрации.')

    return render(request, 'main/register.html', {'form': form, 'active_page': 'register'})


@login_required
def profile(request):
    profile_data = getattr(request.user, 'profile', None)
    return render(
        request,
        'main/profile.html',
        {
            'active_page': 'profile',
            'profile_data': profile_data,
            'memberships': request.user.squad_memberships.select_related('squad'),
        },
    )


def logout_view(request):
    logout(request)
    messages.success(request, 'Вы вышли из аккаунта.')
    return redirect('home')
