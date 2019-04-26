from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('edit_password/', views.edit_password, name='edit_password'),
    path('change_email/', views.change_email, name='change_email'),
    path('confirm/<str:email>/<str:token>/', views.confirm_mail, name='confirm'),
    path('reset_password/', views.get_reset_password, name='get_reset_password'),
    path('reset_password/<str:email>/<str:token>/', views.reset_password, name='reset_password'),
    path('send_email_again/', views.send_email_again, name='send_email_again'),
]
