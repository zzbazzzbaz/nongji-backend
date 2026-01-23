import io
import json
import os
import zipfile
from datetime import datetime
from django.conf import settings
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm


class OCRService:
    """OCR识别服务"""
    
    @staticmethod
    def _get_client():
        """获取阿里云OCR客户端，从数据库配置中读取API key"""
        from alibabacloud_ocr_api20210707.client import Client
        from alibabacloud_tea_openapi import models as open_api_models
        from apps.users.models import SystemConfig
        
        # 从数据库获取启用的OCR配置
        ocr_config = SystemConfig.get_active_config()
        if not ocr_config:
            raise ValueError('未配置OCR接口，请在后台管理中添加并启用OCR配置')
        
        config = open_api_models.Config(
            access_key_id=ocr_config.access_key_id,
            access_key_secret=ocr_config.access_key_secret,
            endpoint='ocr-api.cn-hangzhou.aliyuncs.com'
        )
        return Client(config)
    
    @classmethod
    def recognize_vehicle_license(cls, image_file):
        """
        识别行驶证（正面/副页）
        """
        from alibabacloud_ocr_api20210707 import models
        from alibabacloud_tea_util import models as util_models
        
        client = cls._get_client()
        
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        request = models.RecognizeVehicleLicenseRequest(body=image_file)
        runtime = util_models.RuntimeOptions()
        
        response = client.recognize_vehicle_license_with_options(request, runtime)
        result = json.loads(response.body.data)
        
        # 解析数据 - 结构是 data.face.data 和 data.back.data
        data = result.get('data', {})
        face_info = data.get('face', {})
        back_info = data.get('back', {})
        face_data = face_info.get('data', {}) if isinstance(face_info, dict) else {}
        back_data = back_info.get('data', {}) if isinstance(back_info, dict) else {}
        
        # 处理地址 - 去掉前缀"中华人民共和国拖拉机和联合收割机行驶证"
        address = face_data.get('address', '')
        if '行驶证' in address:
            address = address.split('行驶证')[-1]
        
        # 农机行驶证字段映射（与汽车行驶证不同）
        # OCR把 底盘号/机架号 识别为 model
        # OCR把 型号名称 识别为 vinCode
        return {
            'raw_data': result,
            # 正页信息
            'license_plate_number': face_data.get('licensePlateNumber', ''),
            'vehicle_type': face_data.get('vehicleType', ''),
            'owner': face_data.get('owner', ''),
            'address': address,
            'chassis_number': face_data.get('model', ''),  # 机架号
            'engine_number': face_data.get('engineNumber', ''),
            'brand': '',  # OCR无法识别品牌
            'model_name': face_data.get('vinCode', ''),  # 型号名称
            'registration_date': face_data.get('registrationDate', ''),
            'issue_date': face_data.get('issueDate', ''),
            'issue_authority': face_data.get('issueAuthority', ''),
            # 副页信息
            'tractor_min_weight': back_data.get('curbWeight', ''),
            'harvester_weight': back_data.get('totalWeight', ''),  # 联合收割机质量
            'tractor_max_load': back_data.get('permittedWeight', ''),
            'passenger_capacity': back_data.get('passengerCapacity', ''),
            'overall_dimension': back_data.get('overallDimension', ''),
            'inspection_record': back_data.get('inspectionRecord', ''),
        }
    
    @classmethod
    def recognize_car_number(cls, image_file):
        """
        识别车牌号
        :param image_file: 图片文件对象
        :return: 识别结果字典
        """
        from alibabacloud_ocr_api20210707 import models
        from alibabacloud_tea_util import models as util_models
        
        client = cls._get_client()
        
        # 重置文件指针
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        request = models.RecognizeCarNumberRequest(body=image_file)
        runtime = util_models.RuntimeOptions()
        
        response = client.recognize_car_number_with_options(request, runtime)
        result = json.loads(response.body.data)
        
        # 提取车牌号
        plates = result.get('data', [])
        plate_number = plates[0].get('plateNumber', '') if plates else ''
        
        return {
            'raw_data': result,
            'license_plate_number': plate_number,
        }


