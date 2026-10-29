from django.shortcuts import render
from rest_framework.views import *
from rest_framework.request import HttpRequest
from rest_framework.serializers import ModelSerializer
from .models import *
from rest_framework import serializers
from django.contrib.auth.models import User, Group

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from wms import settings
from django.http import HttpRequest
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
from rest_framework import serializers

class ReceiveItem:
    code = ''
    current_count = 1
    total_count = 1
    damaged = False

    def __init__(self, code, current_count, total_count, damaged):
        self.code = code
        self.current_count = current_count
        self.total_count = total_count
        self.damaged = damaged

class ReceiveItemSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=12, min_length=10)
    current_count = serializers.IntegerField(min_value=1)
    total_count = serializers.IntegerField(min_value=1)
    damaged = serializers.BooleanField()


# Create your views here.
class GetReceiveShipmentProducts(APIView):
    def post(self, request: HttpRequest):

        if 'ship_id' not in request.data:
            return Response({'message': 'Provide ship_id', 
                             'type': 'error'}, status.HTTP_404_NOT_FOUND) 

        try:
            ship_id = request.data['ship_id']
            InboundShipmentID.objects.get(id=ship_id)

            products = InboundItemInShipment.objects.filter(ship_id=ship_id)

            p = []
            for i in products:
                p.append(ReceiveItem(i.product.id, i.available_count, i.total_count, i.damaged))

            if not products.exists():
                return Response({'message': 'Empty shipment id', 
                                             'type': 'error'}, status.HTTP_404_BAD_REQUEST) 

            s = ReceiveItemSerializer(p, many=True)

            return Response({'message': f'Selected shipment "{ship_id}"',
                             'type': 'info',
                             'products': s.data})
        except InboundShipmentID.DoesNotExist:
            return Response({'message': 'Invalid shipment id', 
                             'type': 'error'}, status.HTTP_400_BAD_REQUEST) 


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data.get('access')
        refresh_token = serializer.validated_data.get('refresh')

        response = Response({'message': 'Login successful'}, status=status.HTTP_200_OK)

        # CRITICAL: Attach cookies to response
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE_ACCESS'],
            value=access_token,
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            path='/',
        )
        response.set_cookie(
            key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            value=refresh_token,
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            path='/',
        )
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request: HttpRequest, *args, **kwargs):
        # get last known refresh_token
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])

        # Assign it to request.data so SimpleJWT's serializer can validate it
        if refresh_token:
            request.data['refresh'] = refresh_token

        serializer = self.get_serializer(data=request.data)
        response_data = self.validate_refresh_request(serializer)
        
        # Extract new refresh token
        new_refresh = response_data.pop('refresh', None)

        response = Response(response_data, status=status.HTTP_200_OK)

        # Update the HttpOnly cookie with rotated refresh token if applicable
        if new_refresh:
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
                value=new_refresh,
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],  # Set to True in production (HTTPS)
                path='/',
            )

        return response

    def validate_refresh_request(self, serializer):
        try:
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data
        except TokenError as e:
            raise InvalidToken(e.args[0])


class CookieLogoutView(APIView):
    def post(self, request):
        response = Response({'message': 'Logged out'}, status=status.HTTP_200_OK)
        # logout is just removing cookies with token
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_ACCESS'])
        response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        return response


def get_user_roles(user: User):
    if user.is_superuser:
        return [str(i) for i in Group.objects.all()]
    
    return [str(i) for i in user.groups.all()]


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest):
        user = request.user
        roles = get_user_roles(user)

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'roles': roles
        })