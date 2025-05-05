from django.urls import path
from . import views

app_name = 'subscribers'

urlpatterns = [
    path('', views.SubscriberListView.as_view(), name='subscriber_list'),
    path('<int:pk>/', views.SubscriberDetailView.as_view(),
         name='subscriber_detail'),
    path('create/', views.SubscriberCreateView.as_view(), name='subscriber_create'),
    path('update/<int:pk>/', views.SubscriberUpdateView.as_view(),
         name='subscriber_update'),
    path('delete/<int:pk>/', views.SubscriberDeleteView.as_view(),
         name='subscriber_delete'),

    # API
    path('api/lookup/', views.SubscriberLookupAPIView.as_view(),
         name='subscriber_lookup_api'),
]
