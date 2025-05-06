from django.urls import path
from apps.subscriber import views

app_name = 'subscribers'

urlpatterns = [
    # Subskrybenci
    path('', views.SubscriberListView.as_view(), name='subscriber_list'),
    path('create/', views.SubscriberCreateView.as_view(), name='subscriber_create'),
    path('update/<int:pk>/', views.SubscriberUpdateView.as_view(),
         name='subscriber_update'),
    path('delete/<int:pk>/', views.SubscriberDeleteView.as_view(),
         name='subscriber_delete'),

    # Grupy subskrybentów
    path('groups/', views.SubscriberGroupListView.as_view(),
         name='group_list'),  # Zmieniona nazwa
    path('groups/create/', views.SubscriberGroupCreateView.as_view(),
         name='group_create'),  # Zmieniona nazwa
    path('groups/update/', views.SubscriberGroupUpdateView.as_view(),
         name='group_update'),  # Zmieniona nazwa
    path('groups/delete/<int:pk>/', views.SubscriberGroupDeleteView.as_view(),
         name='group_delete'),  # Zmieniona nazwa

    # Hurtowe operacje
    path('bulk-group-assign/', views.SubscriberBulkGroupAssignView.as_view(),
         name='subscriber_bulk_group_assign'),

    # API
    path('api/lookup/', views.SubscriberLookupAPIView.as_view(),
         name='subscriber_lookup_api'),
    path('api/<int:pk>/', views.SubscriberDetailAPIView.as_view(),
         name='subscriber_api_detail'),

]
