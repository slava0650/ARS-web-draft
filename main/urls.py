from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('squads/', views.squads, name='squads'),
    path('squads/<str:slug>/manage/', views.squad_manage, name='squad_manage'),
    path('squads/<str:slug>/', views.squad_detail, name='squad_detail'),
    path('events/', views.events, name='events'),
    path('events/<str:slug>/', views.event_detail, name='event_detail'),
    path('rules/', views.rules, name='rules'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
