from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import TokenProxy
from .models import User, SystemConfig


# 取消注册不需要显示的模型
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'phone', 'role', 'is_active', 'date_joined']
    list_filter = ['is_superuser', 'role', 'is_active']
    search_fields = ['username', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('phone',)}),
        ('权限', {'fields': ('is_superuser', 'role', 'is_active')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'phone'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def has_module_permission(self, request):
        # 只有超级管理员能看到用户管理模块
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_readonly_fields(self, request, obj=None):
        return ['last_login', 'date_joined']


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """OCR配置后台管理"""
    list_display = ['id', 'name', 'access_key_id', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'remark']
    ordering = ['-is_active', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {'fields': ('name', 'remark')}),
        ('API凭证', {'fields': ('access_key_id', 'access_key_secret')}),
        ('状态', {'fields': ('is_active',)}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_module_permission(self, request):
        # 只有超级管理员能看到系统配置模块
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
