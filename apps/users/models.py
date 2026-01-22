from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """自定义用户模型"""
    
    class Role(models.TextChoices):
        OCR_USER = 'ocr_user', 'OCR用户'
        NORMAL_USER = 'normal_user', '普通用户'
    
    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.NORMAL_USER, 
        verbose_name='角色'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    is_staff = models.BooleanField(default=True, verbose_name='允许登录后台')
    
    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
    
    @property
    def can_use_ocr(self):
        """是否可以使用OCR功能"""
        return self.is_superuser or self.role == self.Role.OCR_USER


class SystemConfig(models.Model):
    """系统配置模型 - OCR接口配置"""
    
    name = models.CharField(max_length=100, verbose_name='配置名称')
    access_key_id = models.CharField(max_length=200, verbose_name='AccessKeyId')
    access_key_secret = models.CharField(max_length=200, verbose_name='AccessKeySecret')
    is_active = models.BooleanField(default=False, verbose_name='是否启用')
    remark = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'system_config'
        verbose_name = 'OCR配置'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.name} {'(启用)' if self.is_active else ''}"
    
    def clean(self):
        """验证只能有一条启用的记录"""
        if self.is_active:
            # 查找其他启用的记录（排除自身）
            qs = SystemConfig.objects.filter(is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError('只能启用一条OCR配置记录，请先禁用其他配置')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """获取当前启用的OCR配置"""
        return cls.objects.filter(is_active=True).first()
