from django.urls import path
from apps.subscriber import views

app_name = 'subscribers'

urlpatterns = [
    # Subscriber list
    path('', views.SubscriberListView.as_view(), name='subscriber_list'),

    # Create subscriber
    path('create-form/', views.SubscriberCreateFormView.as_view(),
         name='subscriber_create_form'),
    path('create/', views.SubscriberCreateView.as_view(), name='subscriber_create'),

    # Update subscriber
    path('update/<int:pk>/', views.SubscriberUpdateView.as_view(),
         name='subscriber_update'),

    # Delete subscriber
    path('delete-confirm/<int:pk>/', views.SubscriberDeleteConfirmView.as_view(),
         name='subscriber_delete_confirm'),
    path('delete/<int:pk>/', views.SubscriberDeleteView.as_view(),
         name='subscriber_delete'),

    # Bulk operations
    path('bulk-group-assign/', views.SubscriberBulkGroupAssignView.as_view(),
         name='subscriber_bulk_group_assign'),

    # Subscriber groups
    path('groups/', views.SubscriberGroupListView.as_view(), name='group_list'),
    path('groups/create-form/', views.SubscriberGroupCreateFormView.as_view(),
         name='group_create_form'),
    path('groups/create/', views.SubscriberGroupCreateView.as_view(),
         name='group_create'),
    path('groups/update/<int:pk>/',
         views.SubscriberGroupUpdateView.as_view(), name='group_update'),
    path('groups/delete/<int:pk>/',
         views.SubscriberGroupDeleteView.as_view(), name='group_delete'),
    path('groups/view-subscribers/<int:pk>/',
         views.SubscriberGroupViewSubscribersView.as_view(), name='group_view_subscribers'),
    path('bulk-edit/', views.SubscriberBulkEditView.as_view(),
         name='subscriber_bulk_edit'),
    path('bulk-update/', views.SubscriberBulkUpdateView.as_view(),
         name='subscriber_bulk_update'),
    path('bulk-action/', views.SubscriberBulkActionView.as_view(),
         name='subscriber_bulk_action'),
    path('import/', views.SubscriberImportView.as_view(), name='subscriber_import'),



]
