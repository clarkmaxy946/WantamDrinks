# branches/admin.py
from django.contrib import admin
from .models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch_id', 'manager_name', 'manager_phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'branch_id', 'manager_name')
    readonly_fields = ('branch_id', 'created_at')