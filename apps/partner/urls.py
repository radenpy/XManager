from django.urls import path
from . import views

app_name = 'partner'

urlpatterns = [
    # Widoki stron
    path('', views.PartnerListView.as_view(), name='partner_list'),
    path('edit/<int:pk>/', views.PartnerUpdateView.as_view(), name='partner_update'),
    path('delete/<int:pk>/', views.PartnerDeleteView.as_view(),
         name='partner_delete'),

    # API endpoints
    path('api/verify-vat/', views.VerifyVATAPIView.as_view(), name='verify_vat_api'),
    path('api/create/', views.PartnerCreateAPIView.as_view(), name='partner_create'),
    path('api/get/<int:partner_id>/',
         views.PartnerGetAPIView.as_view(), name='partner_get'),
    path('api/update/<int:partner_id>/',
         views.PartnerUpdateAPIView.as_view(), name='partner_update_api'),
    path('api/subscribers/lookup/', views.SubscriberLookupAPIView.as_view(),
         name='subscriber_lookup_api'),
]
