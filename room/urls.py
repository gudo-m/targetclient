from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.main, name='room_main'),
    path('roots/', views.roots, name='room_roots'),
    path('roots/<int:page_num>/', views.roots, name='room_roots'),
    path('clients/', views.clients, name='room_clients'),
    path('clients/<int:page_num>/', views.clients, name='room_clients'),
    path('add_group/', views.add_group, name='add_group'),
    path('comments/', views.comments, name='room_comments'),
    path('comments/<int:page_num>/', views.comments, name='room_comments'),
    path('delete_group/<str:gr_id>/', views.delete_group, name='delete_group'),
    path('delete_client/<str:uid>/', views.delete_client, name='delete_client'),
    path('spam/', views.spam, name='room_spam'),
    path('dialogs/<int:vk_acc_id>/', views.dialogs, name='room_dialogs'),
    path('delete_dialog/', views.delete_dialog, name='delete_dialog'),
    path('dialogs/<int:vk_acc_id>/page/<int:page_num>/', views.dialogs, name='room_dialogs'),
    path('dialogs/<int:vk_acc_id>/dialog<int:dialog_id>/', views.dialog, name='room_dialog'),
    path('start_spam/', views.start_spam, name='start_spam'),
    path('select_client/', views.select_client, name='select_client'),
    path('history/', views.history, name='history'),
    path('send_message/', views.send_message, name='send_message'),
    path('add_vk_account/', views.add_vk_account, name='add_vk_account'),
    path('delete_vk_account/', views.delete_vk_account, name='delete_vk_account'),
    path('delete_comment/', views.delete_comment, name='delete_comment'),
    path('select_comment/', views.select_comment, name='select_comment'),
    path('visit_client/', views.visit_client, name='visit_client'),
    path('visit_comment/', views.visit_comment, name='visit_comment'),
    path('check_roots/', views.check_roots, name='check_roots'),
]