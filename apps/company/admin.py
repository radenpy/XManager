from django.contrib import admin
from .models import Company, UserProfile


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "tax_id", "is_active")
    search_fields = ("name", "tax_id")
    list_filter = ("is_active",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'active_company', 'default_company']
    list_filter = ['active_company', 'default_company']
    # list_display = ("user", "active_company")
    filter_horizontal = ("company",)
