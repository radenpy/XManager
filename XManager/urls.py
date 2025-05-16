# XManager/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.core.views import (
    dashboard_view,
    login_view,
    choose_company,
    products_list_view,
    newsletters_list_view,
    sales_offers_list_view,
    logout_view
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Authentication views
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name='logout'),

    # Dashboard and core views
    path('', dashboard_view, name="home"),  # Root URL shows dashboard
    # Keep temporarily for compatibility
    path('dashboard/', dashboard_view, name="dashboard"),
    path('profile/', dashboard_view, name="profile"),
    path('settings/', dashboard_view, name="settings"),
    path('choose-company/', choose_company, name="choose_company"),

    # Legacy product views (można usunąć po pełnej migracji do nowych widoków)
    path('products-list/', products_list_view, name="products_list_view"),

    # App includes (nowy sposób organizacji URL-i)
    path('partner/', include('apps.partner.urls')),
    path('subscribers/', include('apps.subscriber.urls')),
    path('newsletter/', include('apps.newsletter.urls', namespace='newsletter')),

    # Nowa ścieżka dla produktów (używa nowego systemu widoków)
    path('products/', include('apps.product.urls', namespace='product')),

    # Inne legacy views (można przenieść do odpowiednich aplikacji w przyszłości)
    path('newsletters-list/', newsletters_list_view, name="newsletter_list_view"),
    path('sales-offers-list/', sales_offers_list_view,
         name="sales_offers_list_view"),
]

# Dodaj obsługę plików media w trybie deweloperskim
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