class WordExportService:
    """Word文档导出服务 - 基于docxtpl模板引擎"""
    
    # 模板文件路径
    TEMPLATE_PATH = os.path.join(
        os.path.dirname(__file__), 
        'templates', 
        'inspection_template.docx'
    )
    
    @staticmethod
    def _format_date(date_obj, fmt='%Y-%m-%d'):
        """格式化日期"""
        if date_obj:
            return date_obj.strftime(fmt)
        return ''
    
    @staticmethod
    def _get_image_path(image_field):
        """获取图片的绝对路径"""
        if image_field and image_field.name:
            try:
                return image_field.path
            except Exception:
                return os.path.join(settings.MEDIA_ROOT, image_field.name)
        return None
    
    @classmethod
    def export_single(cls, record):
        """
        导出单个检验记录为Word文档
        使用docxtpl模板引擎，支持占位符替换和图片插入
        """
        # 加载模板
        doc = DocxTemplate(cls.TEMPLATE_PATH)
        
        # 准备上下文数据
        context = {
            # 基本信息
            'license_plate_number': record.license_plate_number or '',
            'vehicle_type': record.vehicle_type or '',
            'owner': record.owner or '',
            'address': record.address or '',
            'chassis_number': record.chassis_number or '',
            'trailer_frame_number': record.trailer_frame_number or '',
            'engine_number': record.engine_number or '',
            'brand': record.brand or '',
            'model_name': record.model_name or '',
            'body_color': record.body_color or '',
            'overall_dimension': record.overall_dimension or '',
            
            # 日期字段
            'production_date': cls._format_date(record.production_date),
            'registration_date': cls._format_date(record.registration_date),
            'issue_date': cls._format_date(record.issue_date),
            'created_at': cls._format_date(record.created_at, '%Y-%m-%d'),
            
            # 质量参数
            'tractor_min_weight': record.tractor_min_weight or '',
            'harvester_weight': record.harvester_weight or '',
            'tractor_max_load': record.tractor_max_load or '',
            'passenger_capacity': record.passenger_capacity or '',
            
            # 检验记录
            'inspection_record': record.inspection_record or '',
            'issue_authority': record.issue_authority or '',
        }
        
        # 处理图片 - 制动性能检验报告
        brake_image_path = cls._get_image_path(record.brake_report_image)
        if brake_image_path and os.path.exists(brake_image_path):
            context['brake_report_image'] = InlineImage(
                doc, brake_image_path, width=Mm(150)
            )
        else:
            context['brake_report_image'] = ''
        
        # 处理图片 - 前照灯检验报告
        headlight_image_path = cls._get_image_path(record.headlight_report_image)
        if headlight_image_path and os.path.exists(headlight_image_path):
            context['headlight_report_image'] = InlineImage(
                doc, headlight_image_path, width=Mm(150)
            )
        else:
            context['headlight_report_image'] = ''
        
        # 渲染模板
        doc.render(context)
        
        # 保存到内存
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        # 生成文件名：id_车牌号_时间
        date_str = record.created_at.strftime('%Y-%m-%d') if record.created_at else datetime.now().strftime('%Y-%m-%d')
        plate = record.license_plate_number or 'null'
        filename = f"{record.id}_{plate}_{date_str}.docx"
        
        return buffer, filename
    
    @classmethod
    def export_batch(cls, records):
        """批量导出为ZIP压缩包"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for record in records:
                doc_buffer, filename = cls.export_single(record)
                zip_file.writestr(filename, doc_buffer.getvalue())
        
        zip_buffer.seek(0)
        filename = f"检验记录_{datetime.now().strftime('%Y-%m-%d')}.zip"
        
        return zip_buffer, filename
