from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import InspectionRecord
from .serializers import (
    InspectionListSerializer, 
    InspectionDetailSerializer, 
    InspectionCreateSerializer,
    OCRResultSerializer
)
from .services import OCRService, WordExportService
from .permissions import CanUseOCR


class OCRDrivingLicenseView(APIView):
    """OCR识别行驶证（正面/副页）"""
    permission_classes = [IsAuthenticated, CanUseOCR]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """
        识别行驶证图片，返回结构化数据
        """
        image = request.FILES.get('image')
        
        if not image:
            return Response({
                'code': 400,
                'message': '请上传图片',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件类型
        if not image.content_type.startswith('image/'):
            return Response({
                'code': 400,
                'message': '请上传图片文件',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件大小（最大5MB）
        if image.size > 5 * 1024 * 1024:
            return Response({
                'code': 400,
                'message': '图片大小不能超过5MB',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = OCRService.recognize_vehicle_license(image)
            result.pop('raw_data', None)
            return Response({
                'code': 200,
                'message': '识别成功',
                'data': result
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'识别失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OCRLicensePlateView(APIView):
    """OCR识别车牌号"""
    permission_classes = [IsAuthenticated, CanUseOCR]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """
        识别车牌图片，返回车牌号
        """
        image = request.FILES.get('image')
        
        if not image:
            return Response({
                'code': 400,
                'message': '请上传图片',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not image.content_type.startswith('image/'):
            return Response({
                'code': 400,
                'message': '请上传图片文件',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if image.size > 5 * 1024 * 1024:
            return Response({
                'code': 400,
                'message': '图片大小不能超过5MB',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = OCRService.recognize_car_number(image)
            result.pop('raw_data', None)
            return Response({
                'code': 200,
                'message': '识别成功',
                'data': {
                    'plate_number': result.get('license_plate_number', '')
                }
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'识别失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InspectionListCreateView(APIView):
    """检验记录列表/创建"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get(self, request):
        """
        获取检验记录列表（仅返回当前用户的记录）
        """
        queryset = InspectionRecord.objects.filter(created_by=request.user)
        
        # 搜索筛选
        keyword = request.query_params.get('keyword', '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(license_plate_number__icontains=keyword) |
                Q(owner__icontains=keyword) |
                Q(chassis_number__icontains=keyword)
            )
        
        # 日期筛选
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        
        total = queryset.count()
        results = InspectionListSerializer(queryset[start:end], many=True).data
        
        return Response({
            'code': 200,
            'message': 'success',
            'data': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'results': results
            }
        })
    
    def post(self, request):
        """
        创建检验记录
        """
        serializer = InspectionCreateSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(created_by=request.user)
            return Response({
                'code': 201,
                'message': '创建成功',
                'data': {
                    'id': instance.id,
                    'license_plate_number': instance.license_plate_number,
                    'created_at': instance.created_at.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'code': 400,
            'message': '参数错误',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class InspectionDetailView(APIView):
    """检验记录详情/更新/删除"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_object(self, pk, user):
        return get_object_or_404(InspectionRecord, pk=pk, created_by=user)
    
    def get(self, request, pk):
        """
        获取检验记录详情
        """
        obj = self.get_object(pk, request.user)
        return Response({
            'code': 200,
            'message': 'success',
            'data': InspectionDetailSerializer(obj).data
        })
    
    def put(self, request, pk):
        """
        更新检验记录
        """
        obj = self.get_object(pk, request.user)
        serializer = InspectionCreateSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'code': 200,
                'message': '更新成功',
                'data': {
                    'id': obj.id,
                    'license_plate_number': obj.license_plate_number,
                    'updated_at': obj.updated_at.isoformat()
                }
            })
        return Response({
            'code': 400,
            'message': '参数错误',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        删除检验记录
        """
        obj = self.get_object(pk, request.user)
        obj.delete()
        return Response({
            'code': 200,
            'message': '删除成功',
            'data': None
        })


class InspectionUploadImageView(APIView):
    """上传检验记录图片"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    # 允许的图片字段
    ALLOWED_FIELDS = [
        'license_front_image',
        'license_back_image', 
        'plate_image',
        'brake_report_image',
        'headlight_report_image'
    ]
    
    def post(self, request, pk):
        """
        上传单张图片到检验记录
        """
        obj = get_object_or_404(InspectionRecord, pk=pk, created_by=request.user)
        
        # 查找上传的图片字段
        uploaded_field = None
        uploaded_file = None
        for field in self.ALLOWED_FIELDS:
            if field in request.FILES:
                uploaded_field = field
                uploaded_file = request.FILES[field]
                break
        
        if not uploaded_field:
            return Response({
                'code': 400,
                'message': '请上传图片',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件类型
        if not uploaded_file.content_type.startswith('image/'):
            return Response({
                'code': 400,
                'message': '请上传图片文件',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证文件大小（最大5MB）
        if uploaded_file.size > 5 * 1024 * 1024:
            return Response({
                'code': 400,
                'message': '图片大小不能超过5MB',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 保存图片
        setattr(obj, uploaded_field, uploaded_file)
        obj.save(update_fields=[uploaded_field, 'updated_at'])
        
        return Response({
            'code': 200,
            'message': '上传成功',
            'data': {
                'id': obj.id,
                'field': uploaded_field
            }
        })


class InspectionExportView(APIView):
    """导出单个Word文档"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """
        导出单个检验记录为Word文档
        """
        obj = get_object_or_404(InspectionRecord, pk=pk, created_by=request.user)
        
        try:
            doc_buffer, filename = WordExportService.export_single(obj)
            response = HttpResponse(
                doc_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'导出失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InspectionBatchExportView(APIView):
    """批量导出ZIP"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        批量导出检验记录为ZIP压缩包
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'code': 400,
                'message': '请选择要导出的记录',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(ids) > 50:
            return Response({
                'code': 400,
                'message': '单次最多导出50条记录',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        records = InspectionRecord.objects.filter(id__in=ids, created_by=request.user)
        if not records.exists():
            return Response({
                'code': 404,
                'message': '未找到记录',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            zip_buffer, filename = WordExportService.export_batch(records)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'导出失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
