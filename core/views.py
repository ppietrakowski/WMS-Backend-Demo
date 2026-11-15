from django.shortcuts import render
from rest_framework.views import *
from rest_framework.request import HttpRequest
from rest_framework.serializers import ModelSerializer
from .models import *

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
from django.contrib.auth.models import User, Group

class ReceiveItem:
    id = ''
    name = ''
    count = 1
    damaged = False

    def __init__(self, id, name, current_count, damaged):
        self.id = id
        self.name = name
        self.count = current_count
        self.damaged = damaged


class ReceiveItemSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=12, min_length=10)
    name = serializers.CharField(max_length=64, min_length=10)
    count = serializers.IntegerField(min_value=1)
    damaged = serializers.BooleanField()

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


class MoveDropzone(APIView):
    def post(self, request):
        containers, dropzone = request.data['containers'], request.data['dropzone']
        dz = Dropzone.objects.filter(pk=dropzone)

        if not dz.exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
            

        for container in containers:
            c = StorageUnit.objects.filter(pk=container)

            if c.exists():
                c = c.first()
                c.dropzone = dz.first()
                c.save()
        
        return Response(status=status.HTTP_200_OK)


class AddItemsContainer(APIView):
    def put(self, request):
        container, products = request.data['container'], request.data['products']

        c, created = StorageUnit.objects.get_or_create(id=container)

        for p in products:
            pr = ProductInContainer.objects.filter(product_id = p['product'], container=c)

            if pr.exists():
                pr.first().count += p['count']
                pr.first().save()
            else:
                ProductInContainer.objects.create(container=c, product=ProductCode.objects.get(pk=p['product']), count=p['count'])



        return Response(status=status.HTTP_200_OK)


class ContainerProducts(APIView):
    def post(self, request: HttpRequest):
        if 'container' not in request.data:
            return Response({'message': 'Provide container', 
                             'type': 'error'}, status.HTTP_404_NOT_FOUND) 

        container = request.data['container']
        products = ProductInContainer.objects.filter(container_id=container)

        
        if not products.exists():
            return Response({'products': []}) 

        p = []
        total_count = 0
        for i in products:
            total_count += i.count
            p.append(ReceiveItem(i.product.id, i.product.name, i.count, i.damaged))

        s = ReceiveItemSerializer(p, many=True)
        return Response({'products': s.data, 'total_count': total_count})


class CreateProduct(APIView):
    def post(self, request: HttpRequest):
        name = request.data['name']
        weight = request.data['weight']
        code, base_code = request.data['id']['code'], request.data['id']['baseCode']

        o, c = ProductCode.objects.get_or_create(id=base_code, defaults={
            'id': base_code,
            'name': name,
            'weight': weight
        })

        ProductCodeMapping.objects.get_or_create(product=o, code=base_code, defaults={
            'product': o,
            'code': base_code
        })

        ProductCodeMapping.objects.get_or_create(product=o, code=code, defaults={
                    'product': o,
                    'code': code
                })
        
        return Response(status=status.HTTP_200_OK)

