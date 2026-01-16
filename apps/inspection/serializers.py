from rest_framework import serializers
from .models import InspectionRecord


class InspectionListSerializer(serializers.ModelSerializer):
    """列表序列化器"""
    class Meta:
        model = InspectionRecord
        fields = [
            'id', 'license_plate_number', 'vehicle_type', 'owner', 
            'brand', 'model_name', 'created_at'
        ]


class InspectionDetailSerializer(serializers.ModelSerializer):
    """详情序列化器"""
    license_front_image = serializers.SerializerMethodField()
    license_back_image = serializers.SerializerMethodField()
    plate_image = serializers.SerializerMethodField()
    brake_report_image = serializers.SerializerMethodField()
    headlight_report_image = serializers.SerializerMethodField()
    
    class Meta:
        model = InspectionRecord
        exclude = ['created_by']
    
    def get_license_front_image(self, obj):
        return obj.license_front_image.url if obj.license_front_image else None
    
    def get_license_back_image(self, obj):
        return obj.license_back_image.url if obj.license_back_image else None
    
    def get_plate_image(self, obj):
        return obj.plate_image.url if obj.plate_image else None
    
    def get_brake_report_image(self, obj):
        return obj.brake_report_image.url if obj.brake_report_image else None
    
    def get_headlight_report_image(self, obj):
        return obj.headlight_report_image.url if obj.headlight_report_image else None


class InspectionCreateSerializer(serializers.ModelSerializer):
    """创建/更新序列化器"""
    class Meta:
        model = InspectionRecord
        exclude = ['created_by', 'created_at', 'updated_at']
    
    def validate_license_plate_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('号牌号码不能为空')
        return value.strip()


class OCRResultSerializer(serializers.Serializer):
    """OCR识别结果序列化器"""
    license_plate_number = serializers.CharField(allow_blank=True, default='')
    vehicle_type = serializers.CharField(allow_blank=True, default='')
    owner = serializers.CharField(allow_blank=True, default='')
    address = serializers.CharField(allow_blank=True, default='')
    chassis_number = serializers.CharField(allow_blank=True, default='')
    engine_number = serializers.CharField(allow_blank=True, default='')
    brand = serializers.CharField(allow_blank=True, default='')
    model_name = serializers.CharField(allow_blank=True, default='')
    registration_date = serializers.CharField(allow_blank=True, default='')
    issue_date = serializers.CharField(allow_blank=True, default='')
    issue_authority = serializers.CharField(allow_blank=True, default='')
    tractor_min_weight = serializers.CharField(allow_blank=True, default='')
    harvester_weight = serializers.CharField(allow_blank=True, default='')
    tractor_max_load = serializers.CharField(allow_blank=True, default='')
    passenger_capacity = serializers.CharField(allow_blank=True, default='')
    overall_dimension = serializers.CharField(allow_blank=True, default='')
    inspection_record = serializers.CharField(allow_blank=True, default='')
