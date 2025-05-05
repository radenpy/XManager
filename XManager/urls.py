from django.contrib import admin
from django.urls import path, include

from apps.core.views import home_view
from apps.page.views import (
    dashboard_view,
    choose_context_view,
    products_list_view,
    newsletters_list_view,
    sales_offers_list_view
)
from apps.product.views import product_create_view

urlpatterns = [
    path('', home_view, name="home"),
    path('dashboard/', dashboard_view, name="dashboard"),
    path('dashboard/index/', dashboard_view, name="dashboard:index"),
    # Tymczasowo używamy dashboard_view
    path('profile/', dashboard_view, name="profile"),
    # Tymczasowo używamy dashboard_view
    path('settings/', dashboard_view, name="settings"),

    path('create/', product_create_view, name="products_create_view"),
    path('products-list/', products_list_view, name="products_list_view"),
    path('newsletters-list/', newsletters_list_view, name="newsletter_list_view"),
    path('sales-offers-list/', sales_offers_list_view,
         name="sales_offers_list_view"),
    path('choose-context/', choose_context_view, name="choose_context_view"),

    path('admin/', admin.site.urls),

    # Aplikacja Partners - używamy tylko jednego przyfisu URL
    path('partner/', include('apps.partner.urls')),
    # path('partner_list/', include('apps.partner.urls')),
    path('partner_detail/', include('apps.partner.urls')),

    # Aplikacja Subscribers
    path('subscribers/', include('apps.subscriber.urls')),

    # Aplikacja Reports - dodajemy zaślepki dla linków używanych w szablonie
    path('reports/monthly/', dashboard_view, name="reports:monthly"),
    path('reports/yearly/', dashboard_view, name="reports:yearly"),

    # Logowanie/wylogowywanie
    # Tymczasowo używamy dashboard_view
    path('logout/', dashboard_view, name="logout"),
]
