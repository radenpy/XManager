# XManager/urls.py
from django.contrib import admin
from django.urls import path, include

from apps.core.views import (
    dashboard_view,
    login_view,
    choose_company,
    products_list_view,
    newsletters_list_view,
    sales_offers_list_view,
    logout_view
)
from apps.product.views import product_create_view

urlpatterns = [
    # Authentication views
    path('', dashboard_view, name="home"),  # Root URL shows dashboard
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name='logout'),

    path('admin/', admin.site.urls),

    # Keep dashboard path temporarily for compatibility
    path('dashboard/', dashboard_view, name="dashboard"),

    # Protected views
    path('profile/', dashboard_view, name="profile"),
    path('settings/', dashboard_view, name="settings"),
    path('choose-company/', choose_company, name="choose_company"),
    path('create/', product_create_view, name="products_create_view"),
    path('products-list/', products_list_view, name="products_list_view"),
    path('newsletters-list/', newsletters_list_view, name="newsletter_list_view"),
    path('sales-offers-list/', sales_offers_list_view,
         name="sales_offers_list_view"),

    # App includes
    path('partner/', include('apps.partner.urls')),
    path('subscribers/', include('apps.subscriber.urls')),
    # Aplikacja Newsletter

    path('newsletter/', include('apps.newsletter.urls', namespace='newsletter')),


]
