from django.db import models
from django.contrib.auth.models import AbstractUser


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
