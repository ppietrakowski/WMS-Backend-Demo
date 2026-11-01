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

# Create your views here.
class IndexView(APIView):
    def get(self, request):
        return Response({'status': 'ok'})

class ProductCodeSerializer(ModelSerializer):
    class Meta:
        model = ProductCode
        fields = '__all__'

class ProductCodeView(APIView):
    def get(self, request: HttpRequest, product_id: str):
        o = ProductCode.objects.filter(pk = product_id)

        if not o.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(ProductCodeSerializer(o.first(), many=False).data)
            
class ObjectInContainerSerializer(ModelSerializer):
    class Meta:
        model = ObjectInContainer
        fields = ['product', 'status', 'count', 'ship', 'damaged']

class ContainerItemsView(APIView):
    def get(self, request: HttpRequest, container_id: str):
        objects_in_container = None

        if container_id.startswith('ts'):
            objects_in_container = ObjectInContainer.objects.filter(tote_id=container_id)
        elif container_id.startswith('cs'):
            objects_in_container = ObjectInContainer.objects.filter(container_id=container_id)
        elif container_id.startswith('lo'):
            objects_in_container = ObjectInContainer.objects.filter(location_id=container_id)

        if not objects_in_container or not objects_in_container.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = ObjectInContainerSerializer(objects_in_container, many=True).data

        return_data = {}
        return_data['products'] = data
        return_data['container'] = container_id

        return Response(return_data, status=status.HTTP_200_OK)


class AddItemToContainerView(APIView):
    def post(self, request: HttpRequest, container_id: str):
        objects, created = None, False

        if 'damaged' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if 'product' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if 'count' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)

        objects, created = ProductInContainer.objects.get_or_create(product_id=request.data['product'], container_id=container_id, defaults={'count': int(request.data['count']), 'damaged': request.data['damaged']})

        if not created:
            if request.data['damaged'] != objects.damaged:
               return Response(status=status.HTTP_403_FORBIDDEN)
            objects.count += int(request.data['count'])
            objects.save()

        return Response('ok', status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class RemoveItemFromContainer(APIView):
    def delete(self, request: HttpRequest, container_id: str):
        if 'product' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)

        count = 1
        if 'count' in request.data:
            count = int(request.data['count'])

        objects = []

        if container_id.startswith('ts'):
            objects = ObjectInContainer.objects.filter(tote_id=container_id)

        return Response(status=status.HTTP_200_OK)


    

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


class MoveProductToNewContainer(APIView):
    permission_classes = []
    def post(self, request: HttpRequest):
        if not self.has_required_properties(request):
            return Response({'message': 'Provide valid properties', 'type': 'error'}, status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            return self._stow_item(request)
        

    def _stow_item(self, request):
        source_container = request.data['source_container']
        destination_container_id = request.data['destination_container']
        product = request.data['product']
        pr = ProductCode.objects.filter(id=product)

        if not pr.exists():
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        count = int(request.data['count'])

        source_container_objects = self.get_container_items(container=source_container, product=product)

        if source_container_objects.count < count:
            return Response(status=status.HTTP_403_FORBIDDEN)

        dest_container = StorageUnit.objects.get(pk=destination_container_id)

        if dest_container.has_reached_sku_limit():
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not dest_container.can_store_weight(count * pr.first().weight):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            p = self.get_container_items(container=destination_container_id, product=product)
            p.count += count
            p.save()
        except ProductInContainer.DoesNotExist:
            ProductInContainer.objects.create(product_id=product, count=count, status=source_container_objects.status, damaged=source_container_objects.damaged, container_id=destination_container_id)

        source_container_objects.count -= count
        if source_container_objects.count <= 0:
            source_container_objects.delete()
        else:
            source_container_objects.save()

        return Response(status=status.HTTP_200_OK)
        
    def get_container_items(self, container: str, product: str):
        return ProductInContainer.objects.get(product_id=product, container_id=container)

    def has_required_properties(self, request):
        if 'source_container' not in request.data:
            return False

        if 'destination_container' not in request.data:
            return False

        if 'product' not in request.data:
            return False

        if 'count' not in request.data:
            return False
        
        return True


class MoveDropzone(APIView):
    def post(self, request):
        container, dropzone = request.data['container'], request.data['dropzone']

        c = StorageUnit.objects.get(pk=container)
        c.dropzone = dropzone
        c.save()
        return Response(status.HTTP_200_OK)