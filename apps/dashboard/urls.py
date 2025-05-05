
# from django.urls import path
# from django.contrib.auth.views import LoginView, LogoutView
# from apps.companies.views import choose_company
# from . import views

# app_name = 'dashboard'

# urlpatterns = [
#     path('', views.home, name='home'),
#     path('choose-company/', choose_company, name='choose-company'),
#     path('login/', LoginView.as_view(template_name='dashboard/login.html'), name='login'),
#     path('logout/', LogoutView.as_view(next_page='dashboard:login'), name='logout'),
# ]

from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('choose-company/', views.choose_company,
         name='choose-company'),  # Widok wyboru firmy
]
