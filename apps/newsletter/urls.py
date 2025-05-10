from . import api
from . import views
from django.urls import path

app_name = 'newsletter'

urlpatterns = [
    # Newsletter Views
    path('', views.NewsletterListView.as_view(), name='newsletter_list'),
    path('create/', views.NewsletterCreateView.as_view(), name='newsletter_create'),

    # Template Views - Move these BEFORE the newsletter detail view
    path('templates/', views.NewsletterTemplateListView.as_view(),
         name='template_list'),
    path('templates/create/', views.NewsletterTemplateCreateView.as_view(),
         name='template_create'),
    path('templates/<int:pk>/',
         views.NewsletterTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/',
         views.NewsletterTemplateDeleteView.as_view(), name='template_delete'),
    path('templates/<int:pk>/preview/',
         views.NewsletterTemplatePreviewView.as_view(), name='template_preview'),
    path('newsletters/<slug:slug>/send/',
         views.NewsletterSendView.as_view(), name='newsletter_send'),

    # Newsletter detail views - These should come AFTER more specific patterns
    path('<slug:slug>/', views.NewsletterDetailView.as_view(),
         name='newsletter_detail'),
    path('<slug:slug>/update/', views.NewsletterUpdateView.as_view(),
         name='newsletter_update'),
    path('<slug:slug>/delete/', views.NewsletterDeleteView.as_view(),
         name='newsletter_delete'),
    path('<slug:slug>/preview/', views.NewsletterPreviewView.as_view(),
         name='newsletter_preview'),
    path('<slug:slug>/send-test/', views.NewsletterSendTestView.as_view(),
         name='newsletter_send_test'),

    # API endpoints
    path('api/subscribers/', api.get_subscribers, name='api_subscribers'),
    path('api/subscriber-groups/', api.get_subscriber_groups,
         name='api_subscriber_groups'),
    path('api/subscriber-groups/<int:group_id>/subscribers/',
         api.get_group_subscribers, name='api_group_subscribers'),
    path('api/subscribers/count/', api.get_subscribers_count,
         name='api_subscribers_count'),
    path('api/recipients/count/', api.get_recipients_count,
         name='api_recipients_count'),


]
