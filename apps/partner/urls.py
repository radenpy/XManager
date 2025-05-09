
from django.urls import path
from .import views, api


app_name = 'partner'

urlpatterns = [
    # Widoki stron
    path('', views.PartnerListView.as_view(), name='partner_list'),
    path('create/', views.partner_create_view, name='partner_create'),
    path('update/<int:pk>/', views.partner_update_view, name='partner_update'),
    path('delete/<int:pk>/', views.partner_delete_view, name='partner_delete'),
    path('verify-vat/<int:pk>/', views.verify_vat_view, name='verify_vat'),

    # API endpoints
    path('api/verify-vat/', api.VerifyVATAPIView.as_view(), name='verify_vat_api'),
    path('api/create/', api.PartnerCreateAPIView.as_view(),
         name='partner_create_api'),
    path('api/get/<int:partner_id>/',
         api.PartnerGetAPIView.as_view(), name='partner_get_api'),
    path('api/update/<int:partner_id>/',
         api.PartnerUpdateAPIView.as_view(), name='partner_update_api'),
    path('api/update-verification/<int:pk>/', api.UpdateVerificationAPIView.as_view(),
         name='partner_update_verification_api'),
    path('api/subscribers/lookup/', api.SubscriberLookupAPIView.as_view(),
         name='subscriber_lookup_api'),

    # Data fetching APIs
    path('api/fetch-mf-data/', views.fetch_mf_data, name='fetch_mf_data'),
    path('fetch_vies_data/', views.fetch_vies_data, name='fetch_vies_data'),



]
