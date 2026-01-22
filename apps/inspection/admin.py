from django.contrib import admin
from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import InspectionRecord
from .services import OCRService, WordExportService


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ['license_plate_number', 'owner', 'vehicle_type', 'brand', 'created_by', 'created_at', 'export_link']
    list_filter = ['vehicle_type', 'created_at']
    search_fields = ['license_plate_number', 'owner', 'chassis_number', 'engine_number']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'ocr_button']
    date_hierarchy = 'created_at'
    actions = ['export_selected_records']
    
    class Media:
        js = ('admin/js/ocr_recognize.js',)
    
    fieldsets = (
        ('OCR识别', {
            'fields': ('ocr_button',),
            'classes': ('wide',),
        }),
        ('图片资料', {
            'fields': ('license_front_image', 'license_back_image', 'plate_image'),
        }),
        ('正页信息', {
            'fields': (
                'license_plate_number', 'vehicle_type', 'owner', 'address',
                'chassis_number', 'trailer_frame_number', 'engine_number',
                'brand', 'model_name', 'registration_date', 'issue_date', 'issue_authority'
            )
        }),
        ('副页信息', {
            'fields': (
                'tractor_min_weight', 'harvester_weight', 'tractor_max_load',
                'passenger_capacity', 'overall_dimension', 'inspection_record'
            )
        }),
        ('检验报告', {
            'fields': ('brake_report_image', 'headlight_report_image')
        }),
        ('其他信息', {
            'fields': ('body_color', 'production_date')
        }),
        ('系统信息', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def ocr_button(self, obj):
        # 根据用户权限动态显示OCR按钮
        return mark_safe('''
            <div style="margin: 10px 0;">
                <button type="button" id="ocr-btn" onclick="doOCR()" 
                    style="padding: 10px 20px; background: #417690; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                    🔍 OCR识别
                </button>
                <span style="margin-left: 10px; color: #666;">上传图片后点击识别，自动填充表单</span>
            </div>
        ''')
    ocr_button.short_description = '操作'
    
    def get_fieldsets(self, request, obj=None):
        """根据用户权限动态调整fieldsets，非OCR用户不显示OCR识别区域"""
        fieldsets = super().get_fieldsets(request, obj)
        
        # 如果用户没有OCR权限，移除OCR识别区域
        if not request.user.can_use_ocr:
            fieldsets = [fs for fs in fieldsets if fs[0] != 'OCR识别']
        
        return fieldsets
    
    def has_module_permission(self, request):
        """所有已登录用户都可以看到检验管理模块"""
        return request.user.is_authenticated
    
    def has_view_permission(self, request, obj=None):
        """所有已登录用户都可以查看"""
        if request.user.is_superuser:
            return True
        if obj is not None:
            return obj.created_by == request.user
        return True
    
    def has_add_permission(self, request):
        """所有已登录用户都可以新增"""
        return request.user.is_authenticated
    
    def export_link(self, obj):
        return format_html(
            '<a href="/api/v1/inspections/{}/export/" target="_blank">导出</a>',
            obj.pk
        )
    export_link.short_description = '导出'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('ocr-recognize/', self.admin_site.admin_view(self.ocr_recognize_view), name='inspection_ocr_recognize'),
        ]
        return custom_urls + urls
    
    def ocr_recognize_view(self, request):
        """OCR识别接口"""
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': '仅支持POST请求'})
        
        if not request.user.can_use_ocr:
            return JsonResponse({'success': False, 'message': '您没有OCR识别权限'})
        
        result = {}
        
        # 识别行驶证正面
        license_front = request.FILES.get('license_front_image')
        if license_front:
            try:
                ocr_result = OCRService.recognize_vehicle_license(license_front)
                ocr_result.pop('raw_data', None)
                result.update(ocr_result)
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'行驶证正面识别失败: {str(e)}'})
        
        # 识别行驶证副页
        license_back = request.FILES.get('license_back_image')
        if license_back:
            try:
                ocr_result = OCRService.recognize_vehicle_license(license_back)
                ocr_result.pop('raw_data', None)
                # 副页主要提取这些字段
                for key in ['tractor_min_weight', 'harvester_weight', 'tractor_max_load', 
                           'passenger_capacity', 'overall_dimension', 'inspection_record']:
                    if ocr_result.get(key):
                        result[key] = ocr_result[key]
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'行驶证副页识别失败: {str(e)}'})
        
        # 识别车牌
        plate_image = request.FILES.get('plate_image')
        if plate_image:
            try:
                ocr_result = OCRService.recognize_car_number(plate_image)
                ocr_result.pop('raw_data', None)
                if ocr_result.get('license_plate_number'):
                    result['plate_ocr_result'] = ocr_result['license_plate_number']
                    if not result.get('license_plate_number'):
                        result['license_plate_number'] = ocr_result['license_plate_number']
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'车牌识别失败: {str(e)}'})
        
        if not result:
            return JsonResponse({'success': False, 'message': '请先上传图片'})
        
        return JsonResponse({'success': True, 'data': result})
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is not None:
            return obj.created_by == request.user
        return True
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is not None:
            return obj.created_by == request.user
        return True
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """根据用户权限动态调整只读字段"""
        readonly = list(super().get_readonly_fields(request, obj))
        # 如果用户没有OCR权限，不显示ocr_button
        if not request.user.can_use_ocr and 'ocr_button' in readonly:
            readonly.remove('ocr_button')
        return readonly
    
    @admin.action(description='导出选中记录为Word文档')
    def export_selected_records(self, request, queryset):
        """批量导出选中的检验记录为Word文档（ZIP压缩包）"""
        if queryset.count() == 1:
            # 单条记录直接导出Word
            record = queryset.first()
            try:
                doc_buffer, filename = WordExportService.export_single(record)
                response = HttpResponse(
                    doc_buffer.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except Exception as e:
                self.message_user(request, f'导出失败: {str(e)}', level='error')
                return
        else:
            # 多条记录导出ZIP
            try:
                zip_buffer, filename = WordExportService.export_batch(queryset)
                response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except Exception as e:
                self.message_user(request, f'批量导出失败: {str(e)}', level='error')
                return
