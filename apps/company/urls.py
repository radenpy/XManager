from django.urls import path
from . import views
from apps.core.views import choose_company  # Dodaj ten import


app_name = 'company'

urlpatterns = [
    path('', views.CompanyListView.as_view(), name='company_list'),
    path('add/', views.CompanyCreateView.as_view(), name='company_create'),
    path('<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_update'),
    path('<int:pk>/delete/', views.CompanyDeleteView.as_view(),
         name='company_delete'),
    path('choose_company/', choose_company, name="choose_company"),

]
