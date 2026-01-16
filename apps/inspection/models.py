from django.db import models
from django.conf import settings


class InspectionRecord(models.Model):
    """检验记录 - 农机行驶证"""
    
    # ========== 正页信息 ==========
    license_plate_number = models.CharField(max_length=20, verbose_name='号牌号码', db_index=True)
    vehicle_type = models.CharField(max_length=50, blank=True, verbose_name='类型')
    owner = models.CharField(max_length=50, blank=True, verbose_name='所有人')
    address = models.CharField(max_length=200, blank=True, verbose_name='住址')
    chassis_number = models.CharField(max_length=50, blank=True, verbose_name='底盘号/机架号')
    trailer_frame_number = models.CharField(max_length=50, blank=True, verbose_name='挂车架号码')
    engine_number = models.CharField(max_length=50, blank=True, verbose_name='发动机号码')
    brand = models.CharField(max_length=50, blank=True, verbose_name='品牌')
    model_name = models.CharField(max_length=50, blank=True, verbose_name='型号名称')
    registration_date = models.DateField(null=True, blank=True, verbose_name='登记日期')
    issue_date = models.DateField(null=True, blank=True, verbose_name='发证日期')
    issue_authority = models.CharField(max_length=100, blank=True, verbose_name='发证机关')
    
    # ========== 副页信息 ==========
    tractor_min_weight = models.CharField(max_length=50, blank=True, verbose_name='拖拉机最小使用质量')
    harvester_weight = models.CharField(max_length=50, blank=True, verbose_name='联合收割机质量')
    tractor_max_load = models.CharField(max_length=50, blank=True, verbose_name='拖拉机最大允许载质量')
    passenger_capacity = models.CharField(max_length=20, blank=True, verbose_name='准乘人数')
    overall_dimension = models.CharField(max_length=50, blank=True, verbose_name='外廓尺寸(毫米)')
    inspection_record = models.CharField(max_length=200, blank=True, verbose_name='检验记录')
    
    # ========== 检验报告图片 ==========
    brake_report_image = models.ImageField(upload_to='inspection/brake/', blank=True, verbose_name='制动性能检验报告图片')
    headlight_report_image = models.ImageField(upload_to='inspection/headlight/', blank=True, verbose_name='前照灯检验报告图片')

    # ========== OCR上传图片 ==========
    license_front_image = models.ImageField(upload_to='inspection/license/', blank=True, verbose_name='行驶证正面图片')
    license_back_image = models.ImageField(upload_to='inspection/license/', blank=True, verbose_name='行驶证副页图片')
    plate_image = models.ImageField(upload_to='inspection/plate/', blank=True, verbose_name='车牌号图片')
    plate_ocr_result = models.CharField(max_length=50, blank=True, verbose_name='车牌识别结果')

    # ========== Word文档需要 ==========
    body_color = models.CharField(max_length=50, blank=True, verbose_name='机身颜色')
    production_date = models.DateField(null=True, blank=True, verbose_name='生产日期')
    
    # ========== 系统字段 ==========
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='inspections', 
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'inspection_record'
        verbose_name = '检验记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.license_plate_number} - {self.created_at.strftime('%Y-%m-%d') if self.created_at else ''}"
