from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'chat'

urlpatterns = [
path('', views.register, name='register'),
path('login/', views.user_login, name='login'),
path('logout/', views.custom_logout, name='logout'),

path('dashboard/', views.dashboard, name='dashboard'),

path('create-room/', views.create_room, name='create_room'),

path('chat/<uuid:room_id>/', views.chat_room, name='chat_room'),

path('send-message/<uuid:room_id>/', views.send_message, name='send_message'),

path('fetch-messages/<uuid:room_id>/', views.fetch_messages, name='fetch_messages'),

path('end-chat/<uuid:room_id>/', views.end_chat, name='end_chat'),

path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]

