# apps/product/urls.py
from django.urls import path
from apps.product import views

app_name = 'product'

urlpatterns = [
    # Podstawowe URL-e dla produktów
    path('', views.ProductListView.as_view(), name='product_list'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/update/', views.ProductUpdateView.as_view(),
         name='product_update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(),
         name='product_delete'),

    # URL-e dla akcji masowych
    path('bulk-action/', views.product_bulk_action, name='product_bulk_action'),
    path('bulk-edit/', views.product_bulk_edit, name='product_bulk_edit'),

    # URL-e dla kategorii
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(),
         name='category_create'),
    path('categories/<int:pk>/update/',
         views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/',
         views.CategoryDeleteView.as_view(), name='category_delete'),

    # URL-e dla marek
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<int:pk>/update/',
         views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<int:pk>/delete/',
         views.BrandDeleteView.as_view(), name='brand_delete'),
]
