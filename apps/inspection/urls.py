from django.urls import path
from . import views

urlpatterns = [
    # OCR识别
    path('ocr/driving-license/', views.OCRDrivingLicenseView.as_view(), name='ocr-driving-license'),
    path('ocr/license-plate/', views.OCRLicensePlateView.as_view(), name='ocr-license-plate'),
    
    # 检验记录 CRUD
    path('inspections/', views.InspectionListCreateView.as_view(), name='inspection-list-create'),
    path('inspections/<int:pk>/', views.InspectionDetailView.as_view(), name='inspection-detail'),
    path('inspections/<int:pk>/upload-image/', views.InspectionUploadImageView.as_view(), name='inspection-upload-image'),
    
    # 导出
    path('inspections/<int:pk>/export/', views.InspectionExportView.as_view(), name='inspection-export'),
    path('inspections/export-batch/', views.InspectionBatchExportView.as_view(), name='inspection-batch-export'),
]
