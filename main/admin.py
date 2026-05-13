from django.contrib import admin
from django.utils import timezone

from .models import (
    Event,
    EventSlotAssignment,
    EventSlotDepartment,
    EventSoloRegistration,
    EventSquadSlot,
    Squad,
    SquadApplication,
    SquadJoinApplication,
    SquadMembership,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved', 'steamid64', 'arma_id', 'discord_username', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__username', 'steamid64', 'arma_id', 'discord_username')
    readonly_fields = ('approved_by', 'approved_at', 'created_at')
    actions = ('approve_profiles', 'revoke_profiles')

    def save_model(self, request, obj, form, change):
        if obj.is_approved:
            if not obj.approved_at:
                obj.approved_at = timezone.now()
            if not obj.approved_by:
                obj.approved_by = request.user
            obj.user.is_active = True
        else:
            obj.approved_by = None
            obj.approved_at = None
            obj.user.is_active = False
        obj.user.save(update_fields=['is_active'])
        super().save_model(request, obj, form, change)

    @admin.action(description='Подтвердить выбранные профили')
    def approve_profiles(self, request, queryset):
        for profile in queryset:
            profile.approve(request.user)

    @admin.action(description='Снять подтверждение с выбранных профилей')
    def revoke_profiles(self, request, queryset):
        for profile in queryset:
            profile.revoke()


class SquadMembershipInline(admin.TabularInline):
    model = SquadMembership
    extra = 0
    fields = ('display_name', 'user', 'contact', 'role', 'joined_at')
    readonly_fields = ('joined_at',)


@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    list_display = ('name', 'recruitment_status', 'players_count', 'owner', 'created_at')
    list_filter = ('recruitment_status', 'created_at')
    search_fields = ('name', 'commander_name', 'communication')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (SquadMembershipInline,)


@admin.register(SquadApplication)
class SquadApplicationAdmin(admin.ModelAdmin):
    list_display = ('squad_name', 'commander_name', 'owner', 'contact', 'players_count', 'created_at')
    search_fields = ('squad_name', 'commander_name', 'contact', 'owner__username')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)


@admin.register(SquadJoinApplication)
class SquadJoinApplicationAdmin(admin.ModelAdmin):
    list_display = ('player_name', 'squad_name', 'status', 'contact', 'age', 'created_at')
    search_fields = ('player_name', 'squad_name', 'contact', 'user__username')
    list_filter = ('squad_name', 'status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(SquadMembership)
class SquadMembershipAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'squad', 'user', 'role', 'joined_at')
    list_filter = ('role', 'squad', 'joined_at')
    search_fields = ('display_name', 'contact', 'user__username', 'squad__name')


class EventSoloRegistrationInline(admin.TabularInline):
    model = EventSoloRegistration
    extra = 0
    readonly_fields = ('created_at',)


class EventSquadSlotInline(admin.TabularInline):
    model = EventSquadSlot
    extra = 0
    readonly_fields = ('created_at',)


class EventSlotDepartmentInline(admin.TabularInline):
    model = EventSlotDepartment
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'date_label',
        'time_label',
        'starts_at_unix',
        'event_type',
        'server_name',
        'solo_registration_open',
        'squad_slotting_open',
        'password_configured',
        'password_visible_to_squads',
        'password_visible_to_solo',
    )
    list_filter = (
        'event_type',
        'solo_registration_open',
        'squad_slotting_open',
        'password_visible_to_squads',
        'password_visible_to_solo',
        'created_at',
    )
    search_fields = ('title', 'server_name', 'server_ip')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (EventSlotDepartmentInline, EventSoloRegistrationInline, EventSquadSlotInline)

    @admin.display(boolean=True, description='Пароль указан')
    def password_configured(self, obj):
        return bool(obj.server_password)


@admin.register(EventSoloRegistration)
class EventSoloRegistrationAdmin(admin.ModelAdmin):
    list_display = ('player_name', 'event', 'user', 'contact', 'created_at')
    list_filter = ('event', 'created_at')
    search_fields = ('player_name', 'contact', 'user__username', 'event__title')


@admin.register(EventSquadSlot)
class EventSquadSlotAdmin(admin.ModelAdmin):
    list_display = ('squad', 'event', 'side', 'players_count', 'created_by', 'created_at')
    list_filter = ('event', 'squad', 'created_at')
    search_fields = ('squad__name', 'event__title', 'side')


@admin.register(EventSlotDepartment)
class EventSlotDepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'total_slots', 'occupied_slots_count', 'order')
    list_filter = ('event',)
    search_fields = ('name', 'event__title')


@admin.register(EventSlotAssignment)
class EventSlotAssignmentAdmin(admin.ModelAdmin):
    list_display = ('department', 'slot_number', 'squad', 'created_by', 'created_at')
    list_filter = ('department__event', 'department', 'squad')
    search_fields = ('department__name', 'squad__name', 'created_by__username')
