from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import (
    EventSlotAssignment,
    EventSoloRegistration,
    EventSquadSlot,
    Squad,
    SquadApplication,
    SquadJoinApplication,
    SquadMembership,
    UserProfile,
)


class StyledFormMixin:
    field_class = 'form-control'

    def apply_styles(self):
        for field in self.fields.values():
            classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{classes} {self.field_class}'.strip()


class SquadApplicationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SquadApplication
        fields = ('squad_name', 'commander_name', 'contact', 'players_count', 'description')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean_players_count(self):
        players_count = self.cleaned_data['players_count']
        if players_count < 1:
            raise forms.ValidationError('Укажите количество игроков больше нуля.')
        return players_count


class SquadJoinApplicationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SquadJoinApplication
        fields = ('player_name', 'contact', 'age', 'experience', 'message')
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.squad = kwargs.pop('squad', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.squad:
            instance.squad = self.squad
            instance.squad_name = self.squad.name
        if self.user and self.user.is_authenticated:
            instance.user = self.user
        if commit:
            instance.save()
        return instance

    def clean_age(self):
        age = self.cleaned_data['age']
        if age < 12:
            raise forms.ValidationError('Укажите корректный возраст.')
        return age


class SquadEditForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Squad
        fields = (
            'name',
            'description',
            'players_count',
            'recruitment_status',
            'commander_name',
            'specialization',
            'communication',
            'schedule',
            'requirements',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'specialization': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()


class MembershipRoleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SquadMembership
        fields = ('role',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()


class EventSoloRegistrationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = EventSoloRegistration
        fields = ('player_name', 'contact', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean(self):
        cleaned_data = super().clean()
        if EventSoloRegistration.objects.filter(event=self.event, user=self.user).exists():
            raise forms.ValidationError('Вы уже зарегистрированы на эту миссию как одиночный игрок.')
        if self.event.solo_registrations.count() >= self.event.max_solo_players:
            raise forms.ValidationError('Свободных одиночных слотов на миссию больше нет.')
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.event = self.event
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class EventSquadSlotForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = EventSquadSlot
        fields = ('squad', 'side', 'players_count', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.user = kwargs.pop('user')
        manageable_squads = kwargs.pop('manageable_squads')
        super().__init__(*args, **kwargs)
        self.fields['squad'].queryset = manageable_squads
        self.apply_styles()

    def clean(self):
        cleaned_data = super().clean()
        squad = cleaned_data.get('squad')
        if squad and EventSquadSlot.objects.filter(event=self.event, squad=squad).exists():
            raise forms.ValidationError('Этот отряд уже занял слот на миссии.')
        return cleaned_data

    def clean_players_count(self):
        players_count = self.cleaned_data['players_count']
        if players_count < 1:
            raise forms.ValidationError('Укажите количество игроков больше нуля.')
        return players_count

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.event = self.event
        instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class EventConcreteSlotForm(StyledFormMixin, forms.Form):
    slots = forms.MultipleChoiceField(
        label='Конкретные слоты',
        widget=forms.CheckboxSelectMultiple,
        help_text='Выберите один или несколько свободных слотов в нужных отделениях.',
    )
    comment = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.user = kwargs.pop('user')
        manageable_squads = kwargs.pop('manageable_squads')
        self.squad = manageable_squads.first()
        super().__init__(*args, **kwargs)

        choices = []
        occupied = set(
            EventSlotAssignment.objects.filter(department__event=self.event).values_list(
                'department_id',
                'slot_number',
            )
        )
        for department in self.event.slot_departments.all():
            for slot_number in department.slot_numbers:
                if (department.id, slot_number) not in occupied:
                    value = f'{department.id}:{slot_number}'
                    label = f'{department.name} — слот {slot_number}'
                    choices.append((value, label))
        self.fields['slots'].choices = choices
        self.apply_styles()

    def clean(self):
        cleaned_data = super().clean()
        if self.squad is None:
            raise forms.ValidationError('У вас нет отряда, которым можно занять слот.')
        return cleaned_data

    def clean_slots(self):
        slots = self.cleaned_data['slots']
        if not slots:
            raise forms.ValidationError('Выберите хотя бы один слот.')

        for slot_value in slots:
            department_id, slot_number = slot_value.split(':', 1)
            if EventSlotAssignment.objects.filter(
                department_id=department_id,
                slot_number=slot_number,
            ).exists():
                raise forms.ValidationError('Один из выбранных слотов уже занят.')
        return slots

    def save(self):
        comment = self.cleaned_data.get('comment', '')
        assignments = []
        for slot_value in self.cleaned_data['slots']:
            department_id, slot_number = slot_value.split(':', 1)
            assignments.append(
                EventSlotAssignment.objects.create(
                    department_id=department_id,
                    squad=self.squad,
                    slot_number=int(slot_number),
                    created_by=self.user,
                    comment=comment,
                )
            )
        return assignments


class LoginForm(StyledFormMixin, AuthenticationForm):
    error_messages = {
        'invalid_login': 'Неверное имя пользователя или пароль.',
        'inactive': 'Аккаунт ожидает подтверждения администратором.',
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password'].label = 'Пароль'
        self.apply_styles()

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user_model = get_user_model()
            try:
                user = user_model._default_manager.get_by_natural_key(username)
            except user_model.DoesNotExist:
                user = None
            if user and not user.is_active and user.check_password(password):
                raise ValidationError(self.error_messages['inactive'], code='inactive')

        return super().clean()


class RegisterForm(StyledFormMixin, UserCreationForm):
    steamid64 = forms.CharField(
        label='SteamID64',
        max_length=17,
        help_text='Укажите ваш SteamID64: 17 цифр.',
    )
    arma_id = forms.CharField(
        label='Arma ID',
        max_length=120,
        help_text='Укажите ваш Arma ID из Arma Reforger.',
    )
    discord_username = forms.CharField(
        label='Имя пользователя Discord',
        max_length=120,
        help_text='Укажите Discord username. Пользователь должен быть на сервере Discord ARMA-RUSSIAN.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повторите пароль'
        self.order_fields(['username', 'steamid64', 'arma_id', 'discord_username', 'password1', 'password2'])
        self.apply_styles()

    def clean_steamid64(self):
        steamid64 = self.cleaned_data['steamid64'].strip()
        if not steamid64.isdigit() or len(steamid64) != 17:
            raise forms.ValidationError('SteamID64 должен состоять ровно из 17 цифр.')
        if UserProfile.objects.filter(steamid64=steamid64).exists():
            raise forms.ValidationError('Этот SteamID64 уже используется.')
        return steamid64

    def clean_arma_id(self):
        arma_id = self.cleaned_data['arma_id'].strip()
        if UserProfile.objects.filter(arma_id__iexact=arma_id).exists():
            raise forms.ValidationError('Этот Arma ID уже используется.')
        return arma_id

    def clean_discord_username(self):
        discord_username = self.cleaned_data['discord_username'].strip()
        if UserProfile.objects.filter(discord_username__iexact=discord_username).exists():
            raise forms.ValidationError('Этот Discord username уже используется.')
        return discord_username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                steamid64=self.cleaned_data['steamid64'],
                arma_id=self.cleaned_data['arma_id'],
                discord_username=self.cleaned_data['discord_username'],
                is_approved=False,
            )
        return user
