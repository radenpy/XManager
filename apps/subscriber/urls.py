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
         name='subscriber_group_list'),
    path('groups/create/', views.SubscriberGroupCreateView.as_view(),
         name='subscriber_group_create'),
    path('groups/update/', views.SubscriberGroupUpdateView.as_view(),
         name='subscriber_group_update'),
    path('groups/delete/<int:pk>/', views.SubscriberGroupDeleteView.as_view(),
         name='subscriber_group_delete'),

    # Hurtowe operacje
    path('bulk-group-assign/', views.SubscriberBulkGroupAssignView.as_view(),
         name='subscriber_bulk_group_assign'),

    # API
    path('api/lookup/', views.SubscriberLookupAPIView.as_view(),
         name='subscriber_lookup_api'),
]
