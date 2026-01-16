from rest_framework.permissions import BasePermission


class CanUseOCR(BasePermission):
    """检查用户是否有OCR权限"""
    message = '您没有OCR识别权限'
    
    def has_permission(self, request, view):
        return request.user.can_use_ocr
