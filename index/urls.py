from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.main, name='index'),
    path('using_request', views.using_request, name='using_request')
]
