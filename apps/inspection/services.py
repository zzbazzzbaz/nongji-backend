import io
import json
import zipfile
from datetime import datetime
from django.conf import settings
from docx import Document


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
    """Word文档导出服务"""
    
    @staticmethod
    def export_single(record):
        """导出单个检验记录为Word文档"""
        doc = Document()
        
        # 标题
        doc.add_heading('农机安全技术检验合格证明', 0)
        
        # 基本信息表格
        table = doc.add_table(rows=12, cols=4)
        table.style = 'Table Grid'
        
        fields = [
            ('号牌号码', record.license_plate_number, '类型', record.vehicle_type),
            ('所有人', record.owner, '住址', record.address),
            ('底盘号/机架号', record.chassis_number, '发动机号码', record.engine_number),
            ('品牌', record.brand, '型号', record.model_name),
            ('机身颜色', record.body_color, '生产日期', str(record.production_date or '')),
            ('登记日期', str(record.registration_date or ''), '发证日期', str(record.issue_date or '')),
            ('发证机关', record.issue_authority, '', ''),
            ('拖拉机最小使用质量', record.tractor_min_weight, '联合收割机质量', record.harvester_weight),
            ('拖拉机最大允许载质量', record.tractor_max_load, '准乘人数', record.passenger_capacity),
            ('外廓尺寸(毫米)', record.overall_dimension, '', ''),
            ('检验记录', record.inspection_record, '', ''),
        ]
        
        for i, (label1, value1, label2, value2) in enumerate(fields):
            row = table.rows[i]
            row.cells[0].text = label1
            row.cells[1].text = str(value1) if value1 else ''
            row.cells[2].text = label2
            row.cells[3].text = str(value2) if value2 else ''
        
        # 保存到内存
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        date_str = record.created_at.strftime('%Y-%m-%d') if record.created_at else datetime.now().strftime('%Y-%m-%d')
        filename = f"{record.license_plate_number}_{date_str}.docx"
        
        return buffer, filename
    
    @staticmethod
    def export_batch(records):
        """批量导出为ZIP"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for record in records:
                doc_buffer, filename = WordExportService.export_single(record)
                zip_file.writestr(filename, doc_buffer.getvalue())
        
        zip_buffer.seek(0)
        filename = f"检验记录_{datetime.now().strftime('%Y-%m-%d')}.zip"
        
        return zip_buffer, filename
