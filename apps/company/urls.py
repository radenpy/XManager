from django.urls import path
from . import views

urlpatterns = [
    path('choose-company/', views.choose_company, name='choose-company'),
]
