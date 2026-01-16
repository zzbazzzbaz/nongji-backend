from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer


class LoginView(APIView):
    """用户登录"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'code': 400,
                'message': '用户名和密码不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        if not user:
            return Response({
                'code': 400,
                'message': '用户名或密码错误',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.is_active:
            return Response({
                'code': 403,
                'message': '账号已被禁用',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)
        
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token.key,
                'user': UserSerializer(user).data
            }
        })


class LogoutView(APIView):
    """退出登录"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        request.user.auth_token.delete()
        return Response({
            'code': 200,
            'message': '退出成功',
            'data': None
        })


class ProfileView(APIView):
    """获取当前用户信息"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'code': 200,
            'message': 'success',
            'data': UserSerializer(request.user).data
        })
